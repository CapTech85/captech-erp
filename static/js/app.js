// static/js/app.js
// JS applicatif général extrait de base.html (toasts, thème, sidebar)

window.toast = function (msg, type = "info") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = "rounded-lg px-4 py-3 shadow border text-sm transition-all";
  if (type === "success") el.className += " bg-success-50 text-success-900 border-success-200";
  else if (type === "error") el.className += " bg-danger-50 text-danger-900 border-danger-200";
  else el.className += " bg-slate-100 text-ink-900 border-slate-200";

  el.textContent = msg;
  root?.appendChild(el);
  el.style.opacity = 0;
  requestAnimationFrame(() => { el.style.opacity = 1; });
  setTimeout(() => {
    el.style.opacity = 0;
    setTimeout(() => el.remove(), 200);
  }, 2400);
};

function toggleSidebar() {
  const aside = document.getElementById("sidebar");
  const ov = document.getElementById("overlay");
  const hidden = aside?.classList.toggle("-translate-x-full");
  ov?.classList.toggle("hidden", !!hidden);
}

document.getElementById("toggleTheme")?.addEventListener("click", () => {
  const cls = document.documentElement.classList;
  const dark = cls.toggle("dark");
  localStorage.setItem("theme", dark ? "dark" : "light");
  toast(dark ? "Mode sombre activé" : "Mode clair activé", "success");
});
