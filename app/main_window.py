"""発行登録フォーム(ステップ1)。"""

import os
import re
import secrets
from datetime import datetime

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db import Database

DEPARTMENTS = ["開発部", "営業部", "管理部"]

MSG_NAME_EMPTY = "利用者名を入力してください"
MSG_NAME_TOO_LONG = "利用者名は50文字以内で入力してください"
MSG_BUDGET_EMPTY = "予算上限を入力してください"
MSG_BUDGET_NOT_INT = "予算上限は整数で入力してください"
MSG_BUDGET_OUT_OF_RANGE = "予算上限は1〜1,000,000の範囲で入力してください"
MSG_ISSUED = "発行しました: {key}"

_KEY_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
_DIGITS_ONLY = re.compile(r"^[0-9]+$")


def _now_iso() -> str:
    # REQ: APP_FAKE_NOW(ISO8601)があれば現在時刻より優先する
    fake = os.environ.get("APP_FAKE_NOW")
    if fake:
        return fake
    return datetime.now().isoformat(timespec="seconds")


def generate_key() -> str:
    return "sk-" + "".join(secrets.choice(_KEY_CHARS) for _ in range(32))


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self.setObjectName("mainWindow")
        self.setWindowTitle("APIキー発行台帳")

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        self.user_name_label = QLabel("利用者名")
        self.user_name_label.setObjectName("userNameLabel")
        self.user_name_line_edit = QLineEdit()
        self.user_name_line_edit.setObjectName("userNameLineEdit")

        self.department_label = QLabel("部署")
        self.department_label.setObjectName("departmentLabel")
        self.department_combo_box = QComboBox()
        self.department_combo_box.setObjectName("departmentComboBox")
        self.department_combo_box.addItems(DEPARTMENTS)
        self.department_combo_box.setCurrentIndex(0)

        self.budget_label = QLabel("予算上限")
        self.budget_label.setObjectName("budgetLabel")
        self.budget_line_edit = QLineEdit()
        self.budget_line_edit.setObjectName("budgetLineEdit")

        self.issue_button = QPushButton("発行")
        self.issue_button.setObjectName("issueButton")
        self.issue_button.clicked.connect(self._on_issue_clicked)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")

        form = QFormLayout()
        form.addRow(self.user_name_label, self.user_name_line_edit)
        form.addRow(self.department_label, self.department_combo_box)
        form.addRow(self.budget_label, self.budget_line_edit)

        layout = QVBoxLayout(central)
        layout.addLayout(form)
        layout.addWidget(self.issue_button)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def _on_issue_clicked(self) -> None:
        # トリムは半角空白(0x20)のみが対象。全角空白は残す
        user_name = self.user_name_line_edit.text().strip(" ")
        budget_text = self.budget_line_edit.text().strip(" ")

        error = self._validate(user_name, budget_text)
        if error is not None:
            self.status_label.setText(error)
            return

        key = generate_key()
        while self._db.key_exists(key):
            key = generate_key()

        self._db.insert(
            user_name=user_name,
            department=self.department_combo_box.currentText(),
            budget=int(budget_text),
            api_key=key,
            issued_at=_now_iso(),
        )
        self.status_label.setText(MSG_ISSUED.format(key=key))

    @staticmethod
    def _validate(user_name: str, budget_text: str) -> str | None:
        if len(user_name) == 0:
            return MSG_NAME_EMPTY
        if len(user_name) > 50:
            return MSG_NAME_TOO_LONG
        if len(budget_text) == 0:
            return MSG_BUDGET_EMPTY
        if not _DIGITS_ONLY.match(budget_text):
            return MSG_BUDGET_NOT_INT
        if not 1 <= int(budget_text) <= 1_000_000:
            return MSG_BUDGET_OUT_OF_RANGE
        return None
