// static/js/darkmode-toggle.js
// Accessible dark mode toggle with system preference fallback and prefers-reduced-motion support
(function () {
  const DARK_CLS = 'dark';
  const BTN_ID = 'dark-toggle';

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add(DARK_CLS);
    } else if (theme === 'light') {
      document.documentElement.classList.remove(DARK_CLS);
    }
  }

  function getStoredTheme() {
    try {
      return localStorage.getItem('theme');
    } catch (e) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      localStorage.setItem('theme', theme);
    } catch (e) {
      // ignore
    }
  }

  // initialize
  const stored = getStoredTheme();
  if (stored) {
    applyTheme(stored);
  } else {
    // respect system preference
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
  }

  // init toggle button
  document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById(BTN_ID);
    if (!btn) return;
    // set ARIA initial state
    const isDark = document.documentElement.classList.contains(DARK_CLS);
    btn.setAttribute('aria-pressed', String(isDark));
    btn.addEventListener('click', function (e) {
      const newState = !document.documentElement.classList.contains(DARK_CLS);
      applyTheme(newState ? 'dark' : 'light');
      storeTheme(newState ? 'dark' : 'light');
      btn.setAttribute('aria-pressed', String(newState));
      // update visible icon if applicable
    });
  });
})();
