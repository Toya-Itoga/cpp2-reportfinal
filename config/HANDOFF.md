# Gemba One 実装ハンドオフ仕様書（HANDOFF.md）

配管・設備工事業向け作業指示・進捗管理サービス「**Gemba One**」のフロントエンド実装仕様。
デザインボード（`Gemba One 画面デザイン.dc.html`）に対応する、Claude Code 向けの実装指示書です。

> **バックエンド繋ぎ込み（認証ロジック・DynamoDB アクセス等）は本書では扱いません。`implement.md` を別途参照してください。** 本書は「画面 / テンプレート / 状態 / スタイル / アニメーション / 権限制御」の実装仕様に限定します。

> **インタラクティブモック**: `Gemba One モック.dc.html` に、画面遷移・ダイアログ開閉・ボタン操作・アニメーションを実際に操作できるモックを用意しています。挙動（スピナー表示タイミング、サイドバー固定、ダイアログ演出、ホバー/押下アニメーション）の一次リファレンスとして参照してください。

---

## 0. 技術スタック・前提

| 項目 | 内容 |
| --- | --- |
| サーバー | FastAPI（AWS Lambda / SSR） |
| テンプレート | Jinja2（`.html`） |
| 部分更新 | HTMX（`hx-get` / `hx-post` / `hx-target` / `hx-swap`） |
| クライアント状態 | Alpine.js（`x-data` / `x-show` / `x-on`） |
| DB | Amazon DynamoDB |
| 認証 | JWT（有効期限6時間、HttpOnly Cookie 推奨） |

### 実装方針
- **React / Vue 等の JS フレームワークは使用しない。**
- 画面遷移・一覧再描画・ダイアログ内容取得は **HTMX** でサーバーから HTML 断片を取得して差し込む。
- モーダルの開閉・フィルタタブの選択状態・パスワード表示切替など **クライアント完結の UI 状態は Alpine.js の `x-data`** で持つ。
- コンポーネントは Jinja2 の `{% include %}` / `{% macro %}` で再利用する。
- CSS クラスは **BEM 記法**（`block__element--modifier`）で命名する。

---

## 1. 全体構成

### 1.1 カラーパレット（CSS カスタムプロパティ）

`static/css/tokens.css` に定義し、全画面で参照する。

```css
:root {
  /* Brand / Primary */
  --color-primary:        #2563EB;  /* プライマリ（ボタン・アクティブ・リンク） */
  --color-primary-dark:   #1B4CD6;  /* ホバー・押下 */
  --color-primary-light:  #ECF2FE;  /* 選択背景・アバター背景 */
  --color-primary-tint:   #E7EFFE;  /* バッジ背景（作業中） */

  /* Navy（サイドバー） */
  --color-navy:           #111A2E;
  --color-navy-soft:      #1B2740;

  /* Ink（テキスト） */
  --color-ink:            #16203A;  /* 見出し・本文 */
  --color-ink-2:          #5A6784;  /* サブテキスト */
  --color-ink-3:          #8A96AC;  /* キャプション・プレースホルダ */

  /* Surface / BG */
  --color-bg:             #F4F6FA;  /* アプリ背景 */
  --color-surface:        #FFFFFF;  /* カード・パネル */
  --color-border:         #E4E9F2;  /* 罫線・枠線 */
  --color-border-soft:    #EEF1F6;  /* 淡い区切り線 */

  /* Status */
  --color-pending:        #E08A00;  --color-pending-ink:   #B26A00;  --color-pending-bg:   #FBF0DC;
  --color-progress:       #2563EB;  --color-progress-ink:  #1B4CD6;  --color-progress-bg:  #E7EFFE;
  --color-completed:      #1FA25E;  --color-completed-ink: #167C4A;  --color-completed-bg: #E4F4EB;

  /* Danger */
  --color-danger:         #D14343;

  /* Radius */
  --radius-card:   16px;
  --radius-field:  10px;
  --radius-pill:   999px;

  /* Shadow */
  --shadow-card:   0 1px 3px rgba(16,26,54,.06);
  --shadow-pop:    0 24px 60px rgba(0,0,0,.28);
  --shadow-btn:    0 4px 12px rgba(37,99,235,.30);

  /* Spacing 基準 = 4px */
}
```

