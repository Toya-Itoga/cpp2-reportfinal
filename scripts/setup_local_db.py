"""DynamoDB Localのテーブル作成と初期データ投入スクリプト

実行: python scripts/setup_local_db.py
用途: Docker再起動でデータが消えた際に再投入する
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# .envの読み込み
load_dotenv()

# 環境変数
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:5434")
DYNAMODB_REGION = os.environ.get("DYNAMODB_REGION", "ap-northeast-1")
USER_TABLE_NAME = os.environ.get("USER_TABLE_NAME", "User")
TASK_TABLE_NAME = os.environ.get("TASK_TABLE_NAME", "Task")

# DynamoDBリソース（ローカル接続）
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=DYNAMODB_REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "dummy"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "dummy"),
)


# ─── テーブル作成 ──────────────────────────────────────────────────────────────

def create_user_table() -> None:
    """Userテーブルを作成する（既存の場合はスキップ）"""
    try:
        table = dynamodb.create_table(
            TableName=USER_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "username", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "username", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✅ Userテーブル作成済み（{USER_TABLE_NAME}）")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"✅ Userテーブル作成済み（{USER_TABLE_NAME}）（既存）")
        else:
            raise


def create_task_table() -> None:
    """Taskテーブルを作成する（既存の場合はスキップ）

    PK: task_id（String） — 値は TASK#<uuid> または DONE#<uuid> のプレフィックス付き
    SK: assignee_id（String） — 担当者のusername
    """
    try:
        table = dynamodb.create_table(
            TableName=TASK_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "task_id", "KeyType": "HASH"},
                {"AttributeName": "assignee_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "task_id", "AttributeType": "S"},
                {"AttributeName": "assignee_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"✅ Taskテーブル作成済み（{TASK_TABLE_NAME}）")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"✅ Taskテーブル作成済み（{TASK_TABLE_NAME}）（既存）")
        else:
            raise


# ─── 初期データ投入 ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """bcryptでパスワードをハッシュ化する"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed_users(table) -> int:
    """初期ユーザーデータを投入する

    同じusernameが既に存在する場合はスキップ。
    passwordはbcryptでハッシュ化してpassword_hashとして保存する。
    """
    now = datetime.now(timezone.utc).isoformat()

    users = [
        {"username": "tanaka",    "name": "田中 社長", "role": "admin",    "password": "admin1234"},
        {"username": "sato",      "name": "佐藤 健一", "role": "employee", "password": "emp1234"},
        {"username": "suzuki",    "name": "鈴木 大輔", "role": "employee", "password": "emp1234"},
        {"username": "takahashi", "name": "高橋 修",   "role": "employee", "password": "emp1234"},
    ]

    inserted = 0
    for user in users:
        # 同じPKが既存の場合はスキップ
        response = table.get_item(Key={"username": user["username"]})
        if "Item" in response:
            continue

        table.put_item(Item={
            "username":      user["username"],
            "user_id":       str(uuid.uuid4()),
            "name":          user["name"],
            "role":          user["role"],
            "password_hash": hash_password(user["password"]),
            "created_at":    now,
            "is_active":     True,
        })
        inserted += 1

    return inserted


def seed_tasks(table) -> int:
    """初期タスクデータを投入する

    未完了タスク（PK: TASK#<uuid>）5件 + 完了済みタスク（PK: DONE#<uuid>）2件。
    work / location は別フィールドとして保存する（HANDOFF.md §8 準拠）。
    """
    today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tomorrow  = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).isoformat()

    # username → 表示名のマッピング
    name_map: dict[str, str] = {
        "sato":      "佐藤 健一",
        "suzuki":    "鈴木 大輔",
        "takahashi": "高橋 修",
    }

    # 未完了タスク（PK: TASK#<uuid>）
    pending_tasks = [
        {"work": "給湯器交換工事", "location": "",             "assignee": "sato",      "scheduled_date": today,     "status": "in_progress"},
        {"work": "エアコン新設",   "location": "3F事務所",     "assignee": "suzuki",    "scheduled_date": today,     "status": "pending"},
        {"work": "排水管高圧洗浄", "location": "佐々木ビル",   "assignee": "sato",      "scheduled_date": today,     "status": "pending"},
        {"work": "ボイラー点検",   "location": "中村工場",     "assignee": "takahashi", "scheduled_date": today,     "status": "in_progress"},
        {"work": "水道メーター交換", "location": "田村邸",     "assignee": "suzuki",    "scheduled_date": tomorrow,  "status": "pending"},
    ]

    # 完了済みタスク（PK: DONE#<uuid>）
    done_tasks = [
        {"work": "水漏れ修理",       "location": "田村マンション201", "assignee": "takahashi", "scheduled_date": today,     "status": "completed"},
        {"work": "トイレ詰まり修理", "location": "山田様邸",         "assignee": "sato",      "scheduled_date": yesterday, "status": "completed"},
    ]

    inserted = 0

    for task in pending_tasks:
        pk = f"TASK#{uuid.uuid4()}"
        # 新規UUIDなので同PKは存在しないが、仕様に従い既存チェックを行う
        response = table.get_item(Key={"task_id": pk, "assignee_id": task["assignee"]})
        if "Item" in response:
            continue

        table.put_item(Item={
            "task_id":        pk,
            "assignee_id":    task["assignee"],
            "assignee_name":  name_map[task["assignee"]],
            "work":           task["work"],
            "location":       task["location"],
            "scheduled_date": task["scheduled_date"],
            "status":         task["status"],
            "created_by":     "tanaka",
            "created_at":     now,
            "updated_at":     now,
        })
        inserted += 1

    for task in done_tasks:
        pk = f"DONE#{uuid.uuid4()}"
        response = table.get_item(Key={"task_id": pk, "assignee_id": task["assignee"]})
        if "Item" in response:
            continue

        table.put_item(Item={
            "task_id":        pk,
            "assignee_id":    task["assignee"],
            "assignee_name":  name_map[task["assignee"]],
            "work":           task["work"],
            "location":       task["location"],
            "scheduled_date": task["scheduled_date"],
            "status":         task["status"],
            "created_by":     "tanaka",
            "created_at":     now,
            "updated_at":     now,
        })
        inserted += 1

    return inserted


# ─── メイン ────────────────────────────────────────────────────────────────────

def main() -> None:
    """テーブル作成と初期データ投入を実行する"""
    # テーブル作成（既存の場合はスキップ）
    create_user_table()
    create_task_table()

    # 初期データ投入
    user_table = dynamodb.Table(USER_TABLE_NAME)
    task_table = dynamodb.Table(TASK_TABLE_NAME)

    user_count = seed_users(user_table)
    task_count = seed_tasks(task_table)

    # サマリー出力
    print(f"✅ ユーザー {user_count}件 投入完了")
    print(f"✅ タスク {task_count}件 投入完了")


if __name__ == "__main__":
    main()
