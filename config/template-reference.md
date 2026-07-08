# Claude Code テンプレートリファレンス

新しいチャットでこのファイルを共有することで
claude-code-templateの構成・使い方を素早く引き継げます。

---

## 1. テンプレートリポジトリ

**GitHub**: `https://github.com/Toya-Itoga/claude-code-template`
- Template repository機能が有効化されている
- 新規プロジェクト作成時は「Use this template」またはcloneで使用

### 新規プロジェクト作成手順
```bash
# 方法①: ディレクトリ直下にクローン（推奨）
mkdir ~/ProjectName
cd ~/ProjectName
git clone https://github.com/Toya-Itoga/claude-code-template.git .
git remote remove origin

# 方法②: ディレクトリ名を指定してクローン
git clone https://github.com/Toya-Itoga/claude-code-template.git project-name
cd project-name
git remote remove origin

# 確認
ls          # CLAUDE.mdが表示されればOK
git remote -v # 何も表示されなければ接続切断OK
```

---

## 2. ディレクトリ・ファイル構成

```
project-root/
├── CLAUDE.md                    # Claude Codeへの指示書（ルート直下固定）
├── requirements.txt             # Pythonライブラリ一覧（pip freeze > requirements.txt）
├── push.sh                      # git add/commit/push半自動化スクリプト
├── .env                         # 環境変数（.gitignoreで除外）
├── .gitignore                   # .venv/ .env __pycache__/ *.pyc *.db .DS_Store
│
├── config/                      # Claude Codeが読む設定・ドキュメント（読み取り専用）
│   ├── requirements.md          # 機能要件（What: 何を作るか）
│   ├── implement.md             # 実装タスク（How: どう作るか・Claude Codeへの指示）
│   ├── HANDOFF.md               # Claude Designからの画面仕様書
│   └── tips.md                  # 開発Tips・過去のエラー解決策
│
├── src/                         # アプリケーションコード（Claude Codeが生成・編集）
│                                # ※以下はFastAPI + Jinja2 + HTMX構成のサンプル
│                                # ※アーキテクチャ・技術スタック・アプリの要件によって構成は変わる
│                                # ※CLAUDE.mdのディレクトリ・ファイル構成セクションに実際の構成を定義すること
│   ├── main.py                  # FastAPIアプリ本体・ルーター登録・Mangum設定
│   ├── database.py              # DB接続設定（DynamoDB/SQLite）
│   ├── routers/                 # ルータ層（HTTPエンドポイント定義）
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   └── ...
│   ├── services/                # サービス層（ビジネスロジック）
│   │   ├── auth_service.py      # JWT認証・bcryptパスワード検証
│   │   └── ...
│   ├── repositories/            # リポジトリ層（DB操作）
│   │   ├── user_repository.py
│   │   └── ...
│   ├── templates/               # Jinja2テンプレート
│   │   ├── base.html            # 共通レイアウト
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── components/          # 共通コンポーネント（sidebar.html等）
│   │   └── partials/            # HTMXフラグメント（部分更新用）
│   ├── static/                  # 静的ファイル
│   │   ├── css/
│   │   └── js/
│   ├── models/                  # データモデル定義（SQLAlchemy等）
│   ├── schema/                  # Pydanticスキーマ定義
│   └── utils/                   # ユーティリティ関数
│
├── scripts/                     # 開発補助スクリプト
│   └── setup_local_db.py        # ローカルDynamoDB初期化・データ投入
│
├── tests/                       # テストコード
│
├── .claude/                     # Claude Code設定
│   ├── commands/                # カスタムスラッシュコマンド
│   │   ├── deploy.md            # /deploy コマンド
│   │   ├── task.md              # /task コマンド（implement.mdを読んで実装）
│   │   ├── start.md             # /start コマンド
│   │   └── review.md            # /review コマンド
│   ├── agents/                  # サブエージェント定義
│   └── settings.json            # Claude Code設定
│
└── .github/
    └── workflows/
        └── deploy.yml           # GitHub Actions CI/CDパイプライン
```

---

## 3. 各ファイルの役割と記述内容

### CLAUDE.md（ルート直下・必須）
**Claude Codeが起動時に自動で読む指示書**
35行以内を目安に簡潔に記述する。