### 1.2 タイポグラフィ

- フォント: **Noto Sans JP**（Google Fonts）。数値は `Roboto Mono`（`.u-mono`）で表示すると視認性が上がる。
- `<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">`

| 用途 | サイズ / ウェイト | 例 |
| --- | --- | --- |
| ページ見出し h1 | 30px / 900 | 「作業指示…」 |
| セクション h2 | 19–20px / 900 | 「ダッシュボード」 |
| カード見出し h3 | 15px / 700 | タスク名 |
| 本文 | 14px / 400 | — |
| キャプション | 12px / 500 | 補足・ラベル |

- スマホのタッチ対象は **最小 44px** を確保（完了報告ボタン等）。
- ステータスに依存しない情報伝達（色 + テキスト + アイコンの三重表現）を守る。

### 1.3 レイアウト

- **PC（admin 中心）**: 左固定サイドバー（幅 220px, `--color-navy`）+ 右メインカラム。メイン上部にヘッダーバー（高さ 70px, `--color-surface`）。
- **スマホ（employee 中心）**: サイドバーは非表示。上部に固定ヘッダー（ロゴ + アバター）、下にタスクカードの縦スタック。
- ブレークポイント: `768px` 未満をモバイル扱い。サイドバーは `md` 以上で表示、モバイルではヘッダー内メニュー or ボトム最小構成。
- **サイドバーは固定コンポーネントとして扱う**: `app_shell.html` に一度だけレンダリングし、画面遷移（ダッシュボード⇄タスク一覧⇄設定）では **再取得・再マウントしない**。HTMX の `hx-boost` 対象は右側のメインコンテンツ領域（例: `<div id="main-content">`）のみとし、ナビ項目クリックは `hx-get="/dashboard"` `hx-target="#main-content"` `hx-push-url="true"` のように右ペインだけを差し替える。サイドバー自体の DOM（ロゴ・ナビ項目・ユーザー情報・ログアウト）は差し替え対象に含めない。
- サイドバーのナビ項目は現在アクティブな画面を **背景色（`--color-primary`）+ 左端インジケーターバー（幅4px・白・`border-radius: 0 4px 4px 0`）+ シャドウ** で強調し、どの画面を開いているか視覚的に明確にする。

---

## 2. Jinja2 テンプレート構成

```
templates/
├── base.html                     # <html> 骨格・<head>・トークン読込・{% block %}
├── layouts/
│   ├── app_shell.html            # サイドバー付きレイアウト（admin/PC）
│   └── mobile_shell.html         # モバイル用ヘッダーレイアウト（employee）
├── components/
│   ├── sidebar.html              # 左固定メニュー（macro: sidebar(role, active)）
│   ├── topbar.html               # メインヘッダー（title, user）
│   ├── task_card.html            # タスクカード（macro: task_card(task, role)）
│   ├── task_row.html             # タスク行（テーブル型・2b案）
│   ├── status_badge.html         # ステータスバッジ（macro: status_badge(status)）
│   ├── employee_card.html        # 従業員進捗カード（ダッシュボード）
│   ├── kpi_card.html             # KPI カード（macro: kpi_card(label, value, variant)）
│   ├── modal.html                # モーダル外枠（macro: modal(title)）
│   └── empty_state.html          # 0件表示
├── pages/
│   ├── login.html
│   ├── dashboard.html            # admin のみ
│   ├── tasks.html                # admin/employee 共通
│   └── settings.html             # admin のみ
└── partials/                     # HTMX が返す HTML 断片
    ├── task_list.html            # タスク一覧本体（フィルタ後の再描画対象）
    ├── task_form.html            # 追加・編集ダイアログ中身（流用）
    ├── task_confirm.html         # 完了確認ダイアログ中身
    ├── employee_list.html        # 従業員管理テーブル（設定）
    └── employee_form.html        # 従業員 追加・編集ダイアログ
```

