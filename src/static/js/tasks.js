/**
 * static/js/tasks.js
 * タスク一覧画面の JavaScript
 * - ページ遷移スピナー制御
 * - HTMX close-modal イベントのリッスン
 */

document.addEventListener('DOMContentLoaded', () => {
  // ─── HTMX リクエスト開始時にローダー表示 ───
  document.body.addEventListener('htmx:beforeRequest', () => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = 'flex';
  });

  // ─── HTMX レスポンス受信後にローダー非表示 ───
  document.body.addEventListener('htmx:afterSettle', () => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = '';
  });

  // ─── モーダル内コンテンツ差し込み後にローダーを確実に消す ───
  document.body.addEventListener('htmx:afterSwap', () => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = '';
  });
});
