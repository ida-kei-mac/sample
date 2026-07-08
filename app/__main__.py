"""python -m app で発行登録フォームを起動する。"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.db import Database
from app.main_window import MainWindow


def main() -> int:
    parser = argparse.ArgumentParser(prog="app")
    parser.add_argument(
        "--test",
        action="store_true",
        help="UIテスト用: 一時ファイルSQLiteを使い、ウィンドウ位置サイズを固定する",
    )
    args = parser.parse_args()

    if args.test:
        fd, db_path = tempfile.mkstemp(prefix="apikeys_", suffix=".sqlite3")
        os.close(fd)
    else:
        db_path = str(Path.cwd() / "apikeys.db")

    app = QApplication(sys.argv)
    db = Database(db_path)
    window = MainWindow(db)
    if args.test:
        window.move(100, 100)
        window.setFixedSize(800, 600)
    window.show()
    exit_code = app.exec()
    db.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