### 2.1 マクロ設計例

```jinja2
{# components/status_badge.html #}
{% macro status_badge(status) %}
  {% set map = {
    'pending':     ('未着手', 'pending'),
    'in_progress': ('作業中', 'progress'),
    'completed':   ('完了',   'completed')
  } %}
  {% set label, mod = map[status] %}
  <span class="status-badge status-badge--{{ mod }}">
    <span class="status-badge__dot"></span>{{ label }}
  </span>
{% endmacro %}
```

```jinja2
{# components/task_card.html #}
{% macro task_card(task, role) %}
  <article class="task-card task-card--{{ task.status_variant }}
                  {% if task.status == 'completed' %}task-card--done{% endif %}">
    <header class="task-card__head">
      <h3 class="task-card__title">{{ task.title }}</h3>
      {{ status_badge(task.status) }}
    </header>
    <div class="task-card__meta">
      <span class="task-card__assignee">
        <span class="avatar avatar--sm">{{ task.assignee_name[0] }}</span>{{ task.assignee_name }}
      </span>
      <time class="u-mono">{{ task.scheduled_date }}</time>
    </div>
    <footer class="task-card__actions">
      {% if task.status != 'completed' %}
        <button class="btn btn--complete"
                hx-get="/tasks/{{ task.task_id }}/confirm"
                hx-target="#modal-root" hx-swap="innerHTML">完了</button>
        {% if role == 'admin' %}
          <button class="btn btn--ghost"
                  hx-get="/tasks/{{ task.task_id }}/edit"
                  hx-target="#modal-root" hx-swap="innerHTML">編集</button>
        {% endif %}
      {% else %}
        <span class="task-card__done-label">完了済み</span>
      {% endif %}
    </footer>
  </article>
{% endmacro %}
```

> `task.status_variant` はサーバー側で `pending→pending / in_progress→progress / completed→completed` にマップした値を渡す（バッジ・左ボーダー色に使用）。

---

## 3. 画面別仕様

### 3.1 ログイン画面 `GET /login`

- **ルート**: `GET /login`（フォーム表示）, `POST /login`（認証）。
- **表示項目**: ユーザー名 / パスワード入力、ログインボタン。左に navy のブランドパネル（PC のみ）。
- **操作**: ログイン押下で `POST /login`。成功時 `role` に応じてリダイレクト。
  - `admin → 302 /dashboard`
  - `employee → 302 /tasks`
- **失敗時**: フォーム上部に `.alert--error` を表示（`hx-post` + `hx-target="#login-form"` で断片差し替え、または通常 POST で再レンダリング）。
- **未認証で保護ページにアクセス**: `302 /login` にリダイレクト。
- **HTMX 例**:
  ```html
  <form class="login-form" hx-post="/login" hx-target="#login-form" hx-swap="outerHTML" id="login-form">…</form>
  ```

### 3.2 ダッシュボード画面 `GET /dashboard`（admin のみ）

- **権限**: `role == admin` のみ。employee は `403` または `/tasks` へリダイレクト。
- **集計（サーバー側で算出しコンテキスト投入）**:
  - `today_total` = `scheduled_date == 今日` の全タスク数（＝完了予定数）
  - `completed_count` = うち `status == completed`
  - `pending_count` = うち `status in (pending, in_progress)`
  - `by_employee` = 従業員ごとに `{name, username, done, progress, pending}` を集計
- **レイアウト（採用: 1a 案 = KPI カード + 従業員カードグリッド）**:
  1. KPI カード3枚（本日の完了予定 / 完了済み / 未完了）
  2. 本日の進捗バー（完了 + 作業中の積み上げ）
  3. 従業員進捗カードのグリッド（`repeat(3, 1fr)`、各カードから該当従業員のタスク一覧へ遷移）
- **遷移**: 各従業員カード → `GET /tasks?assignee=<username>`。

### 3.3 タスク一覧画面 `GET /tasks`（admin / employee 共通）

