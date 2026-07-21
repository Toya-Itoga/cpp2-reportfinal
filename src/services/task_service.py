# src/services/task_service.py
# タスク管理ビジネスロジック

from typing import Optional
from fastapi import HTTPException

from schema.task import TaskCreate, TaskUpdate
from repositories.task_repository import (
    list_tasks,
    list_tasks_for_employee,
    create_task as repo_create_task,
    update_task as repo_update_task,
    complete_task as repo_complete_task,
    get_task as repo_get_task,
)
from repositories.user_repository import get_user


# ---------------------------------------------------------------------------
# タスク一覧取得
# ---------------------------------------------------------------------------
def get_tasks_for_user(
    user: dict,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    include_completed: bool = False,
) -> list:
    """ユーザーのロールに応じてタスク一覧を返す。

    admin の場合: 全タスクをフィルタ条件で絞り込んで返す。
    employee の場合: 自分自身のタスクのみ返す。
    各タスク辞書には title と status_variant フィールドが付与される。
    """
    role = user.get("role")
    username = user.get("username")

    if role == "admin":
        # 管理者: 全タスクをフィルタ条件で絞り込む
        tasks = list_tasks(
            status_filter=status,
            assignee_filter=assignee,
            include_completed=include_completed,
        )
    else:
        # 従業員: 自分のタスクのみ取得（status フィルタも渡す）
        tasks = list_tasks_for_employee(
            assignee_id=username,
            include_completed=include_completed,
            status_filter=status,
        )

    return tasks


# ---------------------------------------------------------------------------
# タスク作成
# ---------------------------------------------------------------------------
def create_task(data: TaskCreate, created_by: str, employees: list) -> str:
    """新規タスクを作成し、生成した task_id を返す。

    employees リストから担当者名を取得してタスクに付与する。
    指定された assignee_id が存在しない場合は ValueError を送出する。
    """
    # 担当者名を取得
    assignee_name = _resolve_assignee_name(data.assignee_id, employees)

    task_data = {
        "assignee_id": data.assignee_id,
        "assignee_name": assignee_name,
        "work": data.work,
        "location": data.location,
        "scheduled_date": data.scheduled_date,
        "status": data.status,
        "created_by": created_by,
    }

    return repo_create_task(task_data)


# ---------------------------------------------------------------------------
# タスク更新
# ---------------------------------------------------------------------------
def update_task(
    task_id: str, assignee_id: str, data: TaskUpdate, employees: list
) -> None:
    """指定されたタスクを更新する。

    提供されたフィールドのみを更新する。
    assignee_id が変更される場合は担当者名も合わせて更新する。
    """
    updates: dict = {}

    if data.assignee_id is not None:
        updates["assignee_id"] = data.assignee_id
        updates["assignee_name"] = _resolve_assignee_name(
            data.assignee_id, employees
        )

    if data.work is not None:
        updates["work"] = data.work

    if data.location is not None:
        updates["location"] = data.location

    if data.scheduled_date is not None:
        updates["scheduled_date"] = data.scheduled_date

    if data.status is not None:
        updates["status"] = data.status

    if updates:
        repo_update_task(task_id, assignee_id, updates)


# ---------------------------------------------------------------------------
# タスク完了
# ---------------------------------------------------------------------------
def complete_task(task_id: str, assignee_id: str, current_user: dict) -> None:
    """タスクを完了状態に移行する。

    従業員の場合は自分自身のタスクのみ完了可能。
    タスクが存在しない場合は HTTPException(404) を送出する。
    """
    task = repo_get_task(task_id, assignee_id)
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # 従業員は自分のタスクのみ操作可能
    role = current_user.get("role")
    username = current_user.get("username")
    if role != "admin" and task.get("assignee_id") != username:
        raise HTTPException(status_code=403, detail="権限がありません")

    repo_complete_task(task_id, assignee_id, task)


# ---------------------------------------------------------------------------
# タスク単件取得
# ---------------------------------------------------------------------------
def get_task_by_id(task_id: str, assignee_id: str) -> Optional[dict]:
    """指定された task_id と assignee_id でタスクを取得する。

    見つからない場合は None を返す。
    """
    return repo_get_task(task_id, assignee_id)


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------
def _resolve_assignee_name(assignee_id: str, employees: list) -> str:
    """employees リストから assignee_id に対応する name を返す。

    見つからない場合は DynamoDB を直接参照して取得する。
    それでも見つからない場合は assignee_id をそのまま返す。
    """
    # employees リストから検索
    for emp in employees:
        if emp.get("username") == assignee_id:
            return emp.get("name", assignee_id)

    # DB から直接取得
    user = get_user(assignee_id)
    if user:
        return user.get("name", assignee_id)

    return assignee_id
