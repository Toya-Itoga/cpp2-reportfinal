# src/database.py
# DynamoDB 接続設定

import os
import boto3
from dotenv import load_dotenv

# .env ファイルの読み込み (ローカル開発環境用)
load_dotenv()


# ---------------------------------------------------------------------------
# DynamoDB リソース取得
# ---------------------------------------------------------------------------
def get_dynamodb():
    """DynamoDB リソースを返す。環境変数でエンドポイントを切り替える。

    ローカル開発時は DYNAMODB_ENDPOINT を設定して DynamoDB Local を使用する。
    本番環境 (Lambda) では環境変数を未設定にして AWS の DynamoDB に接続する。
    """
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT")
    region = os.getenv("DYNAMODB_REGION", "ap-northeast-1")

    kwargs: dict = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    return boto3.resource("dynamodb", **kwargs)


# ---------------------------------------------------------------------------
# テーブル取得ヘルパー
# ---------------------------------------------------------------------------
def get_user_table():
    """User テーブルを返す。テーブル名は環境変数 USER_TABLE_NAME で設定する。"""
    table_name = os.getenv("USER_TABLE_NAME", "User")
    return get_dynamodb().Table(table_name)


def get_task_table():
    """Task テーブルを返す。テーブル名は環境変数 TASK_TABLE_NAME で設定する。"""
    table_name = os.getenv("TASK_TABLE_NAME", "Task")
    return get_dynamodb().Table(table_name)
