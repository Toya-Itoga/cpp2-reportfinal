# src/routers/settings.py
# 設定ルータ (ユーザー管理・パスワード変更)

from fastapi import APIRouter, Depends, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from services.auth_service import get_current_user, require_admin
from services.user_service import (
    create_user,
    update_user,
    deactivate_user,
    change_password,
    list_employees,
    get_user_by_username,
)
from repositories.user_repository import list_active_users
from schema.user import UserCreate, UserUpdate

router = APIRouter()

# Lambda対応: src/を含まないテンプレートディレクトリパス
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# 設定ページ表示
# ---------------------------------------------------------------------------
@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    user: dict = Depends(require_admin),
):
    """管理者専用の設定ページを表示する。ユーザー一覧を含む。"""
    users = list_active_users()

    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "users": users,
        "active_page": "settings",
        "page_title": "設定",
    }
    is_htmx = request.headers.get("HX-Request")
    template = "partials/settings_content.html" if is_htmx else "pages/settings.html"
    return templates.TemplateResponse(template, ctx)


# ---------------------------------------------------------------------------
# ユーザー新規作成フォームフラグメント
# ---------------------------------------------------------------------------
@router.get("/settings/users/new", response_class=HTMLResponse)
def new_user_form(
    request: Request,
    user: dict = Depends(require_admin),
):
    """ユーザー新規作成モーダル用フラグメントを返す。管理者専用。"""
    ctx = {"request": request, "user": user}
    return templates.TemplateResponse("partials/employee_form.html", ctx)


# ---------------------------------------------------------------------------
# ユーザー新規作成処理
# ---------------------------------------------------------------------------
@router.post("/settings/users", response_class=HTMLResponse)
async def create_user_handler(
    request: Request,
    username: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    role: str = Form("employee"),
    user: dict = Depends(require_admin),
):
    """新規ユーザーを作成し、更新されたユーザー一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    ユーザー名が重複している場合はエラーフラグメントを返す。
    """
    data = UserCreate(
        username=username,
        name=name,
        password=password,
        role=role,
    )

    try:
        create_user(data)
    except ValueError as e:
        # ユーザー名重複エラー（モーダルは閉じない）
        ctx = {
            "request": request,
            "user": user,
            "error": str(e),
            "form_data": data.model_dump(),
        }
        return templates.TemplateResponse("partials/employee_form.html", ctx)

    users = list_active_users()
    ctx = {
        "request": request,
        "user": user,
        "users": users,
    }
    resp = templates.TemplateResponse("partials/employee_list.html", ctx)
    resp.headers["HX-Trigger"] = "close-modal"
    return resp


# ---------------------------------------------------------------------------
# ユーザー編集フォームフラグメント
# ---------------------------------------------------------------------------
@router.get("/settings/users/{username}/edit", response_class=HTMLResponse)
def edit_user_form(
    username: str,
    request: Request,
    user: dict = Depends(require_admin),
):
    """ユーザー編集モーダル用フラグメントを返す。管理者専用。"""
    target_user = get_user_by_username(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    ctx = {
        "request": request,
        "user": user,
        "target_user": target_user,
    }
    return templates.TemplateResponse("partials/employee_form.html", ctx)


# ---------------------------------------------------------------------------
# ユーザー更新処理
# ---------------------------------------------------------------------------
@router.put("/settings/users/{username}", response_class=HTMLResponse)
async def update_user_handler(
    username: str,
    request: Request,
    name: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    user: dict = Depends(require_admin),
):
    """ユーザー情報を更新し、更新されたユーザー一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    """
    data = UserUpdate(
        name=name if name else None,
        password=password if password else None,
    )
    update_user(username, data)

    users = list_active_users()
    ctx = {
        "request": request,
        "user": user,
        "users": users,
    }
    resp = templates.TemplateResponse("partials/employee_list.html", ctx)
    resp.headers["HX-Trigger"] = "close-modal"
    return resp


# ---------------------------------------------------------------------------
# ユーザー削除確認フラグメント
# ---------------------------------------------------------------------------
@router.get(
    "/settings/users/{username}/delete-confirm", response_class=HTMLResponse
)
def delete_confirm_form(
    username: str,
    request: Request,
    user: dict = Depends(require_admin),
):
    """ユーザー削除確認モーダル用フラグメントを返す。管理者専用。"""
    target_user = get_user_by_username(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    ctx = {
        "request": request,
        "user": user,
        "target_user": target_user,
    }
    return templates.TemplateResponse(
        "partials/employee_delete_confirm.html", ctx
    )


# ---------------------------------------------------------------------------
# ユーザー無効化処理
# ---------------------------------------------------------------------------
@router.post(
    "/settings/users/{username}/deactivate", response_class=HTMLResponse
)
async def deactivate_user_handler(
    username: str,
    request: Request,
    user: dict = Depends(require_admin),
):
    """指定されたユーザーを無効化し、更新されたユーザー一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    自分自身を無効化しようとした場合はエラーを返す。
    """
    if username == user["username"]:
        raise HTTPException(
            status_code=400, detail="自分自身を無効化することはできません"
        )

    deactivate_user(username)

    users = list_active_users()
    ctx = {
        "request": request,
        "user": user,
        "users": users,
    }
    resp = templates.TemplateResponse("partials/employee_list.html", ctx)
    resp.headers["HX-Trigger"] = "close-modal"
    return resp


# ---------------------------------------------------------------------------
# パスワード変更処理
# ---------------------------------------------------------------------------
@router.post("/settings/password", response_class=HTMLResponse)
async def change_password_handler(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """ログイン中ユーザーのパスワードを変更する。

    新しいパスワードと確認用パスワードが一致しない場合、
    または現在のパスワードが間違っている場合はエラーフラグメントを返す。
    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    """
    # 新パスワードの一致確認
    if new_password != confirm_password:
        ctx = {
            "request": request,
            "user": user,
            "error": "新しいパスワードと確認用パスワードが一致しません",
        }
        return templates.TemplateResponse(
            "partials/pw_change_result.html", ctx
        )

    # パスワード変更実行
    success = change_password(
        username=user["username"],
        current_pw=current_password,
        new_pw=new_password,
    )

    if not success:
        ctx = {
            "request": request,
            "user": user,
            "error": "現在のパスワードが正しくありません",
        }
        return templates.TemplateResponse(
            "partials/pw_change_result.html", ctx
        )

    ctx = {
        "request": request,
        "user": user,
        "success": "パスワードを変更しました",
    }
    resp = templates.TemplateResponse("partials/password_form.html", ctx)
    resp.headers["HX-Trigger"] = "close-modal"
    return resp
