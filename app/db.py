"""SQLiteによるAPIキー台帳の永続化層。"""

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    department TEXT NOT NULL,
    budget INTEGER NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    issued_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def key_exists(self, api_key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM api_keys WHERE api_key = ?", (api_key,)
        ).fetchone()
        return row is not None

    def insert(
        self,
        user_name: str,
        department: str,
        budget: int,
        api_key: str,
        issued_at: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO api_keys (user_name, department, budget, api_key, issued_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_name, department, budget, api_key, issued_at),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
