# src/repositories/task_repository.py
# Task テーブルに対する DynamoDB 操作
# PK: TASK#<uuid> (進行中), DONE#<uuid> (完了済)
# SK: assignee_id

import uuid
from typing import Optional
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from database import get_task_table
from utils.datetime import now_iso


# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------
TASK_PREFIX = "TASK#"
DONE_PREFIX = "DONE#"


# ---------------------------------------------------------------------------
# 単一タスク操作
# ---------------------------------------------------------------------------
def get_task(task_id: str, assignee_id: str) -> Optional[dict]:
    """指定された task_id と assignee_id でタスクを取得する。

    TASK# プレフィックスで検索し、見つからない場合は DONE# プレフィックスで再検索する。
    """
    table = get_task_table()

    # 進行中タスクを検索
    response = table.get_item(
        Key={"task_id": f"{TASK_PREFIX}{task_id}", "assignee_id": assignee_id}
    )
    item = response.get("Item")
    if item:
        return _normalize_task(item)

    # 完了済タスクを検索
    response = table.get_item(
        Key={"task_id": f"{DONE_PREFIX}{task_id}", "assignee_id": assignee_id}
    )
    item = response.get("Item")
    if item:
        return _normalize_task(item)

    return None


def create_task(task_data: dict) -> str:
    """新規タスクを Task テーブルに作成し、生成した task_id を返す。

    task_data には assignee_id, work, location, scheduled_date,
    created_by, status などを含める。
    """
    table = get_task_table()
    task_id = str(uuid.uuid4())
    now = now_iso()

    item = {
        "task_id": f"{TASK_PREFIX}{task_id}",
        "assignee_id": task_data["assignee_id"],
        "work": task_data["work"],
        "location": task_data["location"],
        "assignee_name": task_data.get("assignee_name", ""),
        "scheduled_date": task_data["scheduled_date"],
        "status": task_data.get("status", "pending"),
        "created_by": task_data["created_by"],
        "created_at": now,
        "updated_at": now,
    }

    table.put_item(Item=item)
    return task_id


def update_task(task_id: str, assignee_id: str, updates: dict) -> None:
    """指定されたタスクの属性を更新する。

    TASK# プレフィックスの項目のみ更新対象とする。
    """
    table = get_task_table()

    # UpdateExpression を動的構築
    update_parts: list[str] = []
    expression_attrs: dict = {}
    expression_values: dict = {}

    for key, value in updates.items():
        placeholder = f"#{key}"
        value_placeholder = f":{key}"
        update_parts.append(f"{placeholder} = {value_placeholder}")
        expression_attrs[placeholder] = key
        expression_values[value_placeholder] = value

    # updated_at を自動更新
    update_parts.append("#updated_at = :updated_at")
    expression_attrs["#updated_at"] = "updated_at"
    expression_values[":updated_at"] = now_iso()

    table.update_item(
        Key={
            "task_id": f"{TASK_PREFIX}{task_id}",
            "assignee_id": assignee_id,
        },
        UpdateExpression="SET " + ", ".join(update_parts),
        ExpressionAttributeNames=expression_attrs,
        ExpressionAttributeValues=expression_values,
    )


def complete_task(task_id: str, assignee_id: str, task_data: dict) -> None:
    """タスクを完了状態に移行する。

    TASK#<id> の項目を削除し、DONE#<id> の項目を作成することで
    完了済みとして区別する。
    """
    table = get_task_table()
    now = now_iso()

    # 完了済みアイテムを作成
    done_item = {**task_data}
    done_item["task_id"] = f"{DONE_PREFIX}{task_id}"
    done_item["assignee_id"] = assignee_id
    done_item["status"] = "completed"
    done_item["updated_at"] = now

    table.put_item(Item=done_item)

    # 進行中アイテムを削除
    try:
        table.delete_item(
            Key={
                "task_id": f"{TASK_PREFIX}{task_id}",
                "assignee_id": assignee_id,
            }
        )
    except ClientError:
        # 削除に失敗してもロールバックしない (冪等性を優先)
        pass


# ---------------------------------------------------------------------------
# 複数タスク操作
# ---------------------------------------------------------------------------
def list_tasks(
    status_filter: Optional[str] = None,
    assignee_filter: Optional[str] = None,
    include_completed: bool = False,
) -> list:
    """条件に合うタスク一覧を返す。

    include_completed=True の場合は DONE# プレフィックスのアイテムも含める。
    status_filter と assignee_filter は AND 条件で絞り込む。
    """
    table = get_task_table()
    response = table.scan()
    items = response.get("Items", [])

    # ページネーション対応
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    # プレフィックスフィルタリング
    result = []
    for item in items:
        pk: str = item.get("task_id", "")
        if pk.startswith(TASK_PREFIX):
            result.append(_normalize_task(item))
        elif include_completed and pk.startswith(DONE_PREFIX):
            result.append(_normalize_task(item))

    # ステータスフィルタ
    if status_filter:
        result = [t for t in result if t.get("status") == status_filter]

    # 担当者フィルタ
    if assignee_filter:
        result = [t for t in result if t.get("assignee_id") == assignee_filter]

    # 予定日の昇順でソート
    result.sort(key=lambda t: t.get("scheduled_date", ""))
    return result


def list_tasks_for_employee(
    assignee_id: str, include_completed: bool = False
) -> list:
    """指定された従業員のタスク一覧を返す。

    include_completed=True の場合は完了済みタスクも含める。
    """
    return list_tasks(
        assignee_filter=assignee_id, include_completed=include_completed
    )


def list_tasks_for_dashboard() -> list:
    """ダッシュボード集計用に全タスク (進行中 + 完了済) を返す。"""
    return list_tasks(include_completed=True)


# ---------------------------------------------------------------------------
# 内部ヘルパー
# ---------------------------------------------------------------------------
def _normalize_task(item: dict) -> dict:
    """DynamoDB のアイテムをアプリケーション用の辞書に正規化する。

    task_id から TASK#/DONE# プレフィックスを取り除いた純粋な UUID を
    task_id フィールドとして設定する。
    """
    normalized = dict(item)
    raw_pk: str = normalized.get("task_id", "")

    if raw_pk.startswith(TASK_PREFIX):
        normalized["task_id"] = raw_pk[len(TASK_PREFIX):]
    elif raw_pk.startswith(DONE_PREFIX):
        normalized["task_id"] = raw_pk[len(DONE_PREFIX):]

    # テンプレート用の派生フィールドを付与
    work = normalized.get("work", "")
    location = normalized.get("location", "")
    normalized["title"] = f"{work} ／ {location}"

    status = normalized.get("status", "pending")
    status_map: dict[str, str] = {
        "pending": "pending",
        "in_progress": "progress",
        "completed": "completed",
    }
    normalized["status_variant"] = status_map.get(status, "pending")

    return normalized
