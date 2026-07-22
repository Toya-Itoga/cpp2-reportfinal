# Gemba One

配管業・設備工事業向けのクラウド型作業指示・進捗管理サービス。

---

## 背景・課題

配管業や設備工事業の零細・中小企業では、現場への作業指示が口頭や紙ベースで行われることが多く、以下の課題があった。

- 社長（管理者）が各従業員の作業状況をリアルタイムに把握できない
- 従業員が自分の作業指示を手元で確認する手段がない
- タスクの完了報告に電話・LINE などの非公式手段を使い、記録が残らない

**Gemba One** は、これらの課題をシンプルな Web アプリで解決する。社長（admin）がブラウザからタスクを登録し、従業員（employee）がスマートフォンで自分のタスクを確認・完了報告できる。

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| バックエンド | Python 3.12 / FastAPI / Mangum（AWS Lambda 対応） |
| テンプレート | Jinja2（サーバーサイドレンダリング） |
| 部分更新 | HTMX |
| クライアント状態管理 | Alpine.js |
| データベース | Amazon DynamoDB |
| 認証 | JWT（有効期限 6 時間、HttpOnly Cookie） |
| パスワードハッシュ | bcrypt |
| デプロイ | GitHub Actions → AWS Lambda |

---

## 画面一覧と機能

### ログイン画面 `GET /login`

- **対象ロール**: 全員（公開）
- **機能**: JWT 認証によるログイン
- **主な操作**
  - ユーザー名・パスワードを入力してログイン
  - 認証成功時: admin → ダッシュボード、employee → タスク一覧へ遷移
  - 認証失敗時: フォーム上部にエラーメッセージを表示

---

### ダッシュボード画面 `GET /dashboard`

- **対象ロール**: admin のみ
- **機能**: 全従業員の今日の作業状況をリアルタイムで確認
- **主な表示内容**
  - KPI カード（本日の完了予定タスク数・完了済み数・未完了数）
  - 本日の進捗バー（完了＋作業中の積み上げ）
  - 従業員ごとの進捗カードグリッド（名前・タスク進捗状況）
- **主な操作**
  - 各従業員カードから、その従業員のタスク一覧へ遷移（`GET /tasks?assignee=<username>`）

---

### タスク一覧画面 `GET /tasks`

- **対象ロール**: admin・employee 共通
- **機能**: タスクの一覧表示・完了報告・追加・編集
- **主な表示内容**
  - タスクカード（作業内容 / 作業場所・担当者名・予定日・ステータスバッジ・操作ボタン）
  - ステータス別フィルタタブ（すべて / 未着手 / 作業中）
  - 完了済みタスクを表示する ▼ トグル
- **主な操作**
  - 「完了」ボタン → タスク完了確認ダイアログを開く（admin・employee 共通）
  - 「編集」ボタン → タスク追加・編集ダイアログを開く（admin のみ）
  - 「＋」FAB（右下固定）→ タスク追加ダイアログを開く（admin のみ）
- **表示制御**
  - admin: 全タスクを表示。`?assignee=` 指定時は担当者で絞り込み
  - employee: 自分のタスクのみ表示

---

### タスク追加・編集ダイアログ

- **対象ロール**: admin のみ
- **取得エンドポイント**: `GET /tasks/new`（新規）/ `GET /tasks/{id}/edit`（編集）
- **機能**: タスクの新規登録・既存タスクの編集
- **入力項目**: 担当者（select）/ 作業内容（text）/ 作業場所（text）/ 予定日（date）/ ステータス（select）
- **保存操作**: 追加 = `POST /tasks`、更新 = `PUT /tasks/{id}`。成功後にタスク一覧を再描画してダイアログを閉じる

---

### タスク完了確認ダイアログ

- **対象ロール**: admin・employee 共通
- **取得エンドポイント**: `GET /tasks/{id}/confirm`
- **機能**: タスク完了の確認
- **操作**: 確認ボタンで `POST /tasks/{id}/complete` を実行 → ステータスを完了に更新しタスク一覧を再描画

---

### 設定画面 `GET /settings`

- **対象ロール**: admin のみ
- **機能**: ユーザー（従業員）管理・自分自身のパスワード変更
- **主な操作**
  - 従業員追加: 「＋従業員を追加」→ `POST /settings/users`
  - 従業員編集: 「編集」→ `PUT /settings/users/{username}`（パスワード変更を含む）
  - 従業員削除: 「削除」→ 削除確認ダイアログ → `POST /settings/users/{username}/deactivate`（論理削除）
  - パスワード変更: 現在・新規・確認の 3 フィールド → `POST /settings/password`（自分自身のみ）

