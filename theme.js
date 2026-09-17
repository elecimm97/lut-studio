(() => {
  const root = document.documentElement;
  let saved;
  try { saved = localStorage.getItem('lut-studio-theme'); } catch (_) {}
  const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  function apply(theme) {
    root.dataset.theme = theme;
    root.dataset.bsTheme = theme;
    const button = document.getElementById('theme-toggle');
    if (button) {
      button.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
      button.setAttribute('aria-pressed', String(theme === 'dark'));
      button.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
  }
  apply(saved === 'light' || saved === 'dark' ? saved : preferred);
  document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.lang = 'en';
    apply(root.dataset.theme);
    document.getElementById('theme-toggle').addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(theme);
      try { localStorage.setItem('lut-studio-theme', theme); } catch (_) {}
    });
  });
})();
