# src/utils/datetime.py
# 日時ユーティリティ関数 (標準ライブラリのみ使用)

from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# タイムゾーン定義
# ---------------------------------------------------------------------------
JST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# 日時取得関数
# ---------------------------------------------------------------------------
def now_jst() -> datetime:
    """現在の JST 日時を返す"""
    return datetime.now(JST)


def today_str() -> str:
    """今日の日付を YYYY-MM-DD 形式の文字列で返す"""
    return now_jst().strftime("%Y-%m-%d")


def now_iso() -> str:
    """現在の JST 日時を ISO 8601 形式の文字列で返す"""
    return now_jst().isoformat()


# ---------------------------------------------------------------------------
# フォーマット関数
# ---------------------------------------------------------------------------
def format_date_jp(date_str: str) -> str:
    """YYYY-MM-DD 形式の日付文字列を M月D日 形式に変換する。

    変換できない場合は元の文字列をそのまま返す。
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{dt.month}月{dt.day}日"
    except ValueError:
        return date_str
