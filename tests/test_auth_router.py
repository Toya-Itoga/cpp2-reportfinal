"""
tests/test_auth_router.py
auth ルータのログイン成功時リダイレクト方式のテスト

HTMX リクエスト / 非HTMX リクエストで異なるレスポンスを返すことを確認する。
DynamoDB および JWT は unittest.mock でスタブ化する。
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# src/ を Python パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# テスト用環境変数（.envファイルは参照しない）
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-router-test")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_HOURS", "6")
os.environ.setdefault("USER_TABLE_NAME", "User-test")
os.environ.setdefault("DYNAMODB_REGION", "ap-northeast-1")

# モックユーザー (bcrypt ハッシュはauth_serviceを通して生成)
def _make_mock_user(role: str = "admin") -> dict:
    from services.auth_service import hash_password
    return {
        "username": "testuser",
        "name": "テストユーザー",
        "role": role,
        "is_active": True,
        "password_hash": hash_password("password123"),
    }


def _build_client():
    """FastAPI TestClient を返す。DynamoDB接続は行わない。"""
    from fastapi import FastAPI
    from routers.auth import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# HTMX リクエスト（ログイン成功）
# ---------------------------------------------------------------------------
class TestLoginHtmx:
    def test_htmx_admin_returns_200_with_hx_redirect(self):
        """adminがHTMXでログイン成功すると200 + HX-Redirect: /dashboard を返すこと"""
        mock_user = _make_mock_user(role="admin")
        client = _build_client()

        with patch("routers.auth.get_user", return_value=mock_user):
            resp = client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
                headers={"HX-Request": "true"},
                follow_redirects=False,
            )

        assert resp.status_code == 200
        assert resp.headers.get("hx-redirect") == "/dashboard"
        assert "access_token" in resp.cookies

    def test_htmx_employee_returns_200_with_hx_redirect_tasks(self):
        """employeeがHTMXでログイン成功すると200 + HX-Redirect: /tasks を返すこと"""
        mock_user = _make_mock_user(role="employee")
        client = _build_client()

        with patch("routers.auth.get_user", return_value=mock_user):
            resp = client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
                headers={"HX-Request": "true"},
                follow_redirects=False,
            )

        assert resp.status_code == 200
        assert resp.headers.get("hx-redirect") == "/tasks"

    def test_htmx_login_sets_httponly_cookie(self):
        """HTMXログイン成功時に HttpOnly Cookie が設定されること"""
        mock_user = _make_mock_user(role="admin")
        client = _build_client()

        with patch("routers.auth.get_user", return_value=mock_user):
            resp = client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
                headers={"HX-Request": "true"},
                follow_redirects=False,
            )

        assert "access_token" in resp.cookies


# ---------------------------------------------------------------------------
# 非HTMX リクエスト（ログイン成功）
# ---------------------------------------------------------------------------
class TestLoginNonHtmx:
    def test_non_htmx_admin_returns_302_redirect(self):
        """非HTMXリクエストでadminがログイン成功すると302 /dashboard へリダイレクトすること"""
        mock_user = _make_mock_user(role="admin")
        client = _build_client()

        with patch("routers.auth.get_user", return_value=mock_user):
            resp = client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert resp.headers.get("location") == "/dashboard"

    def test_non_htmx_employee_returns_302_redirect_tasks(self):
        """非HTMXリクエストでemployeeがログイン成功すると302 /tasks へリダイレクトすること"""
        mock_user = _make_mock_user(role="employee")
        client = _build_client()

        with patch("routers.auth.get_user", return_value=mock_user):
            resp = client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
                follow_redirects=False,
            )

        assert resp.status_code == 302
        assert resp.headers.get("location") == "/tasks"


# ---------------------------------------------------------------------------
# 認証失敗（既存動作を壊していないこと）
# ---------------------------------------------------------------------------
class TestLoginFailure:
    """認証失敗時のテスト。

    テスト環境にはテンプレートディレクトリが存在しないため、
    TemplateResponse をモックしてレスポンス生成をスタブ化する。
    """

    def _post_login(self, get_user_rv, password: str, htmx: bool = False):
        """ログイン失敗シナリオの共通ヘルパー。"""
        from fastapi.responses import HTMLResponse

        client = _build_client()
        headers = {"HX-Request": "true"} if htmx else {}

        # TemplateResponse はテンプレートファイルを必要とするためモック化
        mock_tr = MagicMock(return_value=HTMLResponse(content="error", status_code=200))

        with patch("routers.auth.get_user", return_value=get_user_rv):
            with patch("routers.auth.templates.TemplateResponse", mock_tr):
                resp = client.post(
                    "/login",
                    data={"username": "testuser", "password": password},
                    headers=headers,
                    follow_redirects=False,
                )
        return resp

    def test_wrong_password_returns_error(self):
        """誤ったパスワードでログイン失敗時にエラーが返ること"""
        mock_user = _make_mock_user(role="admin")
        resp = self._post_login(get_user_rv=mock_user, password="wrong_password")

        # リダイレクトも HX-Redirect も発生しないこと
        assert resp.status_code == 200
        assert "hx-redirect" not in resp.headers
        assert "location" not in resp.headers

    def test_unknown_user_returns_error(self):
        """存在しないユーザーでログイン失敗時にエラーが返ること"""
        resp = self._post_login(get_user_rv=None, password="password123")

        assert resp.status_code == 200
        assert "hx-redirect" not in resp.headers

    def test_inactive_user_returns_error(self):
        """is_active=False のユーザーはログイン失敗すること"""
        from services.auth_service import hash_password
        mock_user = {
            "username": "inactive",
            "name": "無効ユーザー",
            "role": "employee",
            "is_active": False,
            "password_hash": hash_password("password123"),
        }
        resp = self._post_login(get_user_rv=mock_user, password="password123")

        assert resp.status_code == 200
        assert "hx-redirect" not in resp.headers
