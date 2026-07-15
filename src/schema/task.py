# src/schema/task.py
# タスク関連 Pydantic スキーマ (Pydantic v1)

from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# 入力スキーマ
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    """タスク新規作成リクエストスキーマ"""

    assignee_id: str
    work: str
    location: str
    scheduled_date: str
    status: str = "pending"


class TaskUpdate(BaseModel):
    """タスク更新リクエストスキーマ (全フィールド任意)"""

    assignee_id: Optional[str] = None
    work: Optional[str] = None
    location: Optional[str] = None
    scheduled_date: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# 出力スキーマ
# ---------------------------------------------------------------------------
class TaskOut(BaseModel):
    """タスク情報レスポンススキーマ"""

    task_id: str
    assignee_id: str
    work: str
    location: str
    assignee_name: str
    scheduled_date: str
    status: str
    created_by: str
    created_at: str
    updated_at: str

    @property
    def title(self) -> str:
        """作業内容と場所を結合したタイトルを返す"""
        return f"{self.work} ／ {self.location}"

    @property
    def status_variant(self) -> str:
        """ステータスに対応する CSS バリアント名を返す"""
        map_: dict[str, str] = {
            "pending": "pending",
            "in_progress": "progress",
            "completed": "completed",
        }
        return map_.get(self.status, "pending")
