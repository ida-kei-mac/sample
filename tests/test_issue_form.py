"""docs/test-design.md TC-001〜TC-032 のUIテスト。

情報源は docs/ のみ(app/ のソースコードは参照しない)。
期待文言は messages.py(=requirements.md「エラーメッセージ一覧」)との完全一致で判定する。
"""

import re

import pytest

from conftest import FAKE_NOW
from messages import (
    ISSUED_PATTERN,
    MSG_BUDGET_EMPTY,
    MSG_BUDGET_NOT_INT,
    MSG_BUDGET_OUT_OF_RANGE,
    MSG_NAME_EMPTY,
    MSG_NAME_TOO_LONG,
    extract_key,
)

NAME_50 = "あ" * 50
NAME_51 = "あ" * 51
NAME_50_MIXED = "あ" * 25 + "a" * 25  # 全角25+半角25


def _issue(app, name: str, budget: str) -> str:
    """入力して[発行]をクリックし、ステータス欄が成功文言になるまで待って返す。"""
    app.page.set_user_name(name)
    app.page.set_budget(budget)
    app.page.click_issue()
    return app.page.wait_status_matches(ISSUED_PATTERN)


# --- 1. 画面初期状態 ---


@pytest.mark.req("REQ-001")
def test_tc001_initial_user_name_is_empty(app):
    assert app.page.get_user_name() == ""


@pytest.mark.req("REQ-002")
def test_tc002_initial_department_items_and_selection(app):
    assert app.page.get_department_items() == ["開発部", "営業部", "管理部"]
    assert app.page.get_department() == "開発部"


@pytest.mark.req("REQ-003")
def test_tc003_initial_budget_is_empty(app):
    assert app.page.get_budget() == ""


@pytest.mark.req("REQ-004")
def test_tc004_initial_status_is_empty(app):
    assert app.page.get_status() == ""


@pytest.mark.req("REQ-005")
def test_tc005_issue_button_is_enabled(app):
    assert app.page.is_issue_enabled()


@pytest.mark.req("REQ-006")
def test_tc006_department_always_selected(app):
    app.page.select_department("営業部")
    assert app.page.get_department() == "営業部"


# --- 2. 検証の共通ルール ---


@pytest.mark.req("REQ-007")
@pytest.mark.req("REQ-019")
def test_tc007_trims_half_width_spaces_before_validation_and_save(app):
    status = _issue(app, " 田中 ", " 100 ")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"
    rows = app.db_rows()
    assert len(rows) == 1
    row = rows[0]
    assert "田中" in row, f"row={row!r}"          # トリム後の利用者名で保存される
    assert " 田中 " not in row
    assert 100 in row                              # 整数に変換された予算上限


@pytest.mark.req("REQ-007")
@pytest.mark.req("REQ-010")
def test_tc008_name_of_only_half_width_spaces_is_empty(app):
    app.page.set_user_name("   ")
    app.page.set_budget("100")
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_NAME_EMPTY) == MSG_NAME_EMPTY
    assert app.db_row_count() == 0


@pytest.mark.req("REQ-008")
def test_tc009_name_length_counts_unicode_chars(app):
    status = _issue(app, NAME_50_MIXED, "100")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"


@pytest.mark.req("REQ-009")
def test_tc010_first_matching_error_only(app):
    # 利用者名・予算上限とも空 → 先頭の検証(利用者名)のエラーのみ表示
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_NAME_EMPTY) == MSG_NAME_EMPTY


# --- 3. 利用者名の検証 ---


@pytest.mark.req("REQ-010")
def test_tc011_empty_name_shows_error_and_not_saved(app):
    app.page.set_budget("100")
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_NAME_EMPTY) == MSG_NAME_EMPTY
    assert app.db_row_count() == 0


@pytest.mark.req("REQ-011")
def test_tc012_name_51_chars_shows_error_and_not_saved(app):
    app.page.set_user_name(NAME_51)
    app.page.set_budget("100")
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_NAME_TOO_LONG) == MSG_NAME_TOO_LONG
    assert app.db_row_count() == 0


@pytest.mark.req("REQ-011")
def test_tc013_name_50_chars_is_accepted(app):
    status = _issue(app, NAME_50, "100")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"


# --- 4. 予算上限の検証 ---


@pytest.mark.req("REQ-012")
def test_tc014_empty_budget_shows_error_and_not_saved(app):
    app.page.set_user_name("田中")
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_BUDGET_EMPTY) == MSG_BUDGET_EMPTY
    assert app.db_row_count() == 0


def _assert_budget_not_int(app, budget: str):
    app.page.set_user_name("田中")
    app.page.set_budget(budget)
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_BUDGET_NOT_INT) == MSG_BUDGET_NOT_INT
    assert app.db_row_count() == 0


@pytest.mark.req("REQ-013")
def test_tc015_non_numeric_budget(app):
    _assert_budget_not_int(app, "abc")


@pytest.mark.req("REQ-013")
def test_tc016_negative_budget(app):
    _assert_budget_not_int(app, "-5")


@pytest.mark.req("REQ-013")
def test_tc017_full_width_digits_budget(app):
    _assert_budget_not_int(app, "１００")


@pytest.mark.req("REQ-013")
def test_tc018_decimal_budget(app):
    _assert_budget_not_int(app, "1.5")


@pytest.mark.req("REQ-013")
def test_tc019_comma_separated_budget(app):
    _assert_budget_not_int(app, "1,000")


