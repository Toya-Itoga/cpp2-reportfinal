# src/services/user_service.py
# ユーザー管理ビジネスロジック

import uuid
from typing import Optional

from schema.user import UserCreate, UserUpdate
from services.auth_service import hash_password, verify_password
from repositories.user_repository import (
    get_user,
    create_user as repo_create_user,
    update_user as repo_update_user,
    deactivate_user as repo_deactivate_user,
    list_active_employees,
)


# ---------------------------------------------------------------------------
# ユーザー作成
# ---------------------------------------------------------------------------
def create_user(data: UserCreate) -> None:
    """新規ユーザーを作成する。

    パスワードをハッシュ化してからリポジトリに渡す。
    既に同名のユーザーが存在する場合は ValueError が送出される。
    """
    password_hash = hash_password(data.password)
    user_id = str(uuid.uuid4())

    repo_create_user(
        user_id=user_id,
        username=data.username,
        name=data.name,
        role=data.role,
        password_hash=password_hash,
    )


# ---------------------------------------------------------------------------
# ユーザー更新
# ---------------------------------------------------------------------------
def update_user(username: str, data: UserUpdate) -> None:
    """指定されたユーザーの情報を更新する。

    name と password のうち、提供されたフィールドのみ更新する。
    password が提供された場合はハッシュ化してから保存する。
    """
    updates: dict = {}

    if data.name is not None:
        updates["name"] = data.name

    if data.password is not None:
        updates["password_hash"] = hash_password(data.password)

    if updates:
        repo_update_user(username, updates)


# ---------------------------------------------------------------------------
# ユーザー無効化
# ---------------------------------------------------------------------------
def deactivate_user(username: str) -> None:
    """指定されたユーザーを論理削除する。"""
    repo_deactivate_user(username)


# ---------------------------------------------------------------------------
# パスワード変更
# ---------------------------------------------------------------------------
def change_password(username: str, current_pw: str, new_pw: str) -> bool:
    """現在のパスワードを検証し、新しいパスワードに変更する。

    現在のパスワードが正しくない場合は False を返す。
    変更に成功した場合は True を返す。
    """
    user = get_user(username)
    if not user:
        return False

    if not verify_password(current_pw, user["password_hash"]):
        return False

    repo_update_user(username, {"password_hash": hash_password(new_pw)})
    return True


# ---------------------------------------------------------------------------
# ユーザー取得
# ---------------------------------------------------------------------------
def get_user_by_username(username: str) -> Optional[dict]:
    """指定されたユーザー名のユーザー情報を返す。見つからない場合は None。"""
    return get_user(username)


def list_employees() -> list:
    """アクティブな従業員 (role=employee) の一覧を返す。"""
    return list_active_employees()
