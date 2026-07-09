"""アプリ起動/終了fixture、失敗時スクリーンショット保存フック、画面録画fixture。"""

import glob
import os
import shutil
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


def _find_ffmpeg() -> str | None:
    """ffmpeg実行ファイルを探す(PATH → wingetインストール先の順)。"""
    path = shutil.which("ffmpeg")
    if path:
        return path
    pattern = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe",
    )
    hits = glob.glob(pattern, recursive=True)
    return hits[0] if hits else None


@pytest.fixture(scope="session", autouse=True)
def screen_recording():
    """pytest実行全体をffmpegでデスクトップ録画し、artifacts/ にmp4で保存する。

    ffmpegが見つからない場合は録画なしで実行を続ける(テスト結果には影響させない)。
    """
    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        yield None
        return
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    save_path = ARTIFACTS_DIR / f"test-run-{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    recorder = subprocess.Popen(
        [
            ffmpeg, "-y",
            "-f", "gdigrab", "-framerate", "10", "-i", "desktop",
            "-vcodec", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(save_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield save_path
    finally:
        # 'q' 送信で正常終了させ、mp4のインデックスを確定させる
        try:
            recorder.stdin.write(b"q")
            recorder.stdin.flush()
            recorder.wait(timeout=15)
        except Exception:
            recorder.terminate()


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
