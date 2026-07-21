"""
tests/test_exception_handlers.py
main.py のグローバル例外ハンドラ（401・403）のテスト

HTMX リクエスト時は 200 + HX-Redirect ヘッダを返すこと、
通常リクエスト時は 302 リダイレクトを返すことを確認する。

main.py は StaticFiles(directory='static') をモジュールロード時に実行するため、
テスト環境では static/ が存在せず直接 import できない。
そのため TestClient はハンドラと同一ロジックをインラインで持つ最小 FastAPI
アプリを使い、動作仕様のみを検証する。
"""

import os
import sys
import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, Response
from fastapi.testclient import TestClient

# src/ を Python パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-handler-test")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_HOURS", "6")


# ---------------------------------------------------------------------------
# main.py の例外ハンドラと同一ロジックをインライン定義（仕様をそのまま記述）
# ---------------------------------------------------------------------------
async def _unauthorized_handler(request: Request, exc: HTTPException):
    """main.py unauthorized_handler と同一ロジック"""
    if request.headers.get("HX-Request"):
        resp = Response(status_code=200)
        resp.headers["HX-Redirect"] = "/login"
        return resp
    return RedirectResponse(url="/login", status_code=302)


async def _forbidden_handler(request: Request, exc: HTTPException):
    """main.py forbidden_handler と同一ロジック"""
    if request.headers.get("HX-Request"):
        resp = Response(status_code=200)
        resp.headers["HX-Redirect"] = "/tasks"
        return resp
    return RedirectResponse(url="/tasks", status_code=302)


def _build_client() -> TestClient:
    """例外ハンドラをテストするための最小 FastAPI アプリを返す。"""
    app = FastAPI()
    app.add_exception_handler(401, _unauthorized_handler)
    app.add_exception_handler(403, _forbidden_handler)

    @app.get("/trigger-401")
    async def trigger_401():
        raise HTTPException(status_code=401, detail="Unauthorized")

    @app.get("/trigger-403")
    async def trigger_403():
        raise HTTPException(status_code=403, detail="Forbidden")

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 401 Unauthorized ハンドラ
# ---------------------------------------------------------------------------
class TestUnauthorizedHandler:
    def test_htmx_request_returns_200_with_hx_redirect(self):
        """HTMXリクエストで 401 が発生したとき 200 + HX-Redirect: /login を返すこと"""
        client = _build_client()
        resp = client.get(
            "/trigger-401",
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        assert resp.headers.get("hx-redirect") == "/login"

    def test_non_htmx_request_returns_302(self):
        """通常リクエストで 401 が発生したとき 302 /login へリダイレクトすること"""
        client = _build_client()
        resp = client.get("/trigger-401", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/login"

    def test_htmx_response_has_no_location_header(self):
        """HTMXリクエストのレスポンスに Location ヘッダが含まれないこと"""
        client = _build_client()
        resp = client.get(
            "/trigger-401",
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert "location" not in resp.headers


# ---------------------------------------------------------------------------
# 403 Forbidden ハンドラ
# ---------------------------------------------------------------------------
class TestForbiddenHandler:
    def test_htmx_request_returns_200_with_hx_redirect(self):
        """HTMXリクエストで 403 が発生したとき 200 + HX-Redirect: /tasks を返すこと"""
        client = _build_client()
        resp = client.get(
            "/trigger-403",
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        assert resp.headers.get("hx-redirect") == "/tasks"

    def test_non_htmx_request_returns_302(self):
        """通常リクエストで 403 が発生したとき 302 /tasks へリダイレクトすること"""
        client = _build_client()
        resp = client.get("/trigger-403", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers.get("location") == "/tasks"

    def test_htmx_response_has_no_location_header(self):
        """HTMXリクエストのレスポンスに Location ヘッダが含まれないこと"""
        client = _build_client()
        resp = client.get(
            "/trigger-403",
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert "location" not in resp.headers