- **フィルタリング（サーバー側）**:
  - `admin`: Task テーブルを全件スキャンして全タスク表示。`?assignee=` 指定時は絞り込み。
  - `employee`: `SK == 自分の username` で Query し、自分のタスクのみ表示。
- **項目**: タスクは「**作業内容**（`work`）」と「**場所**（`location`）」を別項目として保持する（例: 作業内容＝「給湯器交換工事」、場所＝「山田様邸」）。カード表示は従来どおり「作業内容 ／ 場所」の1行で結合して見せる（`title = work + ' ／ ' + location` をサーバー側もしくはテンプレートで生成）。
- **表示（採用: 2a 案 = タスクカードグリッドに確定）**:
  - タスクカード: 作業内容／場所・担当者名（アイコンなし）・予定日・ステータスバッジ・操作ボタン。
  - ステータス別の左ボーダー色（pending=橙 / in_progress=青 / completed=緑）。
- **デフォルト表示・フィルタ**:
  - **初期表示では完了済みタスクを表示しない**。一覧は `status in (pending, in_progress)` のタスクのみを表示する。
  - フィルタタブは「**すべて／未着手／作業中**」の3つのみ（「完了」タブは廃止）。「すべて」は完了済みを除いた全件を指す。
  - 一覧の最下部に「**完了済みタスクを表示する ▼**」ボタンを配置。押下すると、薄いグレーの背景セクション（`--color-bg` や `#EEF1F6` 相当）内に完了済みタスクをカードグリッドで展開表示する。再度押下で折りたたみ、ボタン文言は「**完了済みタスクを隠す ▲**」に切り替わる（開閉状態は Alpine `x-data` のローカル状態、`GET /tasks?include_completed=true` を遅延取得する実装でも可）。
  - 完了済みカードのデザインは維持: 打ち消し線（`text-decoration: line-through`）+ `opacity: .72`。編集・完了ボタンは非表示のまま「完了済み」ラベルのみ表示。
- **操作**:
  - **admin の「編集」ボタン押下 → タスク追加・編集ダイアログ（`partials/task_form.html`）を開く**（`GET /tasks/{id}/edit` を `#modal-root` に読み込み）。フォームの入力項目も「作業内容」「場所」を別フィールドとして持つ（3.4 参照）。
  - **employee の「完了報告」ボタン押下 → タスク完了確認ダイアログ（`partials/task_confirm.html`）を開く**（`GET /tasks/{id}/confirm` を `#modal-root` に読み込み）。admin の「完了」ボタンも同じ完了確認ダイアログを開く。
  - 右下固定「**+**」FAB → 追加ダイアログ（`GET /tasks/new`、**admin のみ**表示）。
  - **FAB は `position: fixed`（`right/bottom` 固定）でスクロールしても右下に留まる。** モバイルではセーフエリアを考慮（`bottom: calc(20px + env(safe-area-inset-bottom))`）。ホバー時は `translateY(-3px) scale(1.05)` ＋シャドウ拡大で浮き上がる（回転アニメーションは使用しない）。押下時は暗い背景色＋沈み込み（`translateY(0) scale(.95)`）。

### 3.4 タスク追加・編集ダイアログ（admin のみ・流用）

- **取得**: `GET /tasks/new`（空フォーム）/ `GET /tasks/{id}/edit`（値入り）。同一 `partials/task_form.html` を流用し、`action` と見出しだけ切替。
- **入力項目**: 担当者（select・active な employee 一覧）/ **作業内容（text）と場所（text）を別フィールドとして入力** / 予定日（date）/ ステータス（select）。
- **保存**: 追加=`POST /tasks`、更新=`PUT /tasks/{id}`（HTMX は `hx-post` + `_method` か `hx-put`）。成功後は `#task-list` を再描画し、モーダルを閉じる（`HX-Trigger: close-modal` レスポンスヘッダ or Alpine イベント）。
- **キャンセル**: モーダルを閉じるのみ（サーバー通信なし）。
- **デフォルト**: 新規作成時 `status = pending`。

### 3.5 タスク完了確認ダイアログ（admin / employee 共通）

