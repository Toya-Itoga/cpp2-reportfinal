"""
tests/test_auth_service.py
auth_service のユニットテスト

パスワードハッシュ化・検証、JWT発行・検証の基本動作を確認する。
DynamoDB には接続しない（ユニットテスト）。
"""

import os
import sys
import pytest

# src/ を Python パスに追加（Lambda 対応パスと同じ構成）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# テスト用環境変数を設定（実際の.envファイルは読み込まない）
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_HOURS", "6")

from services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
)


# ---------------------------------------------------------------------------
# パスワードハッシュ化・検証テスト
# ---------------------------------------------------------------------------
class TestPassword:
    def test_hash_password_returns_string(self):
        """hash_password が文字列を返すこと"""
        result = hash_password("password123")
        assert isinstance(result, str)

    def test_hash_password_is_not_plaintext(self):
        """ハッシュ値が平文と異なること"""
        pw = "password123"
        hashed = hash_password(pw)
        assert hashed != pw

    def test_verify_password_correct(self):
        """正しいパスワードで verify_password が True を返すこと"""
        pw = "correct_password"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_password_incorrect(self):
        """誤ったパスワードで verify_password が False を返すこと"""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_different_each_time(self):
        """同じパスワードでも毎回異なるハッシュが生成されること (bcrypt ソルト)"""
        pw = "same_password"
        hash1 = hash_password(pw)
        hash2 = hash_password(pw)
        assert hash1 != hash2
        # どちらも検証は通ること
        assert verify_password(pw, hash1) is True
        assert verify_password(pw, hash2) is True


# ---------------------------------------------------------------------------
# JWT 発行・検証テスト
# ---------------------------------------------------------------------------
class TestJWT:
    def test_create_token_returns_string(self):
        """create_token が文字列を返すこと"""
        token = create_token("user1", "admin", "テストユーザー")
        assert isinstance(token, str)

    def test_decode_token_returns_payload(self):
        """decode_token が正しいペイロードを返すこと"""
        token = create_token("user1", "admin", "テストユーザー")
        payload = decode_token(token)
        assert payload is not None
        assert payload["username"] == "user1"
        assert payload["role"] == "admin"
        assert payload["name"] == "テストユーザー"

    def test_decode_invalid_token_returns_none(self):
        """無効なトークンで decode_token が None を返すこと"""
        result = decode_token("invalid.token.string")
        assert result is None

    def test_decode_empty_token_returns_none(self):
        """空文字トークンで decode_token が None を返すこと"""
        result = decode_token("")
        assert result is None

    def test_token_contains_exp(self):
        """トークンに有効期限 (exp) が含まれること"""
        token = create_token("user1", "employee", "従業員")
        payload = decode_token(token)
        assert payload is not None
        assert "exp" in payload
