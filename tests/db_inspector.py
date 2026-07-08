"""--test 起動時の一時SQLiteファイルを検証するヘルパ。

DBの配置パス・スキーマは仕様書(docs/)に定義がないため、
「--test 起動時は一時ファイルSQLiteを使用する」(CLAUDE.md)という事実のみに基づき、
アプリ起動後に一時ディレクトリへ作成されたSQLiteファイルを探索し、
スキーマ非依存(SELECT *)で行を読む。値の検証は行タプルへの含有判定で行う。
"""

import glob
import os
import sqlite3
import tempfile

_PATTERNS = ("*.sqlite3", "*.sqlite", "*.db")


def find_app_db(created_after: float) -> str | None:
    """アプリ起動時刻以降に作成された一時SQLiteファイルのうち最新のものを返す。"""
    candidates = []
    tmp_dir = tempfile.gettempdir()
    for pattern in _PATTERNS:
        for path in glob.glob(os.path.join(tmp_dir, pattern)):
            try:
                if os.path.getctime(path) >= created_after - 2:
                    candidates.append(path)
            except OSError:
                continue
    if not candidates:
        return None
    return max(candidates, key=os.path.getctime)


def read_all_rows(db_path: str) -> list[tuple]:
    """全ユーザーテーブルの全行を読み取り専用で返す。"""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master"
                " WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        rows: list[tuple] = []
        for table in tables:
            rows.extend(con.execute(f'SELECT * FROM "{table}"').fetchall())
        return rows
    finally:
        con.close()
