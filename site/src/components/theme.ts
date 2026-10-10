// 主題設定：data-theme 決定配色；class 決定沿用 HeroUI 的淺色或深色計算色
export const THEMES = [
  { id: 'dark', label: 'Dark', className: 'dark' },
  { id: 'heritage', label: 'Heritage Navy', className: 'light' },
  { id: 'crimson', label: 'Crimson', className: 'light' },
] as const;

export type ThemeId = (typeof THEMES)[number]['id'];
export const DEFAULT_THEME: ThemeId = 'dark';
export const THEME_STORAGE_KEY = 'aqp-theme';

/** 在 <head> 執行，於畫面繪製前套用已儲存的主題，避免閃爍 */
export const themeInitScript = `(function(){try{var t=localStorage.getItem('${THEME_STORAGE_KEY}');var m=${JSON.stringify(
  Object.fromEntries(THEMES.map((t) => [t.id, t.className])),
)};if(!m[t])t='${DEFAULT_THEME}';var e=document.documentElement;e.setAttribute('data-theme',t);e.classList.remove('light','dark');e.classList.add(m[t]);}catch(_){}})();`;
