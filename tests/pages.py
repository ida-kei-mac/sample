"""発行登録フォームのページオブジェクト。

ロケータ(objectName)は本モジュールに集約する(docs/screen-spec.md「コントロール一覧」準拠)。
テスト本体は objectName を直書きせず、必ず IssueFormPage 経由で操作する。

Qt(PySide6)は UIA の AutomationId を objectName そのものではなく
`QApplication.mainWindow.centralWidget.<objectName>` のようなドット区切りの
フルパスとして公開するため、探索は AutomationId の末尾一致(`.<objectName>`)で行う。
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


def _by_object_name(object_name: str):
    """AutomationId が `....<objectName>` で終わるコントロールに一致する比較関数。"""
    suffix = "." + object_name
    return lambda control, depth: control.AutomationId.endswith(suffix)


class IssueFormPage:
    """UIAutomation 経由で発行登録フォームを操作する。

    コントロールはメソッド呼び出しのたびに再探索し、常に最新状態を参照する。
    クリックは実マウスではなく UIA パターン(Invoke / Value / SelectionItem)で行う。
    """

    @property
    def window(self) -> auto.WindowControl:
        return auto.WindowControl(searchDepth=1, Name=WINDOW_TITLE)

    def wait_shown(self, timeout: float = 15.0) -> bool:
        return self.window.Exists(maxSearchSeconds=timeout)

    # --- コントロール探索(パターン取得メソッドを持つ型付きクラスで返す) ---

    def _user_name_edit(self) -> auto.EditControl:
        return self.window.EditControl(
            searchDepth=10, Compare=_by_object_name(USER_NAME_LINE_EDIT)
        )

    def _budget_edit(self) -> auto.EditControl:
        return self.window.EditControl(
            searchDepth=10, Compare=_by_object_name(BUDGET_LINE_EDIT)
        )

    def _department_combo(self) -> auto.ComboBoxControl:
        return self.window.ComboBoxControl(
            searchDepth=10, Compare=_by_object_name(DEPARTMENT_COMBO_BOX)
        )

    def _issue_button(self) -> auto.ButtonControl:
        return self.window.ButtonControl(
            searchDepth=10, Compare=_by_object_name(ISSUE_BUTTON)
        )

    def _status_label(self) -> auto.TextControl:
        return self.window.TextControl(
            searchDepth=10, Compare=_by_object_name(STATUS_LABEL)
        )

    # --- 利用者名 ---

    def set_user_name(self, text: str) -> None:
        self._user_name_edit().GetValuePattern().SetValue(text)

    def get_user_name(self) -> str:
        return self._user_name_edit().GetValuePattern().Value

    # --- 部署 ---

    def get_department(self) -> str:
        return self._department_combo().GetValuePattern().Value

    def get_department_items(self) -> list[str]:
        combo = self._department_combo()
        expand = combo.GetExpandCollapsePattern()
        expand.Expand()
        try:
            return [item.Name for item in self._department_list_items(combo)]
        finally:
            try:
                expand.Collapse()
            except Exception:
                pass

    def select_department(self, name: str) -> None:
        combo = self._department_combo()
        expand = combo.GetExpandCollapsePattern()
        expand.Expand()
        try:
            for item in self._department_list_items(combo):
                if item.Name == name:
                    # SelectionItemPattern.Select() はQtのQComboBoxに選択が反映されない
                    # (実測)ため、LegacyIAccessiblePattern の既定アクション(項目決定)を使う
                    item.GetLegacyIAccessiblePattern().DoDefaultAction()
                    self._wait_until(self.get_department, lambda v: v == name)
                    return
            raise AssertionError(f"部署コンボボックスに項目 {name!r} が見つかりません")
        finally:
            # 項目決定でポップアップが自動で閉じている場合があるため失敗は無視
            try:
                expand.Collapse()
            except Exception:
                pass

    @staticmethod
    def _department_list_items(combo: auto.ComboBoxControl) -> list[auto.Control]:
        """展開中のコンボボックスのリスト項目を返す。"""
        list_control = combo.ListControl(searchDepth=3)
        if not list_control.Exists(maxSearchSeconds=3):
            raise AssertionError("部署コンボボックスのリストが見つかりません")
        return [
            c for c in list_control.GetChildren()
            if c.ControlTypeName == "ListItemControl"
        ]

    # --- 予算上限 ---

    def set_budget(self, text: str) -> None:
        self._budget_edit().GetValuePattern().SetValue(text)

    def get_budget(self) -> str:
        return self._budget_edit().GetValuePattern().Value

    # --- 発行ボタン ---

    def is_issue_enabled(self) -> bool:
        return bool(self._issue_button().IsEnabled)

    def click_issue(self) -> None:
        self._issue_button().GetInvokePattern().Invoke()

    # --- ステータス欄 ---

    def get_status(self) -> str:
        return self._status_label().Name

    def _wait_until(self, getter, predicate, timeout: float = DEFAULT_WAIT):
        """getter() の値が predicate を満たすまで待ち、最終的な値を返す。

        time.sleep は規約で禁止のため、存在しない objectName に対する
        Exists(maxSearchSeconds=0.2) を明示待機としてポーリング間隔を作る。
        """
        deadline = time.monotonic() + timeout
        while True:
            value = getter()
            if predicate(value):
                return value
            if time.monotonic() >= deadline:
                return value
            self.window.Control(
                searchDepth=2, AutomationId=_POLL_DUMMY
            ).Exists(maxSearchSeconds=0.2)

    def wait_status(self, predicate, timeout: float = DEFAULT_WAIT) -> str:
        """ステータス欄のテキストが predicate を満たすまで待ち、最終的なテキストを返す。"""
        return self._wait_until(self.get_status, predicate, timeout)

    def wait_status_equals(self, expected: str, timeout: float = DEFAULT_WAIT) -> str:
        return self.wait_status(lambda t: t == expected, timeout)

    def wait_status_matches(self, pattern: str, timeout: float = DEFAULT_WAIT) -> str:
        regex = re.compile(pattern)
        return self.wait_status(lambda t: regex.match(t) is not None, timeout)
