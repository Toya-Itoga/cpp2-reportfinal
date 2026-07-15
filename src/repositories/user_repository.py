# src/repositories/user_repository.py
# User テーブルに対する DynamoDB 操作

from typing import Optional
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from database import get_user_table
from utils.datetime import now_iso


# ---------------------------------------------------------------------------
# 単一ユーザー操作
# ---------------------------------------------------------------------------
def get_user(username: str) -> Optional[dict]:
    """指定されたユーザー名のユーザー情報を取得する。

    見つからない場合は None を返す。
    """
    table = get_user_table()
    response = table.get_item(Key={"username": username})
    return response.get("Item")


def create_user(
    user_id: str,
    username: str,
    name: str,
    role: str,
    password_hash: str,
) -> None:
    """新規ユーザーを User テーブルに作成する。

    既に同名のユーザーが存在する場合は ValueError を送出する。
    """
    table = get_user_table()
    item = {
        "username": username,
        "user_id": user_id,
        "name": name,
        "role": role,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(username)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError(f"ユーザー '{username}' は既に存在します")
        raise


def update_user(username: str, updates: dict) -> None:
    """指定されたユーザーの属性を更新する。

    updates には更新するフィールドと値のマッピングを指定する。
    """
    table = get_user_table()

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
        Key={"username": username},
        UpdateExpression="SET " + ", ".join(update_parts),
        ExpressionAttributeNames=expression_attrs,
        ExpressionAttributeValues=expression_values,
    )


def deactivate_user(username: str) -> None:
    """指定されたユーザーを論理削除 (is_active = False) する。"""
    update_user(username, {"is_active": False})


# ---------------------------------------------------------------------------
# 複数ユーザー操作
# ---------------------------------------------------------------------------
def list_active_users() -> list:
    """is_active = True の全ユーザーを返す。"""
    table = get_user_table()
    response = table.scan(FilterExpression=Attr("is_active").eq(True))
    return response.get("Items", [])


def list_active_employees() -> list:
    """role = employee かつ is_active = True のユーザー一覧を返す。"""
    table = get_user_table()
    response = table.scan(
        FilterExpression=Attr("role").eq("employee") & Attr("is_active").eq(True)
    )
    return response.get("Items", [])
