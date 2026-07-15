# src/routers/dashboard.py
# ダッシュボードルータ (管理者専用)

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.auth_service import require_admin
from repositories.task_repository import list_tasks_for_dashboard
from repositories.user_repository import list_active_employees
from utils.datetime import today_str

router = APIRouter()

# Lambda対応: src/を含まないテンプレートディレクトリパス
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# ダッシュボードページ表示
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: dict = Depends(require_admin),
):
    """管理者専用のダッシュボードページを表示する。

    今日のタスク集計と従業員ごとの進捗状況を表示する。
    HTMX リクエストの場合もフルページを返す (HTMX ナビゲーション対応)。
    """
    today = today_str()

    # 全タスク (進行中・完了済) を取得して集計
    all_tasks = list_tasks_for_dashboard()
    today_tasks = [t for t in all_tasks if t.get("scheduled_date") == today]
    completed_count = sum(
        1 for t in today_tasks if t.get("status") == "completed"
    )
    pending_count = len(today_tasks) - completed_count

    # 従業員ごとの進捗を集計
    employees = list_active_employees()
    by_employee = _aggregate_by_employee(employees, today_tasks)

    ctx = {
        "request": request,
        "user": user,
        "role": user["role"],
        "today_total": len(today_tasks),
        "completed_count": completed_count,
        "pending_count": pending_count,
        "by_employee": by_employee,
        "today": today,
        "active_page": "dashboard",
        "page_title": "ダッシュボード",
    }

    # HTMX ナビゲーション時はコンテンツ部分のみ返す
    is_htmx = request.headers.get("HX-Request")
    template = "partials/dashboard_content.html" if is_htmx else "pages/dashboard.html"
    return templates.TemplateResponse(template, ctx)


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------
def _aggregate_by_employee(employees: list, today_tasks: list) -> list:
    """従業員ごとのタスク進捗を集計してリストを返す。

    各エントリには done, progress, pending のカウントと完了率を含む。
    """
    result = []

    for emp in employees:
        uname = emp["username"]
        emp_tasks = [t for t in today_tasks if t.get("assignee_id") == uname]

        done = sum(1 for t in emp_tasks if t.get("status") == "completed")
        prog = sum(1 for t in emp_tasks if t.get("status") == "in_progress")
        pend = sum(1 for t in emp_tasks if t.get("status") == "pending")
        total = len(emp_tasks)

        result.append(
            {
                "username": uname,
                "name": emp["name"],
                "done": done,
                "progress": prog,
                "pending": pend,
                "total": total,
                "done_pct": round(done / total * 100) if total else 0,
            }
        )

    return result
