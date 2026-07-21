# src/main.py
# Gemba One - FastAPI アプリケーションエントリーポイント

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
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
    """未認証アクセスをログインページへリダイレクト。

    HTMXリクエストの場合: 302を追跡してswapしてしまうため、
    代わりに 200 + HX-Redirect ヘッダを返してブラウザ全体をリダイレクトさせる。
    通常リクエストの場合: 従来通り 302 リダイレクト。
    """
    if request.headers.get("HX-Request"):
        resp = Response(status_code=200)
        resp.headers["HX-Redirect"] = "/login"
        return resp
    return RedirectResponse(url="/login", status_code=302)


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """権限不足アクセスをタスク一覧ページへリダイレクト。

    HTMXリクエストの場合: 200 + HX-Redirect ヘッダを返す。
    通常リクエストの場合: 従来通り 302 リダイレクト。
    """
    if request.headers.get("HX-Request"):
        resp = Response(status_code=200)
        resp.headers["HX-Redirect"] = "/tasks"
        return resp
    return RedirectResponse(url="/tasks", status_code=302)


# ---------------------------------------------------------------------------
# AWS Lambda ハンドラー
# ---------------------------------------------------------------------------
handler = Mangum(app)