- **取得**: `GET /tasks/{id}/confirm` → `partials/task_confirm.html`。
- **表示**: 「このタスクを完了しますか？」+ 対象タスク名 +「完了後は編集・取り消し不可」の注意。
- **確認**: `POST /tasks/{id}/complete` → `status = completed` に更新 → `#task-list` 再描画・モーダルクローズ。
- **キャンセル**: 閉じるのみ。

### 3.6 設定画面 `GET /settings`（admin のみ）

- **従業員管理**: 一覧（氏名 / username / role / 操作）。**削除済み（is_active=false）ユーザーは一覧に表示しない。**
  - **追加**: 「**+従業員を追加**」ボタン押下 → 従業員追加ダイアログ（`GET /settings/users/new` → `partials/employee_form.html`）→ `POST /settings/users`（`role=employee` 固定。**このダイアログで admin が本パスワードを直接設定する**。初期パスワードではなく本人が使う実パスワードそのものであり、admin が本人に別途通知する）。
  - **編集**: 各行の「**編集**」ボタン押下 → 従業員編集ダイアログ（`GET /settings/users/{username}/edit`、同一 `employee_form.html` を流用）→ `PUT /settings/users/{username}`。ユーザー名（username = PK）は変更不可・読み取り専用で表示。**パスワード欄を含み、空欄なら変更なし・入力時のみ更新**。
  - **削除**: 各行の「**削除**」ボタン押下 → **削除確認ダイアログ**（`partials/employee_delete_confirm.html`）を表示し、確定後に `POST /settings/users/{username}/deactivate` → **物理削除せず `is_active=false`**。担当タスクの履歴は保持。削除確定後、そのユーザーは一覧から非表示になる（`is_active=true` のみ一覧取得）。
  - **パスワード変更権限**: 従業員のパスワード変更は **admin のみ**実行可能（従業員追加・編集ダイアログ経由）。従業員本人はログイン後に自分のパスワードを変更できる（3.6 のパスワード変更フォーム、対象は自分自身のみ）。
- **パスワード変更**: 現在 / 新規 / 確認 の3フィールド → `POST /settings/password`。**自分自身のパスワードのみ変更可能**（本人操作）。新規と確認の一致はクライアント（Alpine）で事前検証。
- **従業員のパスワードは admin が「従業員追加・編集」ダイアログから直接設定・変更する。**従業員本人からの他ユーザーパスワード変更操作は不可。

---

## 4. Alpine.js 状態管理

クライアント完結の UI 状態のみ Alpine で持つ（データ本体は HTMX でサーバーから取得）。

### 4.1 モーダルルート（グローバル）

```html
<body x-data="modalRoot()">
  <!-- HTMX がここへダイアログ HTML を差し込む -->
  <div id="modal-root"
       x-show="open"
       x-transition.opacity
       @close-modal.window="open = false"
       @htmx:after-swap="if ($event.target.id === 'modal-root') open = true"
       class="modal-overlay">
  </div>
</body>

<script>
function modalRoot() {
  return {
    open: false,
    close() { this.open = false; document.getElementById('modal-root').innerHTML = ''; },
  }
}
</script>
```

- サーバーは保存成功時に **`HX-Trigger: close-modal`** ヘッダを返し、`@close-modal.window` で閉じる。
- オーバーレイクリック / ✕ / キャンセルで `close()`。`Esc` キーは `@keydown.escape.window="close()"`。

### 4.2 タスク一覧フィルタタブ

```html
<div x-data="{ status: 'all' }" class="filter-tabs">
  <template x-for="t in [['all','すべて'],['pending','未着手'],['in_progress','作業中'],['completed','完了']]">
    <button class="filter-tabs__item"
            :class="{ 'filter-tabs__item--active': status === t[0] }"
            @click="status = t[0]"
            :hx-get="`/tasks?status=${t[0]}`"
            hx-target="#task-list" hx-swap="innerHTML"
            x-text="t[1]"></button>
  </template>
</div>
```

### 4.3 パスワード変更フォーム（クライアント検証）

