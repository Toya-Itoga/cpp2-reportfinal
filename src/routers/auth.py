# src/routers/auth.py
# 認証関連ルータ (ログイン / ログアウト)

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.auth_service import verify_password, create_token
from repositories.user_repository import get_user

router = APIRouter()

# Lambda対応: src/を含まないテンプレートディレクトリパス
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# ログインページ表示
# ---------------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """ログインページを表示する。"""
    return templates.TemplateResponse(
        "pages/login.html", {"request": request}
    )


# ---------------------------------------------------------------------------
# ログイン処理
# ---------------------------------------------------------------------------
@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    """ログインフォームの送信を処理する。

    認証成功時: ロールに応じてダッシュボードまたはタスク一覧へリダイレクト。
    認証失敗時: HTMX リクエストならフォームフラグメントを返し、
               通常リクエストならログインページ全体を返す。
    """
    user = get_user(username)

    # 認証チェック (存在確認・有効確認・パスワード検証)
    if (
        not user
        or not user.get("is_active")
        or not verify_password(password, user["password_hash"])
    ):
        error_msg = "ユーザー名またはパスワードが正しくありません"
        ctx = {"request": request, "error": error_msg}
        is_htmx = request.headers.get("HX-Request")

        if is_htmx:
            return templates.TemplateResponse(
                "partials/login_form.html", ctx
            )
        return templates.TemplateResponse("pages/login.html", ctx)

    # JWT トークンを生成
    token = create_token(user["username"], user["role"], user["name"])

    # ロールに応じてリダイレクト先を決定
    redirect_url = "/dashboard" if user["role"] == "admin" else "/tasks"

    # HTMXリクエストの場合: HX-Redirect ヘッダでブラウザ全体をリダイレクトさせる
    # (302リダイレクトはHTMXがswapしてしまうため使用しない)
    is_htmx = request.headers.get("HX-Request")
    if is_htmx:
        resp = Response(status_code=200)
        resp.headers["HX-Redirect"] = redirect_url
        resp.set_cookie("access_token", token, httponly=True, max_age=6 * 3600)
        return resp

    # 非HTMXリクエスト（通常フォームPOST）: 従来通り302リダイレクト
    resp = RedirectResponse(url=redirect_url, status_code=302)
    resp.set_cookie("access_token", token, httponly=True, max_age=6 * 3600)
    return resp


# ---------------------------------------------------------------------------
# ログアウト処理
# ---------------------------------------------------------------------------
@router.post("/logout")
def logout():
    """ログアウトし、Cookie を削除してログインページへリダイレクトする。"""
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("access_token")
    return resp
