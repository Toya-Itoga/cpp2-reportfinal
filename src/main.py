# src/main.py
# Gemba One - FastAPI アプリケーションエントリーポイント

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from mangum import Mangum

from routers import auth, dashboard, tasks, settings

# ---------------------------------------------------------------------------
# アプリケーション初期化
# ---------------------------------------------------------------------------
app = FastAPI(title="Gemba One")

# Lambda対応: src/を含まないパスで静的ファイルを提供
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# ルーター登録
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(settings.router)


# ---------------------------------------------------------------------------
# ルートリダイレクト
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """ルートへのアクセスをログインページへリダイレクト"""
    return RedirectResponse(url="/login")


# ---------------------------------------------------------------------------
# 例外ハンドラ (認証・認可エラーをリダイレクトに変換)
# ---------------------------------------------------------------------------
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """未認証アクセスをログインページへリダイレクト"""
    return RedirectResponse(url="/login")


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """権限不足アクセスをタスク一覧ページへリダイレクト"""
    return RedirectResponse(url="/tasks")


# ---------------------------------------------------------------------------
# AWS Lambda ハンドラー
# ---------------------------------------------------------------------------
handler = Mangum(app)