```markdown
# CLAUDE.md

## アーキテクチャ
- レイヤードアーキテクチャ

## レンダリング方式
- サーバーサイドレンダリング

## ディレクトリ・ファイル構成
- `.venv/`         - 仮想環境
- `src/main.py`    - アプリ本体
- `src/routers/`   - ルータ層
- `src/services/`  - サービス層
- `src/repositories/` - リポジトリ層
- `src/templates/` - HTMLテンプレート
- `src/static/`    - 静的ファイル
- `src/utils/`     - ユーティリティ
- `src/database.py`- DB接続設定
- `config/`        - 設定・ドキュメント（読み取り専用）
- `scripts/`       - 開発補助スクリプト
- `tests/`         - テストコード
- `.claude/commands/` - カスタムコマンド

## コーディング規約
- コメントを書くこと
- コードを機能単位のブロックで分割すること
- 生成するコードはsrc/に配置すること
- config/のファイルは読み取り専用とすること
- 機能を実装する際は必ずtests/にテストを作成すること
- HTMLのクラス名はBEM記法を遵守すること
- REST原則を遵守すること

## 認証
- 認証はPyJWTを使用すること
- トークン有効期間は6時間とすること
- 全APIエンドポイントでトークン検証を行うこと
- FastAPIのDependsを使用して共通の認証ミドルウェアとして実装すること
- 認証処理はsrc/services/auth_service.pyに定義すること

## 環境変数
# ※以下はサンプル。使用するAWSサービス・技術スタック・アプリの要件によって増減する
# ※プロジェクト固有の環境変数はここに追記すること（例: S3_BUCKET_NAME・KNOWLEDGE_BASE_ID等）
- ENV: 実行環境（development / production）
- DYNAMODB_ENDPOINT: DynamoDBエンドポイント
- DYNAMODB_REGION: ap-northeast-1
- USER_TABLE_NAME: Userテーブル名
- JWT_SECRET_KEY: JWT署名キー
- JWT_ALGORITHM: HS256
- JWT_EXPIRE_HOURS: 6

## 禁止事項
- ハードコードされたダミーデータを本番コードに含めないこと
- TODOコメントを残したまま実装を完了しないこと
- import文にsrc.プレフィックスを含めないこと
- 静的ファイルのパスにsrc/を含めないこと
  - StaticFiles(directory="static")
  - Jinja2Templates(directory="templates")

## Lambda対応
- 静的ファイルのパスはsrc/を含めないこと
- import文はsrc.を含めないこと

## 更新ポリシー
- 機能追加時はREADME.mdを更新すること
- AIが間違った動作をしたらここに反映すること

## 技術スタック
- Python 3.12 / FastAPI / uvicorn / Jinja2
- HTMX / Alpine.js
- boto3 / PyJWT / bcrypt / Mangum
```

---

### config/requirements.md
**機能要件（What: 何を作るか）**

```markdown
# requirements.md

## アプリ概要
- アプリ名:
- 概要:

## デザイン
- Claude Designのハンドオフバンドルを参照すること
- ハンドオフ後のバックエンド繋ぎ込みはimplement.mdで別途指示すること

## 画面 / 基本機能

### 画面名（/path）
- 機能:
- 表示項目:
- 操作:
- 備考:

## 非機能要件
- パフォーマンス:
- セキュリティ:
- 対応デバイス:

## データ構造

### テーブル名
- PK: KEY#value
- SK: key_id
- attributes:
  - field: 説明

## ビジネスロジック
- （都度計算するもの・判定ロジック等）

## 制約条件
- （技術的制約・デプロイ先等）
```

---

### config/implement.md
**実装タスク（Claude Codeへの指示）**
`/task`コマンドで実行される。

```markdown
## コンテキスト
- CLAUDE.md
- config/requirements.md
- config/HANDOFF.md（Claude Designのハンドオフ）
- src/

## タスク

### [機能名]
- [具体的な実装指示]
- [ファイル名・関数名まで明示すること]

## 注意事項
- [禁止事項・制約・既存機能を壊さないこと]
```

---

### config/HANDOFF.md
**Claude Designが生成する画面仕様書**
Claude Designへの指示例:

```
このデザインをもとにClaude Code向けの実装仕様書（HANDOFF.md）を作成してください。

## 重要な前提
- フレームワーク: FastAPI + Jinja2 + HTMX + Alpine.js
- ReactやVue等のJSフレームワークは使用しない
- コンポーネントはJinja2テンプレート（.html）で実装する
- 状態管理はAlpine.jsのx-dataで実装する

## 記載してほしい内容
- 全体構成（レイアウト・カラーパレット・フォント・デザイントークン）
- 画面別仕様
- Jinja2テンプレート構成
- Alpine.jsの状態管理
- CSSクラス名（BEM記法）
- アニメーション仕様
- 権限による画面制御
```

---

### .claude/commands/ のカスタムコマンド

| コマンド | 説明 |
|---|---|
| `/task` | implement.mdを読んで実装を実行する |
| `/deploy` | デプロイ前チェックリストを確認してpush・デプロイ |
| `/review` | コードレビューを実行する |
| `/start` | プロジェクト開始時の初期確認を行う |