```html
<form x-data="{ pw:'', confirm:'', get match(){ return this.pw !== '' && this.pw === this.confirm } }"
      hx-post="/settings/password" hx-target="#pw-result">
  <input type="password" x-model="pw" name="new_password">
  <input type="password" x-model="confirm" name="confirm_password">
  <p class="field-error" x-show="confirm && !match">パスワードが一致しません</p>
  <button class="btn btn--primary" :disabled="!match">変更を保存</button>
</form>
```

### 4.4 完了確認ダイアログ内の二重送信防止

```html
<button class="btn btn--complete-solid"
        x-data="{ sending:false }"
        @click="sending = true" :disabled="sending"
        hx-post="/tasks/{{ task.task_id }}/complete"
        hx-target="#task-list" hx-swap="innerHTML">完了する</button>
```

---

## 5. CSS クラス名（BEM 記法）

`static/css/` にコンポーネント単位で分割。命名は `block__element--modifier`。

### 5.1 レイアウト
| ブロック | 要素 / 修飾子 |
| --- | --- |
| `.app-shell` | `__sidebar` `__main` `__header` `__body` |
| `.sidebar` | `__brand` `__nav` `__item` `__item--active` `__icon` `__footer` `__user` `__logout` |
| `.topbar` | `__title` `__actions` `__date` |

### 5.2 コンポーネント
| ブロック | 要素 / 修飾子 |
| --- | --- |
| `.btn` | `--primary` `--secondary` `--ghost` `--complete` `--danger` `--block` `:disabled` |
| `.status-badge` | `__dot` / `--pending` `--progress` `--completed` |
| `.task-card` | `__head` `__title` `__meta` `__assignee` `__actions` `__done-label` / `--pending` `--progress` `--completed` `--done` |
| `.task-table` | `__head` `__row` `__cell` `__cell--actions` / `--completed`（行） |
| `.kpi-card` | `__label` `__value` `__delta` / `--completed` `--pending` |
| `.progress` | `__bar` `__seg` `__seg--done` `__seg--progress` `__legend` |
| `.employee-card` | `__head` `__avatar` `__name` `__bar` `__stats` |
| `.avatar` | `--sm` `--lg` / `--blue` `--amber` `--green` |
| `.modal` | `__overlay` `__panel` `__head` `__title` `__close` `__body` `__footer` |
| `.field` | `__label` `__input` `__input--focus` `__error` `__row` |
| `.fab` | （右下固定 + ボタン） |
| `.filter-tabs` | `__item` `__item--active` |
| `.data-table` | `__head` `__row` `__cell` `__row--inactive` |
| `.alert` | `--error` `--success` `--warn` |

### 5.3 ユーティリティ
`.u-mono`（等幅数値）, `.u-truncate`, `.u-hide-mobile`, `.u-hide-desktop`。

### 5.4 ステータス → クラスの対応
```
pending     → status-badge--pending  / task-card--pending  （橙 #E08A00）
in_progress → status-badge--progress / task-card--progress （青 #2563EB）
completed   → status-badge--completed/ task-card--completed（緑 #1FA25E）
```

---

## 6. アニメーション仕様

控えめ・機能的に。過剰なモーションは避ける（現場での視認性優先）。

