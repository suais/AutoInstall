/* =========================================================
   AutoInstall 官网脚本 — 下载配置
   ---------------------------------------------------------
   下载地址集中在此配置。后续部署到 Vercel / GitHub Pages
   时如需改用外链（例如 GitHub Release），只需把
   DOWNLOAD_URL 改成完整外链地址，无需改动 HTML。
   ========================================================= */

(function () {
  "use strict";

  // ── 下载配置 ──────────────────────────────────────────
  // GitHub Release 外链模式：exe 托管在 GitHub Releases
  const DOWNLOAD_URL =
    "https://github.com/suais/AutoInstall/releases/latest/download/AutoInstall.exe";

  // ── 版本信息（与 src/config.py 保持一致）──────────────
  const APP_VERSION = "v1.0.0";
  const FILE_SIZE = "45 MB";

  // ── 填充下载按钮 ─────────────────────────────────────
  document.querySelectorAll(".download-link").forEach(function (a) {
    a.href = DOWNLOAD_URL;
    a.setAttribute("download", "AutoInstall.exe");
  });

  // ── 填充版本 / 大小信息 ───────────────────────────────
  var verEls = document.querySelectorAll("#verText, #verText2");
  verEls.forEach(function (el) {
    el.textContent = APP_VERSION;
  });

  var sizeEls = document.querySelectorAll("#sizeText, #sizeText2");
  sizeEls.forEach(function (el) {
    el.textContent = FILE_SIZE;
  });
})();
