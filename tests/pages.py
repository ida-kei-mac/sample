"""発行登録フォームのページオブジェクト。

ロケータ(objectName)は本モジュールに集約する(docs/screen-spec.md「コントロール一覧」準拠)。
テスト本体は objectName を直書きせず、必ず IssueFormPage 経由で操作する。
"""

import re
import time

import uiautomation as auto

WINDOW_TITLE = "APIキー発行台帳"

# docs/screen-spec.md の objectName
MAIN_WINDOW = "mainWindow"
USER_NAME_LINE_EDIT = "userNameLineEdit"
DEPARTMENT_COMBO_BOX = "departmentComboBox"
BUDGET_LINE_EDIT = "budgetLineEdit"
ISSUE_BUTTON = "issueButton"
STATUS_LABEL = "statusLabel"

DEFAULT_WAIT = 5.0

# ポーリング間隔の明示待機に使う、存在しない objectName
_POLL_DUMMY = "__poll_wait_no_such_object__"


class IssueFormPage:
    """UIAutomation 経由で発行登録フォームを操作する。

    コントロールはプロパティアクセスのたびに再探索し、常に最新状態を参照する。
    クリックは実マウスではなく UIA パターン(Invoke / Value / SelectionItem)で行う。
    """

    @property
    def window(self) -> auto.WindowControl:
        return auto.WindowControl(searchDepth=1, Name=WINDOW_TITLE)

    def wait_shown(self, timeout: float = 15.0) -> bool:
        return self.window.Exists(maxSearchSeconds=timeout)

    def _control(self, object_name: str) -> auto.Control:
        return self.window.Control(searchDepth=10, AutomationId=object_name)

    # --- 利用者名 ---

    def set_user_name(self, text: str) -> None:
        self._control(USER_NAME_LINE_EDIT).GetValuePattern().SetValue(text)

    def get_user_name(self) -> str:
        return self._control(USER_NAME_LINE_EDIT).GetValuePattern().Value

    # --- 部署 ---

    def get_department(self) -> str:
        combo = self._control(DEPARTMENT_COMBO_BOX)
        try:
            value = combo.GetValuePattern().Value
            if value:
                return value
        except Exception:
            pass
        selection = combo.GetSelectionPattern().GetSelection()
        return selection[0].Name

    def get_department_items(self) -> list[str]:
        combo = self._control(DEPARTMENT_COMBO_BOX)
        expand = combo.GetExpandCollapsePattern()
        expand.Expand()
        try:
            items = [c.Name for c in self._department_list_items(combo)]
        finally:
            try:
                expand.Collapse()
            except Exception:
                pass
        return items

    def select_department(self, name: str) -> None:
        combo = self._control(DEPARTMENT_COMBO_BOX)
        expand = combo.GetExpandCollapsePattern()
        expand.Expand()
        try:
            for item in self._department_list_items(combo):
                if item.Name == name:
                    item.GetSelectionItemPattern().Select()
                    return
            raise AssertionError(f"部署コンボボックスに項目 {name!r} が見つかりません")
        finally:
            try:
                expand.Collapse()
            except Exception:
                pass

    @staticmethod
    def _department_list_items(combo: auto.Control) -> list[auto.Control]:
        """展開中のコンボボックスのリスト項目を返す(ポップアップの位置に依存しない)。"""
        list_control = combo.ListControl(searchDepth=3)
        if not list_control.Exists(maxSearchSeconds=2):
            # ポップアップが別トップレベルウィンドウとして出る実装へのフォールバック
            list_control = auto.ListControl(searchDepth=3)
            if not list_control.Exists(maxSearchSeconds=2):
                raise AssertionError("部署コンボボックスのリストが見つかりません")
        return [
            c for c in list_control.GetChildren()
            if c.ControlTypeName == "ListItemControl"
        ]

    # --- 予算上限 ---

    def set_budget(self, text: str) -> None:
        self._control(BUDGET_LINE_EDIT).GetValuePattern().SetValue(text)

    def get_budget(self) -> str:
        return self._control(BUDGET_LINE_EDIT).GetValuePattern().Value

    # --- 発行ボタン ---

    def is_issue_enabled(self) -> bool:
        return bool(self._control(ISSUE_BUTTON).IsEnabled)

    def click_issue(self) -> None:
        self._control(ISSUE_BUTTON).GetInvokePattern().Invoke()

    # --- ステータス欄 ---

    def get_status(self) -> str:
        return self._control(STATUS_LABEL).Name

    def wait_status(self, predicate, timeout: float = DEFAULT_WAIT) -> str:
        """predicate(テキスト) が真になるまで待ち、最終的なテキストを返す。

        time.sleep は規約で禁止のため、存在しない objectName に対する
        Exists(maxSearchSeconds=0.2) を明示待機としてポーリング間隔を作る。
        """
        deadline = time.monotonic() + timeout
        while True:
            text = self.get_status()
            if predicate(text):
                return text
            if time.monotonic() >= deadline:
                return text
            self.window.Control(
                searchDepth=2, AutomationId=_POLL_DUMMY
            ).Exists(maxSearchSeconds=0.2)

    def wait_status_equals(self, expected: str, timeout: float = DEFAULT_WAIT) -> str:
        return self.wait_status(lambda t: t == expected, timeout)

    def wait_status_matches(self, pattern: str, timeout: float = DEFAULT_WAIT) -> str:
        regex = re.compile(pattern)
        return self.wait_status(lambda t: regex.match(t) is not None, timeout)