| 対象 | 挙動 | 実装 |
| --- | --- | --- |
| 画面初期表示 | ログインカード・サイドバー・各画面コンテンツがフェード＋わずかな上方向スライドで登場（`opacity 0→1` + `translateY(12~18px)→0`、350~500ms、`cubic-bezier(.2,.7,.2,1)`） | `@keyframes fadeSlideUp` / `loginIn` / `sidebarIn` を要素に付与 |
| 画面遷移スピナー | サイドバー押下から次画面表示までの間、**画面全体**（`position: fixed; inset:0`）にオーバーレイ＋スピナーを表示。サイドバーは同じ DOM に残ったまま（固定コンポーネントのため再マウントされない）。目安 400~600ms | `hx-indicator` を全画面オーバーレイ要素に紐付け、または `htmx:beforeRequest`/`htmx:afterSettle` でオーバーレイの表示/非表示を切替 |
| ログイン処理中 | ログインボタン押下後も同様に**画面全体**にオーバーレイ＋スピナーを表示してから遷移 | 同上 |
| モーダル表示 | オーバーレイ フェードイン 150~180ms、パネル `translateY(16px) scale(.97)→translateY(0) scale(1)` + フェード 200ms | Alpine `x-transition` + `@keyframes modalIn` / `cubic-bezier(.2,.7,.2,1)` |
| モーダル閉じ | オーバーレイ・パネルともに逆再生でフェードアウト（120~170ms） | `@keyframes backdropOut` / `modalOut`、`x-transition:leave` |
| ボタン（プライマリ系） | ホバーで **浮き上がる**（`translateY(-2px)` 前後 + シャドウ拡大）とともに背景色を濃色へ、押下時は **背景色をさらに濃く変化**させつつ `translateY(0) scale(.97)` で沈み込む | CSS `transition: background .15s, transform .15s, box-shadow .15s` を各ボタンに付与 |
| サイドバー・ログアウトボタン | ホバーで **背景色が赤（`--color-danger`）に変化**し `translateY(-3px)` で浮き上がる、押下でさらに濃い赤に変化し沈み込む | 同上（ホバー/押下で `background` と `transform` を同時に変更） |
| タスク追加 FAB（右下 +） | ホバーで `translateY(-3px) scale(1.05)` の浮き上がり＋シャドウ拡大、押下で濃色＋ `scale(.95)`。**回転アニメーションは使用しない** | 同上 |
| タスク完了 | 完了確定時、対象カードを一覧から除去し、下部の「完了済みタスク」セクションへ反映（一覧の再取得 `hx-swap` によるフェード） | HTMX swap 後のフェード |
| フィルタタブ | アクティブ背景を 150ms でスライド/フェード | CSS transition |
| HTMX 差し替え | `hx-swap="innerHTML swap:120ms settle:120ms"` で軽いフェード | HTMX `htmx-settling` クラス |
| トースト（保存完了） | 下からスライドイン、2.4秒後にフェードアウト | Alpine `x-data` + `setTimeout` |

