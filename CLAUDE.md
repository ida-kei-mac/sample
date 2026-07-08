\# プロジェクト概要

APIキー発行台帳(PySide6 + SQLite)。仕様書駆動でアプリとUI自動試験を作る練習プロジェクト。



\# ディレクトリ構成

\- docs/requirements.md : 要件仕様(EARS記法、REQ-ID付き)

\- docs/screen-spec.md  : 画面定義(コントロール/objectNameの対応表)

\- docs/test-design.md  : テスト設計書(ケースID、対応REQ-ID)

\- app/    : アプリ本体(python -m app で起動)

\- tests/  : pytest + uiautomation のUIテスト



\# アプリ実装規約

\- 全ウィジェット(MainWindow含む全階層)に objectName を設定する

\- `python -m app --test` 起動時: 一時ファイルSQLite使用、ウィンドウ位置サイズ固定(100,100 / 800x600)

\- 確認ダイアログはQMessageBox標準ボタンを使わず自作し、ボタンにobjectNameを付ける

\- 現在時刻は環境変数 APP\_FAKE\_NOW(ISO8601)があればそれを優先する



\# テスト実装規約

\- pytest + uiautomation。time.sleep禁止、Exists(maxSearchSeconds=N)等の明示待機のみ

\- クリックは実マウスのClick()ではなく GetInvokePattern().Invoke() 等のUIAパターン優先

\- 全テストに @pytest.mark.req("REQ-xxx") を付与

\- 失敗時スクリーンショットを artifacts/ に保存(conftest.pyフック)

\- テストの情報源は docs/ のみ。app/ のソースコードは読まない



\# 実行環境

\- Windowsネイティブ(PowerShell)。WSL不可。venv: .venv

