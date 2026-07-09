# Windows GUIテスト自動化ツールの比較検討

本プロジェクト(PySide6アプリ + pytest + uiautomation)での経験をもとに、
Windows デスクトップアプリのUIテスト自動化に使えるツールと、
アプリの実装言語・フレームワークごとの推奨を整理する。

## 前提知識: 方式は大きく3つ

| 方式 | 仕組み | 代表ツール |
|---|---|---|
| アクセシビリティAPI経由(UIA) | OSの UI Automation API を通じ、実プロセスのウィンドウを外部から操作する。実装言語を問わない | uiautomation, pywinauto, FlaUI, WinAppDriver |
| アプリ内部フック | テストコードがアプリと同一プロセス(または専用フック)でウィジェットを直接操作する。フレームワーク専用 | pytest-qt, Qt Test, Squish |
| 画像認識 | 画面のスクリーンショットに対する画像マッチングで操作位置を決める。アプリの内部構造に依存しない | SikuliX, AutoHotkey(座標/画像) |

UIA系はどのツールを選んでも「アプリのフレームワークがアクセシビリティ層に何をどう公開するか」
という癖の影響を受ける。本プロジェクトで遭遇した例:

- Qt は objectName をそのまま AutomationId にせず `QApplication.mainWindow.centralWidget.<objectName>` というドット区切りフルパスで公開する
- QComboBox の項目選択は `SelectionItemPattern.Select()` では反映されず、`LegacyIAccessiblePattern.DoDefaultAction()` が必要だった

## ツール比較

| ツール | 言語 / 方式 | 利点 | 留意点 |
|---|---|---|---|
| **uiautomation**(今回採用) | Python / UIA | 軽量でUIAパターンを素直に扱える。依存が少ない | 低レベルで、待機やロケータ照合(末尾一致等)は自作が必要 |
| **pywinauto** | Python / UIA(+Win32) | 高レベルAPI(`app.window(auto_id=...)`)で記述量が少ない。`wait("ready")` 等の組み込み待機。`win32` バックエンドでレガシーアプリにも対応。情報が豊富 | UIA由来のフレームワークの癖からは逃れられない |
| **pytest-qt** | Python / Qt内部 | 同一プロセスでウィジェットを直接操作するため圧倒的に高速(実測69秒のスイートが数秒レベル相当)。offscreen起動でヘッドレスCI可。objectNameでの特定もそのまま可能 | 真のE2E(アクセシビリティ層・実ウィンドウ経由)の検証にはならない。Qt専用 |
| **FlaUI** | C#/.NET / UIA | UIA3の忠実なラッパーで活発にメンテ。型安全にパターン操作でき、情報も豊富 | テストコードがC#になる |
| **WinAppDriver + Appium** | 各言語 / WebDriverプロトコル | Selenium/Appiumの知識・資産(Page Object、Grid、各言語クライアント)を流用可能。Webとデスクトップでテスト基盤を統一しやすい | Microsoftのメンテナンスがほぼ停止している |
| **Squish**(商用) | 専用スクリプト / Qtフック | Qtオブジェクトを直接認識するため、アクセシビリティ層の癖問題が起きにくい。記録再生・レポート機能あり | 有償。ベンダーロックイン |
| **SikuliX 等(画像ベース)** | 画像認識 | objectNameもアクセシビリティ公開もないレガシーアプリで最後の手段になる | 解像度・テーマ・フォント変更に脆い。文言の完全一致検証に不向き |

## 本プロジェクトでの使い分け指針

- 規約(実マウス不使用・UIAパターン優先・objectName特定)を保ったまま乗り換えるなら **pywinauto** が最有力。今回自作した「AutomationId末尾一致」「明示待機ヘルパ」相当が組み込みで揃う。
- **pytest-qt を別レイヤーとして併用**する価値が高い。入力検証の網羅(境界値など)は pytest-qt で高速に回し、「UIAツリーへの公開」「実ウィンドウでの一連操作」だけをUIA系E2Eで確認する2段構えにすると、実行時間と信頼性のバランスが良い。

## アプリが C# / C++ 製だった場合のツール選定

UIAはOSのAPIなので、**テスト側ツールの選択肢自体はアプリの実装言語に依存しない**
(C#製アプリをPython+pywinautoでテストすることも普通にできる)。
変わるのは「アプリ側がどれだけ素直にUIAへ情報を公開するか」と「チームに合う言語」である。

### C#(WPF / WinForms / WinUI 3)の場合

| 推奨 | 理由 |
|---|---|
| **FlaUI**(第一候補) | アプリとテストを同じC#/.NETで書け、ビルド・CIも統一できる。WPFは `x:Name` / `AutomationProperties.AutomationId` がそのままUIAのAutomationIdになるため、Qtのようなフルパス化の癖がなくロケータが素直 |
| Appium + WinAppDriver | Webテスト資産(Selenium)を持つチームが基盤を統一したい場合 |
| pywinauto / uiautomation | テストチームがPython主体の場合。C#アプリでも問題なく動く |

補足: WPF/WinFormsはMicrosoft純正フレームワークだけあってUIAへの公開品質が高く、
標準コントロールなら `SelectionItemPattern` 等が仕様どおり機能することが多い。
なお過去の定番だった Coded UI Test と White は開発終了のため新規採用は避ける。

### C++ の場合(フレームワークで分岐)

| アプリの構成 | 推奨 | 理由 |
|---|---|---|
| Qt / C++ | **Squish**(予算があれば)または pywinauto/uiautomation | SquishはQtオブジェクトを直接認識し、本プロジェクトで遭遇したUIA公開の癖を回避できる。無償でやるならPySide6と同じ知見(AutomationIdフルパス、LegacyIAccessible等)がそのまま通用する |
| Win32 API / MFC(レガシー) | **pywinauto(win32バックエンド)** | 古いアプリはUIA対応が不完全なことが多く、Win32 API(ハンドル・コントロールID)ベースの操作が確実。pywinautoは `backend="win32"` と `backend="uia"` を切り替えられるため両対応できる |
| 独自描画UI(ゲーム、組込み風UIなど) | 画像ベース(SikuliX等)+ 可能ならアプリに専用テストAPIを追加 | OSにコントロールとして公開されないため外部からの構造的操作が不可能。長期的にはアプリ側へのアクセシビリティ実装かテスト用フックの追加が本筋 |

### 選定の考え方(まとめ)

1. **アプリのフレームワーク**が最初の分岐: 専用フック(pytest-qt / Squish)が使えるなら、アクセシビリティ層の癖を丸ごと回避できる。
2. 次に**チームの言語**: テスト資産・メンバーのスキルに合わせる(.NETチームならFlaUI、Pythonチームならpywinautoやuiautomation)。
3. E2Eの網羅テストは遅く脆くなりがちなので、**ロジック検証は内部フックの高速テスト、公開・結合の確認だけE2E**という2段構えを基本形とする。
