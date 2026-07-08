"""docs/requirements.md「エラーメッセージ一覧」(MSG-001〜006)の確定文言。

表記ゆれ防止のため、テストは必ず本モジュールの定数で完全一致判定する。
"""

import re

MSG_NAME_EMPTY = "利用者名を入力してください"                              # MSG-001
MSG_NAME_TOO_LONG = "利用者名は50文字以内で入力してください"                 # MSG-002
MSG_BUDGET_EMPTY = "予算上限を入力してください"                            # MSG-003
MSG_BUDGET_NOT_INT = "予算上限は整数で入力してください"                     # MSG-004
MSG_BUDGET_OUT_OF_RANGE = "予算上限は1〜1,000,000の範囲で入力してください"   # MSG-005

# MSG-006: 発行しました: <キー>(<キー>は ^sk-[a-z0-9]{32}$ に合致)
KEY_PATTERN = r"sk-[a-z0-9]{32}"
ISSUED_PATTERN = rf"^発行しました: ({KEY_PATTERN})$"


def extract_key(status_text: str) -> str | None:
    """成功メッセージからAPIキー部分を取り出す。形式不一致なら None。"""
    m = re.match(ISSUED_PATTERN, status_text)
    return m.group(1) if m else None
