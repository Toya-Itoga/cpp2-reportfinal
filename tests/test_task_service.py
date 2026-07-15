"""
tests/test_task_service.py
task_service のユニットテスト

DynamoDB 依存部分はモックで置き換えてビジネスロジックのみを検証する。
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# src/ を Python パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_HOURS", "6")
os.environ.setdefault("USER_TABLE_NAME", "User-test")
os.environ.setdefault("TASK_TABLE_NAME", "Task-test")
os.environ.setdefault("DYNAMODB_REGION", "ap-northeast-1")


# ---------------------------------------------------------------------------
# _resolve_assignee_name のテスト
# ---------------------------------------------------------------------------
class TestResolveAssigneeName:
    def test_found_in_employees_list(self):
        """employees リストに username が存在する場合は name を返すこと"""
        from services.task_service import _resolve_assignee_name
        employees = [
            {"username": "tanaka", "name": "田中 太郎"},
            {"username": "sato", "name": "佐藤 花子"},
        ]
        result = _resolve_assignee_name("tanaka", employees)
        assert result == "田中 太郎"

    def test_not_found_returns_username(self):
        """employees リストに存在せずDBにも存在しない場合はusernameを返すこと"""
        from services.task_service import _resolve_assignee_name
        with patch("services.task_service.get_user", return_value=None):
            result = _resolve_assignee_name("unknown_user", [])
        assert result == "unknown_user"

    def test_found_in_db(self):
        """employees リストになくDBに存在する場合はDBから name を返すこと"""
        from services.task_service import _resolve_assignee_name
        mock_user = {"username": "yamada", "name": "山田 一郎"}
        with patch("services.task_service.get_user", return_value=mock_user):
            result = _resolve_assignee_name("yamada", [])
        assert result == "山田 一郎"


# ---------------------------------------------------------------------------
# get_tasks_for_user のテスト
# ---------------------------------------------------------------------------
class TestGetTasksForUser:
    def test_admin_gets_all_tasks(self):
        """admin ユーザーは全タスクを取得できること"""
        from services.task_service import get_tasks_for_user
        mock_tasks = [
            {"task_id": "1", "work": "作業A", "location": "場所A",
             "status": "pending", "status_variant": "pending", "title": "作業A ／ 場所A"},
        ]
        admin_user = {"username": "admin1", "role": "admin"}

        with patch("services.task_service.list_tasks", return_value=mock_tasks):
            result = get_tasks_for_user(admin_user)

        assert result == mock_tasks

    def test_employee_gets_own_tasks(self):
        """employee は自分のタスクのみ取得できること"""
        from services.task_service import get_tasks_for_user
        mock_tasks = [
            {"task_id": "2", "work": "作業B", "location": "場所B",
             "status": "in_progress", "status_variant": "progress",
             "assignee_id": "emp1", "title": "作業B ／ 場所B"},
        ]
        emp_user = {"username": "emp1", "role": "employee"}

        with patch("services.task_service.list_tasks_for_employee", return_value=mock_tasks):
            result = get_tasks_for_user(emp_user)

        assert result == mock_tasks


# ---------------------------------------------------------------------------
# complete_task のテスト
# ---------------------------------------------------------------------------
class TestCompleteTask:
    def test_employee_cannot_complete_others_task(self):
        """employee は他人のタスクを完了できないこと"""
        from services.task_service import complete_task
        from fastapi import HTTPException

        mock_task = {
            "task_id": "abc123",
            "assignee_id": "other_user",
            "status": "pending",
        }
        emp_user = {"username": "emp1", "role": "employee"}

        with patch("services.task_service.repo_get_task", return_value=mock_task):
            with pytest.raises(HTTPException) as exc_info:
                complete_task("abc123", "other_user", current_user=emp_user)
            assert exc_info.value.status_code == 403

    def test_task_not_found_raises_404(self):
        """存在しないタスクは 404 を送出すること"""
        from services.task_service import complete_task
        from fastapi import HTTPException

        admin_user = {"username": "admin1", "role": "admin"}

        with patch("services.task_service.repo_get_task", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                complete_task("nonexistent", "user1", current_user=admin_user)
            assert exc_info.value.status_code == 404
