# src/schema/user.py
# ユーザー関連 Pydantic スキーマ (Pydantic v2)

from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# 入力スキーマ
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    """ユーザー新規作成リクエストスキーマ"""

    username: str
    name: str
    password: str
    role: str = "employee"


class UserUpdate(BaseModel):
    """ユーザー更新リクエストスキーマ (全フィールド任意)"""

    name: Optional[str] = None
    password: Optional[str] = None


# ---------------------------------------------------------------------------
# 出力スキーマ
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    """ユーザー情報レスポンススキーマ (パスワードハッシュを除く)"""

    username: str
    name: str
    role: str
    is_active: bool


# ---------------------------------------------------------------------------
# JWT ペイロードスキーマ
# ---------------------------------------------------------------------------
class TokenPayload(BaseModel):
    """JWT トークンのペイロードスキーマ"""

    username: str
    role: str
    name: str
