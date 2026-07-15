# requirements.md

## アプリ概要
- アプリ名: Gemba One
- 概要: 零細・中小の配管業・設備工事業向けクラウド型作業指示・進捗管理サービス。
  社長（admin）がタスクを登録し、従業員（employee）はスマホで自分のタスクを確認・完了報告できる。

## デザイン
- Claude Designのハンドオフバンドルを参照すること
- ハンドオフ後のバックエンド繋ぎ込みはimplement.mdで別途指示すること

## 画面 / 基本機能

### ログイン画面
- 機能: JWT認証によるログイン
- 表示項目: ユーザー名・パスワード入力フォーム、ログインボタン
- 操作: ログインボタン押下で認証。成功時はロールに応じて遷移
- 備考: adminはダッシュボード、employeeはタスク一覧に遷移

### ダッシュボード画面（adminのみ）
- 機能: 全従業員の作業状況をリアルタイムで確認
- 表示項目: 従業員ごとのカード（名前・タスク進捗状況）、今日の完了予定タスク数・実績
- 操作: 各カードから従業員のタスク一覧に遷移可能
- 備考: 左側に固定メニューバー（ダッシュボード・タスク一覧・設定・ログアウト）

### タスク一覧画面（admin・employee共通）
- 機能: タスクの一覧表示・完了報告・追加・編集
- 表示項目: タスクカード（担当者・日時・ステータス）
- 操作: 「完了」ボタン→確認ダイアログ、「編集」ボタン→編集ダイアログ、「+」ボタン（adminのみ・右下固定）→タスク追加ダイアログ
- 備考: employeeは自分のタスクのみ表示。左側に固定メニューバー（タスク一覧・ログアウト）

### タスク追加・編集ダイアログ（adminのみ）
- 機能: タスクの新規登録・既存タスクの編集
- 表示項目: 担当者・作業内容・日時・ステータス入力フォーム
- 操作: 保存ボタンで登録・更新、キャンセルで閉じる
- 備考: 追加と編集でダイアログを流用

### タスク完了確認ダイアログ
- 機能: タスク完了の確認
- 表示項目: 「このタスクを完了しますか？」の確認メッセージ
- 操作: 確認ボタンで完了、キャンセルで閉じる
- 備考: admin・employee両方が操作可能

### 設定画面（adminのみ）
- 機能: ユーザー管理・パスワード変更
- 表示項目: 従業員一覧（追加・編集・削除）、パスワード変更フォーム
- 操作: 従業員の追加・編集・削除、パスワード変更
- 備考: 左側に固定メニューバー

## ビジネスロジック

### 認証・認可
- ログイン時にusername・passwordを受け取り、Userテーブルから該当ユーザーを取得
- bcryptでパスワードを検証し、成功時はJWT（有効期限6時間）を発行
- JWTのpayloadにはusername・role・nameを含める
- 全エンドポイントでJWTを検証し、未認証の場合はログイン画面にリダイレクト
- ロールに応じてアクセス制御：adminのみアクセス可能なエンドポイントはrole=adminを検証

### ログイン後の遷移
- role=admin → ダッシュボード画面（/dashboard）
- role=employee → タスク一覧画面（/tasks）

### タスク一覧のフィルタリング
- adminはTaskテーブルを全件スキャンして全タスクを表示
- employeeはSK=自分のusernameでQueryして自分のタスクのみ表示

### ダッシュボードの集計（adminのみ）
- 全タスクを取得し、scheduled_date=今日でフィルタリング
- ステータス別に集計して表示
  - 完了予定タスク数：scheduled_date=今日の全タスク数
  - 完了済み：status=completedのタスク数
  - 未完了：status=pending / in_progressのタスク数
- 従業員ごとにグルーピングしてカード形式で表示

### タスクのステータス管理
- タスク作成時のデフォルトステータスはpending
- 「完了」ボタン押下 → 確認ダイアログ → 確認で以下を実行：
  - 既存アイテム（TASK#<task_id>）を削除
  - DONE#<task_id>として同内容を再登録（status=completed・updated_at更新）
- ステータスの遷移：pending → in_progress → completed
- 完了済みタスクは編集・完了操作不可

### ユーザー管理（adminのみ）
- 従業員の追加：username・name・role=employeeで新規ユーザーを作成
- 初期パスワードはadminが設定し、従業員に別途通知
- 従業員の削除：is_active=falseに更新（物理削除はしない）

## 非機能要件
- パフォーマンス: 画面表示3秒以内
- セキュリティ: JWT認証、ロールベースのアクセス制御（admin / employee）
- 対応デバイス: スマートフォン（iOS・Android）・PC（Chrome最新版）

## データ構造

### Userテーブル
- PK: username
- attributes:
  - user_id: UUID
  - password_hash: bcryptハッシュ化済みパスワード
  - role: admin / employee
  - name: 表示名
  - created_at: 作成日時（ISO8601）
  - is_active: 有効フラグ（true / false）

### Taskテーブル
- PK: TASK#<task_id>（未完了）/ DONE#<task_id>（完了済） ※完了実行時にPKをTASK# → DONE#に付け替える（delete → put）
- SK: assignee_id（担当者のusername）
- attributes:
  - title: 作業内容
  - assignee_name: 担当者の表示名
  - scheduled_date: 作業予定日（YYYY-MM-DD）
  - status: pending / in_progress / completed
  - created_by: 作成者のusername
  - created_at: 作成日時（ISO8601）
  - updated_at: 更新日時（ISO8601）

## 制約条件
- バックエンド: AWS Lambda（FastAPI / SSR）
- データベース: Amazon DynamoDB
- デプロイ: GitHub Actions経由でLambdaに自動デプロイ
- 画像アップロード機能は将来対応予定（Amazon S3）