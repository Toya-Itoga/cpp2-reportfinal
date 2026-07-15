"""
tests/test_user_service.py
user_service のユニットテスト

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
os.environ.setdefault("DYNAMODB_REGION", "ap-northeast-1")


# ---------------------------------------------------------------------------
# change_password のテスト
# ---------------------------------------------------------------------------
class TestChangePassword:
    def test_returns_false_if_user_not_found(self):
        """存在しないユーザーのパスワード変更は False を返すこと"""
        from services.user_service import change_password
        with patch("services.user_service.get_user", return_value=None):
            result = change_password("nonexistent", "oldpw", "newpw")
        assert result is False

    def test_returns_false_if_current_password_wrong(self):
        """現在のパスワードが間違っている場合は False を返すこと"""
        from services.user_service import change_password
        from services.auth_service import hash_password

        correct_hash = hash_password("correct_pw")
        mock_user = {"username": "user1", "password_hash": correct_hash}

        with patch("services.user_service.get_user", return_value=mock_user):
            result = change_password("user1", "wrong_pw", "new_pw")
        assert result is False

    def test_returns_true_on_success(self):
        """正しい現在のパスワードで変更が成功し True を返すこと"""
        from services.user_service import change_password
        from services.auth_service import hash_password

        correct_hash = hash_password("correct_pw")
        mock_user = {"username": "user1", "password_hash": correct_hash}

        with patch("services.user_service.get_user", return_value=mock_user):
            with patch("services.user_service.repo_update_user") as mock_update:
                result = change_password("user1", "correct_pw", "new_pw")

        assert result is True
        # repo_update_user が password_hash を含む引数で呼ばれたこと
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert call_args[0] == "user1"
        assert "password_hash" in call_args[1]


# ---------------------------------------------------------------------------
# update_user のテスト
# ---------------------------------------------------------------------------
class TestUpdateUser:
    def test_empty_password_not_updated(self):
        """password が None の場合は password_hash を更新しないこと"""
        from services.user_service import update_user
        from schema.user import UserUpdate

        data = UserUpdate(name="新しい名前", password=None)

        with patch("services.user_service.repo_update_user") as mock_update:
            update_user("user1", data)
            call_args = mock_update.call_args[0]
            # password_hash が含まれないこと
            assert "password_hash" not in call_args[1]
            # name が含まれること
            assert "name" in call_args[1]

    def test_password_hashed_when_provided(self):
        """password が提供された場合は ハッシュ化されて更新されること"""
        from services.user_service import update_user
        from schema.user import UserUpdate

        data = UserUpdate(name=None, password="new_password")

        with patch("services.user_service.repo_update_user") as mock_update:
            update_user("user1", data)
            call_args = mock_update.call_args[0]
            assert "password_hash" in call_args[1]
            # ハッシュ値が平文と異なること
            assert call_args[1]["password_hash"] != "new_password"
