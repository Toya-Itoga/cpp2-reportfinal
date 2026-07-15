/**
 * static/js/login.js
 * ログイン画面の JavaScript
 * - ページローダー表示（ログインボタン押下時）
 */

document.addEventListener('DOMContentLoaded', () => {
  // ─── HTMX リクエスト開始時にページローダーを表示 ───
  document.body.addEventListener('htmx:beforeRequest', () => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = 'flex';
  });

  // ─── HTMX レスポンス受信後にページローダーを非表示 ───
  document.body.addEventListener('htmx:afterSettle', () => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = '';
  });
});
