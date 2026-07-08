# 画面定義書(screen-spec.md)

## 対象範囲

社内APIキー発行台帳アプリのうち、**ステップ1「発行登録フォーム+入力検証」** の単一画面(発行登録フォーム)を対象とする。
本書は [requirements.md](./requirements.md) の各REQ-IDが参照するコントロールの実体(種別・objectName・初期状態)を定義する。

## 画面イメージ(構成のみ・レイアウト詳細は規定しない)

```
+-----------------------------------------------+
| APIキー発行台帳                                  |  <- mainWindow (タイトル)
+-----------------------------------------------+
| 利用者名   [                              ]     |  <- userNameLabel / userNameLineEdit
| 部署       [開発部            v]                |  <- departmentLabel / departmentComboBox
| 予算上限   [                              ]     |  <- budgetLabel / budgetLineEdit
|                                                 |
|                       [        発行        ]    |  <- issueButton
|                                                 |
| (ステータス表示領域)                              |  <- statusLabel
+-----------------------------------------------+
```

## コントロール一覧

| コントロール名 | 種別 | objectName | 初期状態 |
|---|---|---|---|
| メインウィンドウ | QMainWindow | `mainWindow` | タイトル文字列「APIキー発行台帳」。`python -m app --test` 起動時はウィンドウ位置(100, 100)・サイズ800×600に固定。 |
| セントラルウィジェット | QWidget | `centralWidget` | mainWindowの中央領域に配置され、以下の全コントロールを内包する。 |
| 利用者名ラベル | QLabel | `userNameLabel` | テキスト「利用者名」を表示。 |
| 利用者名入力欄 | QLineEdit | `userNameLineEdit` | 空文字。活性(編集可能)。 |
| 部署ラベル | QLabel | `departmentLabel` | テキスト「部署」を表示。 |
| 部署コンボボックス | QComboBox | `departmentComboBox` | 項目は「開発部」「営業部」「管理部」の3件、この順序で登録。初期選択インデックスは0(「開発部」)。活性(選択変更可能)。項目の追加・削除ができない(編集不可)構成とする。 |
| 予算上限ラベル | QLabel | `budgetLabel` | テキスト「予算上限」を表示。 |
| 予算上限入力欄 | QLineEdit | `budgetLineEdit` | 空文字。活性(編集可能)。 |
| 発行ボタン | QPushButton | `issueButton` | テキスト「発行」。活性(クリック可能)。 |
| ステータス欄 | QLabel | `statusLabel` | 空文字。表示専用(編集不可)。発行成功時・検証NG時の文言をこの欄に表示する(文言は [requirements.md](./requirements.md) の「エラーメッセージ一覧」に定義)。 |

## objectName命名規則

- キャメルケース(先頭小文字)で統一する。
- 入力系コントロールは `<項目名>LineEdit` / `<項目名>ComboBox` とする。
- ラベルは `<項目名>Label` とする。
- ボタンは `<動作名>Button` とする。
- 上記に該当しないコンテナ・ウィンドウ類は役割が分かる名称(`mainWindow`、`centralWidget`)とする。

## コントロールとREQ-IDの対応(参考)

| objectName | 関連するREQ-ID |
|---|---|
| `userNameLineEdit` | REQ-001, REQ-007, REQ-008, REQ-010, REQ-011, REQ-015, REQ-019, REQ-020, REQ-022 |
| `departmentComboBox` | REQ-002, REQ-006, REQ-015, REQ-019, REQ-022 |
| `budgetLineEdit` | REQ-003, REQ-007, REQ-012, REQ-013, REQ-014, REQ-015, REQ-019, REQ-022 |
| `issueButton` | REQ-005, REQ-009 |
| `statusLabel` | REQ-004, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-021 |

※ 本表は参照の便宜のための一覧であり、正式なREQ-ID対応表(ケースID単位)は test-design.md で管理する。