def _assert_budget_out_of_range(app, budget: str):
    app.page.set_user_name("田中")
    app.page.set_budget(budget)
    app.page.click_issue()
    assert (
        app.page.wait_status_equals(MSG_BUDGET_OUT_OF_RANGE) == MSG_BUDGET_OUT_OF_RANGE
    )
    assert app.db_row_count() == 0


@pytest.mark.req("REQ-014")
def test_tc020_budget_zero_is_rejected(app):
    _assert_budget_out_of_range(app, "0")


@pytest.mark.req("REQ-014")
def test_tc021_budget_one_is_accepted(app):
    status = _issue(app, "田中", "1")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"


@pytest.mark.req("REQ-014")
def test_tc022_budget_million_is_accepted(app):
    status = _issue(app, "田中", "1000000")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"


@pytest.mark.req("REQ-014")
def test_tc023_budget_million_plus_one_is_rejected(app):
    _assert_budget_out_of_range(app, "1000001")


@pytest.mark.req("REQ-014")
@pytest.mark.req("REQ-019")
def test_tc024_leading_zeros_treated_as_integer(app):
    status = _issue(app, "田中", "007")
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"
    rows = app.db_rows()
    assert len(rows) == 1
    assert 7 in rows[0], f"row={rows[0]!r}"  # 整数値7として保存される


# --- 5. 検証NG時の共通動作 ---


@pytest.mark.req("REQ-015")
def test_tc025_inputs_kept_on_validation_error(app):
    app.page.set_user_name(NAME_51)
    app.page.select_department("営業部")
    app.page.set_budget("100")
    app.page.click_issue()
    assert app.page.wait_status_equals(MSG_NAME_TOO_LONG) == MSG_NAME_TOO_LONG
    assert app.page.get_user_name() == NAME_51
    assert app.page.get_department() == "営業部"
    assert app.page.get_budget() == "100"


@pytest.mark.req("REQ-016")
def test_tc026_existing_records_kept_on_validation_error(app):
    status = _issue(app, "田中", "1")
    key = extract_key(status)
    assert key is not None, f"status={status!r}"
    assert app.db_row_count() == 1

    app.page.set_budget("0")
    app.page.click_issue()
    assert (
        app.page.wait_status_equals(MSG_BUDGET_OUT_OF_RANGE) == MSG_BUDGET_OUT_OF_RANGE
    )
    rows = app.db_rows()
    assert len(rows) == 1
    assert key in rows[0], f"row={rows[0]!r}"  # 既存レコードが変更されていない


# --- 6. 検証OK時(発行処理) ---


@pytest.mark.req("REQ-017")
@pytest.mark.req("REQ-021")
def test_tc027_key_format(app):
    status = _issue(app, "田中", "100")
    key = extract_key(status)
    assert key is not None, f"status={status!r}"
    assert re.fullmatch(r"sk-[a-z0-9]{32}", key)


@pytest.mark.req("REQ-018")
def test_tc028_keys_are_unique(app):
    status1 = _issue(app, "田中", "100")
    key1 = extract_key(status1)
    assert key1 is not None, f"status={status1!r}"

    app.page.click_issue()
    status2 = app.page.wait_status(
        lambda t: re.match(ISSUED_PATTERN, t) is not None and t != status1
    )
    key2 = extract_key(status2)
    assert key2 is not None, f"status={status2!r}"
    assert key1 != key2

    rows = app.db_rows()
    assert len(rows) == 2
    saved_keys = {v for row in rows for v in row if isinstance(v, str) and v.startswith("sk-")}
    assert saved_keys == {key1, key2}


@pytest.mark.req("REQ-019")
def test_tc029_saved_record_contents(app):
    app.page.set_user_name("田中")
    app.page.select_department("管理部")
    app.page.set_budget("500")
    app.page.click_issue()
    status = app.page.wait_status_matches(ISSUED_PATTERN)
    key = extract_key(status)
    assert key is not None, f"status={status!r}"

    rows = app.db_rows()
    assert len(rows) == 1
    row = rows[0]
    assert "田中" in row, f"row={row!r}"
    assert "管理部" in row, f"row={row!r}"
    assert 500 in row, f"row={row!r}"
    assert key in row, f"row={row!r}"
    assert FAKE_NOW in row, f"row={row!r}"  # 発行日時はAPP_FAKE_NOWの値


@pytest.mark.req("REQ-020")
def test_tc030_same_name_can_issue_multiple_times(app):
    status1 = _issue(app, "田中", "100")
    assert re.match(ISSUED_PATTERN, status1), f"status={status1!r}"

    app.page.click_issue()
    status2 = app.page.wait_status(
        lambda t: re.match(ISSUED_PATTERN, t) is not None and t != status1
    )
    assert re.match(ISSUED_PATTERN, status2), f"status={status2!r}"
    assert app.db_row_count() == 2


@pytest.mark.req("REQ-021")
def test_tc031_success_message_exact_format(app):
    status = _issue(app, "田中", "100")
    key = extract_key(status)
    assert key is not None, f"status={status!r}"
    assert status == f"発行しました: {key}"


@pytest.mark.req("REQ-022")
def test_tc032_inputs_kept_after_success(app):
    app.page.set_user_name("田中")
    app.page.select_department("営業部")
    app.page.set_budget("100")
    app.page.click_issue()
    status = app.page.wait_status_matches(ISSUED_PATTERN)
    assert re.match(ISSUED_PATTERN, status), f"status={status!r}"
    assert app.page.get_user_name() == "田中"
    assert app.page.get_department() == "営業部"
    assert app.page.get_budget() == "100"
