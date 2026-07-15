# src/routers/tasks.py
# タスク一覧・CRUD ルータ (管理者・従業員共用)

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from services.auth_service import get_current_user, require_admin
from services.task_service import (
    get_tasks_for_user,
    create_task,
    update_task,
    complete_task,
    get_task_by_id,
)
from services.user_service import list_employees
from schema.task import TaskCreate, TaskUpdate
from utils.datetime import today_str

router = APIRouter()

# Lambda対応: src/を含まないテンプレートディレクトリパス
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# タスク一覧ページ
# ---------------------------------------------------------------------------
@router.get("/tasks", response_class=HTMLResponse)
def task_list(
    request: Request,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    include_completed: bool = False,
    user: dict = Depends(get_current_user),
):
    """タスク一覧ページを表示する。

    HTMX リクエストの場合はコンテンツ部分のフラグメントを返す。
    クエリパラメータでステータス・担当者・完了済み表示のフィルタが可能。
    """
    tasks = get_tasks_for_user(
        user=user,
        status=status,
        assignee=assignee,
        include_completed=include_completed,
    )
    employees = list_employees() if user.get("role") == "admin" else []

    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "tasks": tasks,
        "employees": employees,
        "status_filter": status,
        "assignee_filter": assignee,
        "include_completed": include_completed,
        "today": today_str(),
        "active_page": "tasks",
        "page_title": "タスク一覧",
    }

    is_htmx = request.headers.get("HX-Request")
    # フィルタリクエスト（HX-Requestかつtask-listへのswap）はtask_listフラグメントを返す
    # ナビゲーション（HX-Requestかつmain-contentへのswap）はcontent部分を返す
    htmx_target = request.headers.get("HX-Target", "")
    if is_htmx and htmx_target == "task-list":
        template = "partials/task_list.html"
    elif is_htmx and htmx_target == "main-content":
        template = "partials/tasks_content.html"
    else:
        template = "pages/tasks.html"
    return templates.TemplateResponse(template, ctx)


# ---------------------------------------------------------------------------
# タスク新規作成フォームフラグメント
# ---------------------------------------------------------------------------
@router.get("/tasks/new", response_class=HTMLResponse)
def new_task_form(
    request: Request,
    user: dict = Depends(require_admin),
):
    """タスク新規作成モーダル用フラグメントを返す。管理者専用。"""
    employees = list_employees()

    ctx = {
        "request": request,
        "user": user,
        "employees": employees,
        "today": today_str(),
    }
    return templates.TemplateResponse("partials/task_form.html", ctx)


# ---------------------------------------------------------------------------
# タスク新規作成処理
# ---------------------------------------------------------------------------
@router.post("/tasks", response_class=HTMLResponse)
async def create_task_handler(
    request: Request,
    response: Response,
    assignee_id: str = Form(...),
    work: str = Form(...),
    location: str = Form(...),
    scheduled_date: str = Form(...),
    status: str = Form("pending"),
    user: dict = Depends(require_admin),
):
    """タスクを新規作成し、更新されたタスク一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    """
    data = TaskCreate(
        assignee_id=assignee_id,
        work=work,
        location=location,
        scheduled_date=scheduled_date,
        status=status,
    )
    employees = list_employees()
    create_task(data, created_by=user["username"], employees=employees)

    # モーダルを閉じるイベントを発火
    response.headers["HX-Trigger"] = "close-modal"

    tasks = get_tasks_for_user(user=user)
    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "tasks": tasks,
        "employees": employees,
        "today": today_str(),
    }
    return templates.TemplateResponse("partials/task_list.html", ctx)


# ---------------------------------------------------------------------------
# タスク編集フォームフラグメント
# ---------------------------------------------------------------------------
@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def edit_task_form(
    task_id: str,
    assignee_id: str,
    request: Request,
    user: dict = Depends(require_admin),
):
    """タスク編集モーダル用フラグメントを返す。管理者専用。"""
    task = get_task_by_id(task_id, assignee_id)
    employees = list_employees()

    ctx = {
        "request": request,
        "user": user,
        "task": task,
        "employees": employees,
        "today": today_str(),
    }
    return templates.TemplateResponse("partials/task_form.html", ctx)


# ---------------------------------------------------------------------------
# タスク更新処理
# ---------------------------------------------------------------------------
@router.put("/tasks/{task_id}", response_class=HTMLResponse)
async def update_task_handler(
    task_id: str,
    request: Request,
    response: Response,
    assignee_id: str = Form(...),
    work: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    scheduled_date: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    user: dict = Depends(require_admin),
):
    """タスクを更新し、更新されたタスク一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    """
    data = TaskUpdate(
        work=work,
        location=location,
        scheduled_date=scheduled_date,
        status=status,
    )
    employees = list_employees()
    update_task(task_id, assignee_id, data, employees)

    # モーダルを閉じるイベントを発火
    response.headers["HX-Trigger"] = "close-modal"

    tasks = get_tasks_for_user(user=user)
    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "tasks": tasks,
        "employees": employees,
        "today": today_str(),
    }
    return templates.TemplateResponse("partials/task_list.html", ctx)


# ---------------------------------------------------------------------------
# タスク完了確認フラグメント
# ---------------------------------------------------------------------------
@router.get("/tasks/{task_id}/confirm", response_class=HTMLResponse)
def confirm_complete_form(
    task_id: str,
    assignee_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """タスク完了確認モーダル用フラグメントを返す。"""
    task = get_task_by_id(task_id, assignee_id)

    ctx = {
        "request": request,
        "user": user,
        "task": task,
    }
    return templates.TemplateResponse("partials/task_confirm.html", ctx)


# ---------------------------------------------------------------------------
# タスク完了処理
# ---------------------------------------------------------------------------
@router.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
async def complete_task_handler(
    task_id: str,
    request: Request,
    response: Response,
    assignee_id: str = Form(...),
    user: dict = Depends(get_current_user),
):
    """タスクを完了状態に移行し、更新されたタスク一覧フラグメントを返す。

    成功時は HX-Trigger ヘッダで close-modal イベントを発火する。
    従業員は自分のタスクのみ完了可能。
    """
    complete_task(task_id, assignee_id, current_user=user)

    # モーダルを閉じるイベントを発火
    response.headers["HX-Trigger"] = "close-modal"

    employees = list_employees() if user.get("role") == "admin" else []
    tasks = get_tasks_for_user(user=user)
    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "tasks": tasks,
        "employees": employees,
        "today": today_str(),
    }
    return templates.TemplateResponse("partials/task_list.html", ctx)
