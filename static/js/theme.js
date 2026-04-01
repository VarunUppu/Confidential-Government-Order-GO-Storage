(function () {
  'use strict';

  const THEME_KEY   = 'go-storage-theme';
  const DARK_THEME  = 'dark';
  const LIGHT_THEME = 'light';

  function setTheme(theme) {
    const html = document.documentElement;
    if (theme === DARK_THEME) {
      html.setAttribute('data-theme', DARK_THEME);
    } else {
      html.removeAttribute('data-theme');
    }
    localStorage.setItem(THEME_KEY, theme);
    updateToggleButton(theme);
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || LIGHT_THEME;
    setTheme(current === LIGHT_THEME ? DARK_THEME : LIGHT_THEME);
  }

  function initTheme() {
    const saved      = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(saved || (prefersDark ? DARK_THEME : LIGHT_THEME));
  }

  function updateToggleButton(theme) {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.textContent        = theme === DARK_THEME ? '☀️' : '🌙';
      btn.title              = theme === DARK_THEME ? 'Light Mode' : 'Dark Mode';
      btn.setAttribute('aria-label',
        theme === DARK_THEME ? 'Switch to light mode' : 'Switch to dark mode');
    });
  }

  document.addEventListener('click', function (e) {
    if (e.target.closest('.theme-toggle')) {
      e.preventDefault();
      toggleTheme();
    }
  });

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem(THEME_KEY)) {
      setTheme(e.matches ? DARK_THEME : LIGHT_THEME);
    }
  });

  window.themeManager = { toggle: toggleTheme, set: setTheme };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();


(function () {
  function initActiveLinks() {
    const path  = window.location.pathname;
    const links = document.querySelectorAll('.sidebar-menu a');
    links.forEach(link => {
      const href = link.getAttribute('href') || '';
      const isActive = href === '/'
        ? path === '/'
        : href.length > 1 && path.startsWith(href);
      link.classList.toggle('active', isActive);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initActiveLinks);
  } else {
    initActiveLinks();
  }
})();


(function () {
  function initAlerts() {
    document.querySelectorAll('.alert').forEach(alert => {
      setTimeout(() => {
        alert.style.transition = 'opacity 0.4s ease';
        alert.style.opacity    = '0';
        setTimeout(() => alert.remove(), 400);
      }, 5000);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAlerts);
  } else {
    initAlerts();
  }
})();