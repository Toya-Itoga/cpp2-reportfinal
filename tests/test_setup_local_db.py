"""scripts/setup_local_db.py のユニットテスト

DynamoDB Localへの接続なしにロジック単体を検証する。
"""

import importlib
import sys
import types
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch


# ─── モジュール読み込みのヘルパー ──────────────────────────────────────────────

def _load_module():
    """setup_local_db.py をモック依存関係で読み込む"""
    # 外部ライブラリをスタブに置き換えてインポート
    boto3_stub = MagicMock()
    bcrypt_stub = MagicMock()
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda: None
    botocore_stub = types.ModuleType("botocore")
    botocore_exceptions = types.ModuleType("botocore.exceptions")

    class _ClientError(Exception):
        def __init__(self, code: str):
            self.response = {"Error": {"Code": code}}
    botocore_exceptions.ClientError = _ClientError

    with patch.dict(sys.modules, {
        "boto3": boto3_stub,
        "bcrypt": bcrypt_stub,
        "dotenv": dotenv_stub,
        "botocore": botocore_stub,
        "botocore.exceptions": botocore_exceptions,
    }):
        # キャッシュを無効化して再インポート
        sys.modules.pop("setup_local_db", None)
        spec = importlib.util.spec_from_file_location(
            "setup_local_db",
            "scripts/setup_local_db.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    return mod, bcrypt_stub, botocore_exceptions.ClientError


# ─── hash_password ──────────────────────────────────────────────────────────────

class TestHashPassword:
    def test_returns_decoded_string(self):
        mod, bcrypt_stub, _ = _load_module()
        bcrypt_stub.hashpw.return_value = b"$2b$12$hashed"
        bcrypt_stub.gensalt.return_value = b"$2b$12$salt"

        result = mod.hash_password("secret")

        bcrypt_stub.hashpw.assert_called_once_with(b"secret", b"$2b$12$salt")
        assert result == "$2b$12$hashed"


# ─── seed_users ────────────────────────────────────────────────────────────────

class TestSeedUsers:
    def _make_table(self, existing_usernames: list[str]) -> MagicMock:
        """DynamoDB テーブルモックを生成する"""
        table = MagicMock()

        def get_item(Key):
            if Key["username"] in existing_usernames:
                return {"Item": {"username": Key["username"]}}
            return {}

        table.get_item.side_effect = get_item
        return table

    def test_inserts_all_users_when_table_empty(self):
        mod, bcrypt_stub, _ = _load_module()
        bcrypt_stub.hashpw.return_value = b"hashed"
        bcrypt_stub.gensalt.return_value = b"salt"
        table = self._make_table([])

        count = mod.seed_users(table)

        assert count == 4
        assert table.put_item.call_count == 4

    def test_skips_existing_user(self):
        mod, bcrypt_stub, _ = _load_module()
        bcrypt_stub.hashpw.return_value = b"hashed"
        bcrypt_stub.gensalt.return_value = b"salt"
        table = self._make_table(["tanaka", "sato"])

        count = mod.seed_users(table)

        assert count == 2  # suzuki と takahashi のみ投入

    def test_put_item_contains_required_fields(self):
        mod, bcrypt_stub, _ = _load_module()
        bcrypt_stub.hashpw.return_value = b"hashed"
        bcrypt_stub.gensalt.return_value = b"salt"
        table = self._make_table([])

        mod.seed_users(table)

        # 最初のputの引数（田中）を検証
        first_call_item = table.put_item.call_args_list[0].kwargs["Item"]
        assert first_call_item["username"] == "tanaka"
        assert first_call_item["role"] == "admin"
        assert first_call_item["is_active"] is True
        assert "user_id" in first_call_item
        assert "password_hash" in first_call_item
        assert "created_at" in first_call_item

    def test_password_is_not_stored_in_plain_text(self):
        mod, bcrypt_stub, _ = _load_module()
        bcrypt_stub.hashpw.return_value = b"hashed"
        bcrypt_stub.gensalt.return_value = b"salt"
        table = self._make_table([])

        mod.seed_users(table)

        for call_kwargs in table.put_item.call_args_list:
            item = call_kwargs.kwargs["Item"]
            assert "password" not in item, "平文パスワードが保存されている"


# ─── seed_tasks ────────────────────────────────────────────────────────────────

class TestSeedTasks:
    def _make_table(self) -> MagicMock:
        table = MagicMock()
        # 新規UUIDのため既存アイテムは常に存在しない
        table.get_item.return_value = {}
        return table

    def test_inserts_7_tasks(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        count = mod.seed_tasks(table)

        assert count == 7
        assert table.put_item.call_count == 7

    def test_pending_tasks_have_task_prefix(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        mod.seed_tasks(table)

        items = [c.kwargs["Item"] for c in table.put_item.call_args_list]
        pending = [i for i in items if i["status"] != "completed"]
        assert len(pending) == 5
        for item in pending:
            assert item["task_id"].startswith("TASK#"), f"プレフィックスがTASK#でない: {item['task_id']}"

    def test_done_tasks_have_done_prefix(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        mod.seed_tasks(table)

        items = [c.kwargs["Item"] for c in table.put_item.call_args_list]
        done = [i for i in items if i["status"] == "completed"]
        assert len(done) == 2
        for item in done:
            assert item["task_id"].startswith("DONE#"), f"プレフィックスがDONE#でない: {item['task_id']}"

    def test_task_has_work_and_location_fields(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        mod.seed_tasks(table)

        for c in table.put_item.call_args_list:
            item = c.kwargs["Item"]
            assert "work" in item, "workフィールドが存在しない"
            assert "location" in item, "locationフィールドが存在しない"
            assert "title" not in item, "titleフィールドを使ってはならない"

    def test_task_has_required_fields(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        mod.seed_tasks(table)

        required = {"task_id", "assignee_id", "assignee_name", "work", "location",
                    "scheduled_date", "status", "created_by", "created_at", "updated_at"}
        for c in table.put_item.call_args_list:
            item = c.kwargs["Item"]
            assert required.issubset(item.keys()), f"必須フィールドが不足: {required - item.keys()}"

    def test_created_by_is_tanaka(self):
        mod, _, _ = _load_module()
        table = self._make_table()

        mod.seed_tasks(table)

        for c in table.put_item.call_args_list:
            item = c.kwargs["Item"]
            assert item["created_by"] == "tanaka"


# ─── create_user_table / create_task_table ────────────────────────────────────

class TestCreateTables:
    def test_create_user_table_skips_on_existing(self):
        mod, _, ClientError = _load_module()

        mock_dynamodb = MagicMock()
        mock_dynamodb.create_table.side_effect = ClientError("ResourceInUseException")
        mod.dynamodb = mock_dynamodb

        # 例外が外へ伝播しないこと
        mod.create_user_table()

    def test_create_task_table_skips_on_existing(self):
        mod, _, ClientError = _load_module()

        mock_dynamodb = MagicMock()
        mock_dynamodb.create_table.side_effect = ClientError("ResourceInUseException")
        mod.dynamodb = mock_dynamodb

        mod.create_task_table()

    def test_create_user_table_raises_on_other_error(self):
        import pytest
        mod, _, ClientError = _load_module()

        mock_dynamodb = MagicMock()
        mock_dynamodb.create_table.side_effect = ClientError("InternalServerError")
        mod.dynamodb = mock_dynamodb

        with pytest.raises(ClientError):
            mod.create_user_table()
