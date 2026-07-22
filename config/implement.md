# implement.md

## コンテキスト
- CLAUDE.md
- config/requirements.md（designs/Gemba One 画面デザイン.dc.html を正本として再生成したもの。
  旧モック・旧デザインファイルは廃止済み）
- config/HANDOFF.md
- src/

## 背景
- デザインファイルを1つに統一し、HANDOFF.mdを再生成した。
- 統一前は「モック」と「画面デザイン」の2ファイルを参照していたため、
  細部の差異（コンポーネントの見た目・余白・状態表示など）が
  実装に混在し、タスク一覧・設定画面のスタイル崩れの原因になっていた。
- 今回のタスクは、新しいHANDOFF.mdを唯一の正としてフロントエンド実装を
  総点検・再整合させること。

## タスク
- TemplateResponseの呼び出し形式を新形式に統一する

### 症状
- Lambda環境で /login にアクセスすると
  TypeError: unhashable type: 'dict' が発生する
  （ローカルでも過去に同様のエラーが発生し、
  当時はrequirements.txtのバージョン固定
  （starlette==0.41.3等）で一時的に回避していた）

### 根本原因
- src/routers/auth.py内のTemplateResponse呼び出しが
  古い形式（第一引数にテンプレート名、第二引数に
  {"request": request, ...}のdictを渡す形式）のままになっている
```python
  # 旧形式（問題あり）
  templates.TemplateResponse("pages/login.html", {"request": request})
```
- 新しいバージョンのStarlette/Jinja2ではこの形式が
  内部のテンプレートキャッシュキー生成で
  TypeError: unhashable type: 'dict' を引き起こす

### 修正内容
- src/配下の全てのルータファイル
  （routers/auth.py, dashboard.py, tasks.py, settings.py）で、
  TemplateResponseの呼び出しを全て新形式に統一する:
```python
  # 新形式（正しい）
  return templates.TemplateResponse(
      request=request,
      name="pages/login.html",
      context={}  # requestを含めない、追加のcontext変数のみ
  )
```
- 具体的には auth.py の3箇所を以下のように修正する:
  1. login_page関数:
```python
     return templates.TemplateResponse(
         request=request,
         name="pages/login.html",
         context={}
     )
```
  2. login関数（認証失敗時・HTMX）:
```python
     return templates.TemplateResponse(
         request=request,
         name="partials/login_form.html",
         context={"error": error_msg}
     )
```
  3. login関数（認証失敗時・通常）:
```python
     return templates.TemplateResponse(
         request=request,
         name="pages/login.html",
         context={"error": error_msg}
     )
```
- 他のルータファイル（dashboard.py, tasks.py, settings.py）に
  同様の旧形式のTemplateResponse呼び出しが残っていないか
  全て確認し、同じ新形式に統一すること

### requirements.txtのバージョン固定を解除
- 以前ローカルの問題を回避するために固定した
  starlette / jinja2 / fastapi のバージョン指定
  （requirements.txtにピン留めがあれば）を確認し、
  コード修正により不要になった場合は最新の安定版に
  戻してよい（Lambda側のレイヤーと揃える）

## 注意事項
- 修正後、ローカル（uvicorn）とLambda（本番）の
  両方で /login にアクセスし、正常にログイン画面が
  表示されることを確認すること
- 認証失敗時のエラーメッセージ表示、HTMX時の
  フォーム差し替えも正しく動作することを確認すること