---

## ディレクトリ・ファイル構成

```
.
├── src/
│   ├── main.py                          # FastAPIアプリ本体・ルーター登録・Mangum設定
│   ├── database.py                      # DynamoDB接続設定
│   │
│   ├── routers/                         # ルータ層
│   │   ├── auth.py                      # 認証（ログイン・ログアウト）
│   │   ├── dashboard.py                 # ダッシュボード（adminのみ）
│   │   ├── tasks.py                     # タスク一覧・追加・編集・完了
│   │   └── settings.py                  # 設定・ユーザー管理・パスワード変更
│   │
│   ├── services/                        # サービス層
│   │   ├── auth_service.py              # JWT認証・bcryptパスワード検証
│   │   ├── task_service.py              # タスクのビジネスロジック
│   │   └── user_service.py              # ユーザー管理ロジック
│   │
│   ├── repositories/                    # リポジトリ層
│   │   ├── user_repository.py           # Userテーブル操作
│   │   └── task_repository.py           # Taskテーブル操作
│   │
│   ├── schema/                          # Pydanticスキーマ定義
│   │   ├── user.py                      # ユーザー関連スキーマ
│   │   └── task.py                      # タスク関連スキーマ
│   │
│   ├── utils/
│   │   └── datetime.py                  # 日付フォーマット・今日の日付取得・ISO8601変換
│   │
│   ├── templates/                       # Jinja2テンプレート
│   │   ├── base.html                    # 共通レイアウト
│   │   ├── layouts/
│   │   │   ├── app_shell.html           # サイドバー付きレイアウト（PC・admin向け）
│   │   │   └── mobile_shell.html        # モバイル用レイアウト
│   │   ├── pages/                       # フルページテンプレート
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── tasks.html
│   │   │   └── settings.html
│   │   ├── components/                  # 再利用コンポーネント（Jinja2 macro）
│   │   │   ├── sidebar.html
│   │   │   ├── topbar.html
│   │   │   ├── task_card.html
│   │   │   ├── status_badge.html
│   │   │   ├── employee_card.html
│   │   │   ├── kpi_card.html
│   │   │   ├── modal.html
│   │   │   └── empty_state.html
│   │   └── partials/                    # HTMXが差し替えるHTMLフラグメント
│   │       ├── task_list.html
│   │       ├── task_form.html
│   │       ├── task_confirm.html
│   │       ├── employee_list.html
│   │       ├── employee_form.html
│   │       └── employee_delete_confirm.html
│   │
│   └── static/                          # 静的ファイル
│       ├── css/
│       │   ├── tokens.css               # デザイントークン（カラー・タイポグラフィ）
│       │   ├── base.css                 # 共通スタイル
│       │   ├── login.css
│       │   ├── dashboard.css
│       │   ├── tasks.css
│       │   └── settings.css
│       └── js/
│           ├── login.js
│           ├── dashboard.js
│           ├── tasks.js
│           └── settings.js
│
├── tests/                               # テストコード
│   ├── test_auth_router.py
│   ├── test_auth_service.py
│   ├── test_exception_handlers.py
│   ├── test_task_service.py
│   ├── test_user_service.py
│   └── test_setup_local_db.py
│
├── config/                              # 設計ドキュメント（読み取り専用）
│   ├── requirements.md                  # 機能要件
│   ├── implement.md                     # 実装タスク
│   └── HANDOFF.md                       # フロントエンド実装仕様書
│
├── scripts/
│   └── setup_local_db.py               # ローカルDynamoDB初期化・データ投入
│
├── .github/workflows/
│   └── deploy.yml                       # GitHub Actions CI/CDパイプライン
│
├── requirements.txt
└── .venv/                               # 仮想環境
```

## ロール・権限

| 機能 | admin | employee |
|------|:-----:|:--------:|
| ダッシュボード閲覧 | ✓ | — |
| タスク一覧閲覧 | ✓（全員分） | ✓（自分のみ） |
| タスク追加・編集 | ✓ | — |
| タスク完了報告 | ✓ | ✓（自分のタスクのみ） |
| ユーザー管理 | ✓ | — |
| パスワード変更 | ✓（自分・従業員） | - |
