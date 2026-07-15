# src/services/auth_service.py
# JWT + bcrypt を使った認証サービス

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
import bcrypt
from fastapi import Cookie, Depends, HTTPException
from dotenv import load_dotenv

# .env ファイルの読み込み (ローカル開発環境用)
load_dotenv()


# ---------------------------------------------------------------------------
# 環境変数から設定値を取得
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "changeme")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "6"))


# ---------------------------------------------------------------------------
# パスワードハッシュ関数
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """パスワードを bcrypt でハッシュ化して返す。"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """平文パスワードがハッシュと一致するか検証する。"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT 操作
# ---------------------------------------------------------------------------
def create_token(username: str, role: str, name: str) -> str:
    """ユーザー情報を含む JWT アクセストークンを生成して返す。"""
    payload = {
        "username": username,
        "role": role,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """JWT トークンを検証してペイロードを返す。無効な場合は None を返す。"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------------------
# FastAPI 依存性注入用認証関数
# ---------------------------------------------------------------------------
def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
) -> dict:
    """Cookie の JWT を検証し、ユーザー情報を返す。

    トークンが存在しないか無効な場合は 401 を送出し、
    main.py の例外ハンドラがログインページへリダイレクトする。
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """認証済みユーザーの role が admin であることを検証する。

    admin でない場合は 403 を送出し、main.py の例外ハンドラが
    タスク一覧ページへリダイレクトする。
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
