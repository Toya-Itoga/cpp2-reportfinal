# commands.md

## Claude Code
- 起動: `claude`
- 再ログイン: `/login`
- 終了: `/exit`
- 直前の操作を取り消す: `/undo`

## Git初期設定

### テンプレートから始める場合
- リモート削除: `git remote remove origin`
- リモート紐付け: `git remote add origin https://github.com/ユーザー名/新しいリポジトリ名.git`
- 最初のpush: `git push -u origin main`

### ゼロから始める場合
- Gitの初期化: `git init`
- リモートの紐付け: `git remote add origin https://github.com/ユーザー名/リポジトリ名.git`
- `git add .`
- `git commit -m "first commit"`
- `git branch -M main`
- `git push -u origin main`

## Git関係
- プッシュ: `sh scripts/push.sh ""`
- 変更履歴確認: `git log --oneline`
- 直前のコミットに戻す: `git revert HEAD`

## サーバー起動
- 開発サーバー(uvicorn): `python -m uvicorn src.main:app --reload`

## 仮想環境
- 作成: `python3.12 -m venv .venv`
- 有効化: `source .venv/bin/activate`

## DynamoDB Local確認
- テーブル一覧:
  AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy \
  aws dynamodb list-tables --endpoint-url http://localhost:5434 --region ap-northeast-1

- テーブルスキャン:
  AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy \
  aws dynamodb scan --table-name テーブル名 --endpoint-url http://localhost:5434 --region ap-northeast-1

- データ追加:
  AWS_ACCESS_KEY_ID=dummy AWS_SECRET_ACCESS_KEY=dummy \
  aws dynamodb put-item --table-name テーブル名 --endpoint-url http://localhost:5434 --region ap-northeast-1 --item '{}'

## パスワードハッシュ化
- python -c "import bcrypt; print(bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode())"

## Lambdaレイヤー作成
- mkdir -p layer/python
- pip install -r requirements.txt -t ./layer/python --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12
- cd layer && zip -r ../layer.zip . && cd ..