**deploy.mdのデプロイ前チェックリスト**
```markdown
## デプロイ前チェックリスト
- [ ] import文にsrc.プレフィックスが含まれていないか
- [ ] 静的ファイルのパスにsrc/が含まれていないか
- [ ] ハードコードされたダミーデータが残っていないか
- [ ] TODOコメントが残っていないか
- [ ] ローカルで動作確認済みか
- [ ] .envが.gitignoreに含まれているか
```

---

### push.sh（git半自動化）

```bash
#!/bin/bash
git add .
git commit -m "$1"
git push
```

**使い方**
```bash
sh scripts/push.sh "feat: ログイン機能を実装"
```

**Conventional Commitsプレフィックス**

| プレフィックス | 意味 |
|---|---|
| `feat:` | 新機能追加 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメント更新 |
| `refactor:` | リファクタリング |
| `chore:` | 雑務・設定変更 |
| `ci:` | CI/CD関連 |
| `test:` | テスト追加・修正 |
| `style:` | コードスタイル修正 |

---

### .github/workflows/deploy.yml（Lambda向け）

```yaml
name: Deploy to Lambda
on:
  workflow_dispatch:  # 手動実行
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: ZIPを作成
        run: |
          cd src
          zip -r ../function.zip .
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      - name: Lambdaを更新
        run: |
          aws lambda update-function-code \
            --function-name ${{ secrets.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://function.zip
```

**GitHub Secretsに登録するもの**
```
AWS_ACCESS_KEY_ID      ← IAMユーザーのアクセスキー
AWS_SECRET_ACCESS_KEY  ← IAMユーザーのシークレットキー
LAMBDA_FUNCTION_NAME   ← Lambda関数名
```

---

### scripts/setup_local_db.py
**ローカルDynamoDB初期化・データ投入スクリプト**

```python
# 役割: DynamoDB Localにテーブルを作成しダミーデータを投入する
# 実行: python scripts/setup_local_db.py
# 用途: Docker再起動でデータが消えた際に再投入する

import boto3

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:5434',
    region_name='ap-northeast-1',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

# テーブル作成・データ投入処理
```

---

## 4. 開発フロー

### AIDDパイプライン
```
Claude.ai（設計・壁打ち・エラー原因特定）
        ↓
Claude Design（画面デザイン・HANDOFF.md生成）
        ↓
Claude Code（実装・コーディング）
```

### 新機能追加の流れ
```
1. Claude.aiで設計・壁打ち
        ↓
2. config/requirements.mdに機能要件を追記
        ↓
3. Claude Designで画面イメージ作成 → HANDOFF.md生成
        ↓
4. config/implement.mdに実装タスクを記載
        ↓
5. Claude Codeで /task を実行
        ↓
6. ローカルで動作確認
        ↓
7. sh scripts/push.sh "feat: ○○機能を追加"
        ↓
8. GitHub ActionsでRun workflow → Lambdaデプロイ
```

### Claude Codeの起動
```bash
# プロジェクトディレクトリで
claude

# または特定ファイルを指定して起動
claude src/main.py
```

---

## 5. ローカル開発環境のセットアップ

### 手順
```bash
# 1. 仮想環境作成・有効化
python3.12 -m venv .venv
source .venv/bin/activate

# 2. ライブラリインストール
pip install -r requirements.txt

# 3. .envを作成（テンプレート）
cat > .env << 'ENVEOF'
ENV=development
DYNAMODB_ENDPOINT=http://localhost:5434
DYNAMODB_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
USER_TABLE_NAME=User
JWT_SECRET_KEY=dev-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=6
PORT=8000
ENVEOF

# 4. DynamoDB Local起動
docker run -d -p 5434:8000 amazon/dynamodb-local \
  -jar DynamoDBLocal.jar -inMemory

# 5. テーブル・データ初期化
python scripts/setup_local_db.py

# 6. 開発サーバー起動
python -m uvicorn src.main:app --reload --port 8000
```

**注意**: `uvicorn`ではなく`python -m uvicorn`を使う
→ 仮想環境のPythonで実行するため

---

## 6. CLAUDE.mdとrequirements.mdの役割分担

| ファイル | 役割 | 問いへの答え |
|---|---|---|
| `CLAUDE.md` | どう作るか・制約・規約 | **How** |
| `requirements.md` | 何を作るか・機能要件 | **What** |
| `implement.md` | 今回のタスク指示 | **Do this** |
| `HANDOFF.md` | 画面仕様・デザイン | **Look like this** |

---

## 7. .gitignoreの標準設定

```gitignore
.venv/
.env
__pycache__/
*.pyc
*.db
.DS_Store
*.zip
layer/
```