- **`prefers-reduced-motion: reduce` を尊重**し、バー成長・スライド系は無効化しフェードのみに。

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```

---

## 7. 権限による画面制御

### 7.1 ロール
- `admin`（社長）: 全画面。ダッシュボード・設定・タスク追加/編集が可能。
- `employee`（従業員）: タスク一覧のみ。自分のタスクの閲覧と完了報告のみ。

### 7.2 サーバー側ガード（正）
UI の出し分けだけに頼らず、**必ずサーバーで検証**する。

```python
# 依存関数の例
def require_admin(user = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user

# admin 専用エンドポイント
@app.get("/dashboard")
def dashboard(user = Depends(require_admin)): ...
@app.get("/settings")
def settings(user = Depends(require_admin)): ...
@app.post("/tasks")            # 追加
@app.put("/tasks/{id}")        # 編集
@app.post("/settings/users")   # 従業員追加  … いずれも require_admin
```

- 未認証（JWT 無効 / 期限切れ）: 全保護ルートで `302 /login`。
- employee が `/dashboard` `/settings` へアクセス: `403`（またはタスク一覧へリダイレクト）。
- タスク一覧・完了確認・完了実行は admin/employee 両方可。ただし employee の対象は **自分の担当タスクに限定**（`SK == 自分の username` を検証）。

### 7.3 テンプレート側の出し分け（従）
`role` をテンプレートコンテキストに渡し、要素の表示可否を制御する。

```jinja2
{# サイドバー: role で項目を出し分け #}
{% if role == 'admin' %}
  {{ nav_item('dashboard', 'ダッシュボード', active) }}
  {{ nav_item('tasks', 'タスク一覧', active) }}
  {{ nav_item('settings', '設定', active) }}
{% else %}
  {{ nav_item('tasks', 'タスク一覧', active) }}
{% endif %}
{{ nav_logout() }}

{# タスク一覧: FAB と編集ボタンは admin のみ #}
{% if role == 'admin' %}
  <button class="fab" hx-get="/tasks/new" hx-target="#modal-root">+</button>
{% endif %}
```

### 7.4 完了済みタスクの制御
- `status == completed` のタスクは **編集・完了操作不可**（ボタン非表示、`task-card--done`）。
- ステータス遷移は `pending → in_progress → completed` の一方向。`completed` からの巻き戻し不可。

---

## 8. データ構造（参照）

### User（PK: `username`）
`user_id(UUID)` / `password_hash(bcrypt)` / `role(admin|employee)` / `name` / `created_at(ISO8601)` / `is_active(bool)`

### Task（PK: `TASK#<task_id>` / SK: `assignee_id`＝担当者 username）
`work`（作業内容）/ `location`（場所）/ `assignee_name` / `scheduled_date(YYYY-MM-DD)` / `status(pending|in_progress|completed)` / `created_by` / `created_at` / `updated_at`

> 一覧・カード表示用のタイトルはテンプレート側で `work + ' ／ ' + location` として結合する（`title` フィールドとして DB に保持しない）。

---

## 9. ルート一覧（サマリー）

| メソッド | パス | 権限 | 用途 | レスポンス |
| --- | --- | --- | --- | --- |
| GET | `/login` | 公開 | ログインフォーム | ページ |
| POST | `/login` | 公開 | 認証・JWT 発行 | リダイレクト / 断片 |
| POST | `/logout` | 認証 | ログアウト | リダイレクト `/login` |
| GET | `/dashboard` | admin | ダッシュボード | ページ |
| GET | `/tasks` | admin/emp | タスク一覧（`?status=` `?assignee=`・デフォルトは完了済みを除外） | ページ / 断片 |
| GET | `/tasks?include_completed=true` | admin/emp | 「完了済みタスクを表示する」展開時の完了済み一覧 | 断片 |
| GET | `/tasks/new` | admin | 追加ダイアログ | 断片 |
| POST | `/tasks` | admin | 追加 | 断片 + `HX-Trigger` |
| GET | `/tasks/{id}/edit` | admin | 編集ダイアログ | 断片 |
| PUT | `/tasks/{id}` | admin | 更新 | 断片 + `HX-Trigger` |
| GET | `/tasks/{id}/confirm` | admin/emp | 完了確認ダイアログ | 断片 |
| POST | `/tasks/{id}/complete` | admin/emp | 完了実行 | 断片（一覧再描画） |
| GET | `/settings` | admin | 設定画面 | ページ |
| GET | `/settings/users/new` | admin | 従業員追加ダイアログ | 断片 |
| POST | `/settings/users` | admin | 従業員追加（本パスワードを含む） | 断片 |
| GET | `/settings/users/{username}/edit` | admin | 従業員編集ダイアログ | 断片 |
| PUT | `/settings/users/{username}` | admin | 従業員編集（パスワード変更含む・空欄時は変更なし） | 断片 |
| GET | `/settings/users/{username}/delete-confirm` | admin | 削除確認ダイアログ | 断片 |
| POST | `/settings/users/{username}/deactivate` | admin | 削除確定（is_active=false・一覧から非表示） | 断片 |
| POST | `/settings/password` | 認証 | パスワード変更 | 断片 |

---

## 10. 対応デバイス・非機能

- 画面表示 3秒以内。KPI 集計は全件スキャン後にサーバーで集計してから描画。
- 対応: スマートフォン（iOS / Android）・PC（Chrome 最新）。
- 画像アップロード（S3）は将来対応。現時点ではタスクに画像フィールドを持たせない。

---

### デザイン参照
- 全画面デザイン: `Gemba One 画面デザイン.dc.html`（デザインボード）
  - `03` タスク一覧（**採用: 2a** タスクカードグリッド + employee スマホ）/ `04` ダイアログ / `05` 設定（+ 従業員 追加・編集ダイアログ）/ `00` デザインシステム
- 採用案: ダッシュボード = **1a**、タスク一覧 = **2a**（いずれも確定）。
