# CLAUDE.md

## アーキテクチャ
- レイヤードアーキテクチャ

## レンダリング方式
- サーバーサイドレンダリング

## ディレクトリ・ファイル構成
- `.venv/`                          - 仮想環境
- `src/main.py`                     - FastAPIアプリ本体・ルーター登録・Mangum設定
- `src/database.py`                 - DynamoDB接続設定
- `src/routers/`                    - ルータ層
- `src/routers/auth.py`             - 認証（ログイン・ログアウト）
- `src/routers/dashboard.py`        - ダッシュボード（adminのみ）
- `src/routers/tasks.py`            - タスク一覧・追加・編集・完了
- `src/routers/settings.py`         - 設定・ユーザー管理・パスワード変更
- `src/services/`                   - サービス層
- `src/services/auth_service.py`    - JWT認証・bcryptパスワード検証
- `src/services/task_service.py`    - タスクのビジネスロジック
- `src/services/user_service.py`    - ユーザー管理ロジック
- `src/repositories/`              - リポジトリ層
- `src/repositories/user_repository.py`  - Userテーブル操作
- `src/repositories/task_repository.py`  - Taskテーブル操作
- `src/templates/`                  - Jinja2テンプレート
- `src/templates/base.html`         - 共通レイアウト
- `src/templates/layouts/`          - レイアウトテンプレート
- `src/templates/layouts/app_shell.html`    - サイドバー付きレイアウト
- `src/templates/layouts/mobile_shell.html` - モバイル用レイアウト
- `src/templates/pages/`            - HTMLテンプレート
- `src/templates/pages/login.html`
- `src/templates/pages/dashboard.html`
- `src/templates/pages/tasks.html`
- `src/templates/pages/settings.html`
- `src/templates/components/`       - コンポーネント
- `src/templates/components/sidebar.html`
- `src/templates/components/topbar.html`
- `src/templates/components/task_card.html`
- `src/templates/components/status_badge.html`
- `src/templates/components/employee_card.html`
- `src/templates/components/kpi_card.html`
- `src/templates/components/modal.html`
- `src/templates/components/empty_state.html`
- `src/templates/partials/`         - HTMXフラグメント
- `src/templates/partials/task_list.html`
- `src/templates/partials/task_form.html`
- `src/templates/partials/task_confirm.html`
- `src/templates/partials/employee_list.html`
- `src/templates/partials/employee_form.html`
- `src/templates/partials/employee_delete_confirm.html`
- `src/static/`                     - 静的ファイル
- `src/static/css/tokens.css`       - デザイントークン（カラー・タイポグラフィ）
- `src/static/css/base.css`         - 共通スタイル
- `src/static/css/login.css`        - ログイン画面CSS
- `src/static/css/dashboard.css`    - ダッシュボード画面CSS
- `src/static/css/tasks.css`        - タスク一覧画面CSS
- `src/static/css/settings.css`     - 設定画面CSS
- `src/static/js/login.js`          - ログイン画面JavaScript
- `src/static/js/dashboard.js`      - ダッシュボード画面JavaScript
- `src/static/js/tasks.js`          - タスク一覧画面JavaScript
- `src/static/js/settings.js`       - 設定画面JavaScript
- `src/schema/`                     - Pydanticスキーマ定義
- `src/schema/user.py`              - ユーザー関連スキーマ
- `src/schema/task.py`              - タスク関連スキーマ
- `src/utils/`                      - ユーティリティ関数
- `src/utils/datetime.py`           - 日付フォーマット・今日の日付取得・ISO8601変換
- `config/`                         - 設定・ドキュメント（読み取り専用）
- `config/requirements.md`          - 機能要件
- `config/implement.md`             - 実装タスク
- `config/HANDOFF.md`               - Claude Designハンドオフ仕様書
- `scripts/`                        - 開発補助スクリプト
- `scripts/setup_local_db.py`       - ローカルDynamoDB初期化・データ投入
- `tests/`                          - テストコード
- `.claude/commands/`               - カスタムスラッシュコマンド
- `.claude/agents/`                 - サブエージェント定義
- `.github/workflows/deploy.yml`    - GitHub Actions CI/CDパイプライン

## コーディング規約
- コメントを書くこと
- コードを機能単位のブロックで分割すること
- 生成するコードはsrc/に配置すること
- config/のファイルは読み取り専用とすること
- 機能を実装する際は必ずtests/にテストを作成すること
- HTMLのクラス名はBEM記法を遵守すること

## データベース
- 環境ごとにDBを分けること
- 本番環境とテスト環境のDBを分けること

## 禁止事項
- .envファイルの参照
- any型の乱用禁止
- ハードコードされたダミーデータを本番コードに含めないこと
- TODOコメントを残したまま実装を完了しないこと
- import文にsrc.プレフィックスを含めないこと

## Lambda対応
- 静的ファイルのパスはsrc/を含めないこと
  - StaticFiles(directory="static")
  - Jinja2Templates(directory="templates")
- import文はsrc.を含めないこと

## 更新ポリシー
- 機能追加時はREADME.mdを更新すること
- AIが間違った動作をしたらここに反映すること

## 技術スタック
- Python 3.12
- FastAPI
- uvicorn
- Jinja2
- HTMX
- Alpine.js
- boto3
- PyJWT
- bcrypt
- Mangum
- Pydantic