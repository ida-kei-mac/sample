"""アプリ起動/終了fixtureと、失敗時スクリーンショット保存フック。"""

import os
import subprocess
import time
from pathlib import Path

import pytest
import uiautomation as auto

import db_inspector
from pages import IssueFormPage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# 共通前提P2(docs/test-design.md): 発行日時の検証用固定時刻
FAKE_NOW = "2026-07-09T12:00:00"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "req(req_id): 対応する要件ID(docs/requirements.md)"
    )


class AppUnderTest:
    """テスト対象アプリ1プロセス分のハンドル。page(UI操作)とDB検証を束ねる。"""

    def __init__(self, page: IssueFormPage, started_at: float):
        self.page = page
        self.started_at = started_at

    def db_rows(self) -> list[tuple]:
        db_path = db_inspector.find_app_db(self.started_at)
        if db_path is None:
            return []
        return db_inspector.read_all_rows(db_path)

    def db_row_count(self) -> int:
        return len(self.db_rows())


@pytest.fixture
def app():
    """`python -m app --test` でアプリを起動し、終了まで面倒を見る(共通前提P1/P2)。"""
    env = os.environ.copy()
    env["APP_FAKE_NOW"] = FAKE_NOW
    started_at = time.time()
    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "app", "--test"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    page = IssueFormPage()
    try:
        assert page.wait_shown(timeout=15), "アプリのメインウィンドウが表示されませんでした"
        yield AppUnderTest(page, started_at)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト失敗時にウィンドウのスクリーンショットを artifacts/ へ保存する。"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    save_path = ARTIFACTS_DIR / f"{item.name}.png"
    try:
        aut = item.funcargs.get("app")
        window = aut.page.window if aut is not None else None
        if window is not None and window.Exists(maxSearchSeconds=1):
            window.CaptureToImage(str(save_path))
        else:
            auto.GetRootControl().CaptureToImage(str(save_path))
    except Exception:
        # スクリーンショット失敗でテスト結果自体は変えない
        pass
