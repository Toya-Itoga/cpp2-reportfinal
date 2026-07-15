# implement.md

## コンテキスト
- CLAUDE.md
- config/requirements.md
- src/

## タスク
- config/requirements.mdとconfig/HANDOFF.mdのデータ構造を参照し、
- scripts/setup_local_db.pyを実装してください。

### 1. テーブル作成

以下の2テーブルをDynamoDB Localに作成する。
既に存在する場合はスキップ（delete→recreateはしない）。

**Userテーブル**
- テーブル名: 環境変数 USER_TABLE_NAME
- PK: username（String）
- SKなし

**Taskテーブル**
- テーブル名: 環境変数 TASK_TABLE_NAME
- PK: task_id（String）
- SK: assignee_id（String）
- BillingMode: PAY_PER_REQUEST

### 2. 初期データ投入

以下のダミーデータを投入する。
既に同じPKのアイテムが存在する場合はスキップ。

**Userテーブル**

| username | name | role | password |
|---|---|---|---|
| tanaka | 田中 社長 | admin | admin1234 |
| sato | 佐藤 健一 | employee | emp1234 |
| suzuki | 鈴木 大輔 | employee | emp1234 |
| takahashi | 高橋 修 | employee | emp1234 |

※passwordはbcryptでハッシュ化してpassword_hashとして保存すること
※user_idはuuid4で生成
※created_at はISO8601形式（datetime.utcnow().isoformat()）
※is_active = True

**Taskテーブル**

未完了タスク（PK: TASK#<task_id>）を5件：

| title | assignee | scheduled_date | status |
|---|---|---|---|
| 給湯器交換工事 | sato | 今日の日付 | in_progress |
| エアコン新設 / 3F事務所 | suzuki | 今日の日付 | pending |
| 排水管高圧洗浄 / 佐々木ビル | sato | 今日の日付 | pending |
| ボイラー点検 / 中村工場 | takahashi | 今日の日付 | in_progress |
| 水道メーター交換 / 田村邸 | suzuki | 明日の日付 | pending |

完了済みタスク（PK: DONE#<task_id>）を2件：

| title | assignee | scheduled_date | status |
|---|---|---|---|
| 水漏れ修理 / 田村マンション201 | takahashi | 今日の日付 | completed |
| トイレ詰まり修理 / 山田様邸 | sato | 昨日の日付 | completed |

※task_idはuuid4で生成
※assignee_nameはassignee（username）から名前を引いてセットすること
※created_by = tanaka
※created_at / updated_at はISO8601形式

### 3. 実行確認

スクリプト末尾に投入結果のサマリーを出力すること。
✅ Userテーブル作成済み
✅ Taskテーブル作成済み
✅ ユーザー 4件 投入完了
✅ タスク 7件 投入完了

## 注意事項
- DynamoDB LocalのエンドポイントはDYNAMODB_ENDPOINTから読むこと
- .envを読み込むこと（python-dotenv使用）
- 既存データを削除・上書きしないこと