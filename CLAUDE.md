# CLAUDE.md

## アーキテクチャ
- レイヤードアーキテクチャ

## レンダリング方式
- サーバーサイドレンダリング

## ディレクトリ・ファイル構成
- `.venv/`                - 仮想環境
- `src/main.py`           - アプリ本体
- `src/routers/`          - ルータ層
- `src/routers/auth.py`       - 認証ルータ
- `src/routers/dashboard.py`  - ダッシュボードルータ
- `src/routers/tasks.py`      - タスク一覧ルータ
- `src/services/`         - サービス層
- `src/routers/`
- `src/`
- `src/`
- `src/`
- `src/database.py`       - データベース接続設定定義
- `src/templates/`      - HTMLファイル
- `src/templates/dashboard.html`   - ダッシュボード画面HTML
- `src/templates/tasks`            - タスク一覧画面HTML
- `src/static/js/dashboard.js`     - ダッシュボード画面JavaScript
- `src/static/css/dashboard.css`   - ダッシュボード画面CSS
- `src/templates/components/`      - コンポーネントHTML
- `src/templates/task-/`
- `config/`               - 設定・ドキュメント
- `scripts/`              - 開発補助スクリプト
- `scripts/setup_local_db.py`
- `tests/`                - テストコード
- `.claude/commands/`     - コマンド
- `.claude/agents/`       - サブエージェント定義

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
- Python3.12
- FastAPI
- Jinja2
- uvicorn
- boto3
- Pydantic
- 
- 