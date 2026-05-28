const THEME_KEY = 'user_preferences';

export function getSavedTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    if (!saved) return 'light';

    const parsed = JSON.parse(saved);
    return parsed.theme === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export function applyTheme(theme) {
  const resolved = theme === 'dark' ? 'dark' : 'light';
  const root = document.documentElement;

  root.classList.toggle('dark', resolved === 'dark');
  root.style.colorScheme = resolved;
}

export function saveTheme(theme) {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    const parsed = saved ? JSON.parse(saved) : {};
    const next = {
      ...parsed,
      theme: theme === 'dark' ? 'dark' : 'light'
    };
    localStorage.setItem(THEME_KEY, JSON.stringify(next));
  } catch {
    localStorage.setItem(THEME_KEY, JSON.stringify({ theme: theme === 'dark' ? 'dark' : 'light' }));
  }
}
