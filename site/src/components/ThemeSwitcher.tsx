'use client';

import { Button } from '@heroui/react';
import { useEffect, useState } from 'react';
import { DEFAULT_THEME, THEMES, THEME_STORAGE_KEY, type ThemeId } from './theme';

export function ThemeSwitcher({ label }: { label: string }) {
  const [current, setCurrent] = useState<ThemeId>(DEFAULT_THEME);

  // 掛載後讀取 <head> 腳本已套用的主題
  useEffect(() => {
    const t = document.documentElement.getAttribute('data-theme') as ThemeId | null;
    if (t && THEMES.some((x) => x.id === t)) setCurrent(t);
  }, []);

  function apply(id: ThemeId) {
    const theme = THEMES.find((x) => x.id === id)!;
    const el = document.documentElement;
    el.setAttribute('data-theme', id);
    el.classList.remove('light', 'dark');
    el.classList.add(theme.className);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, id);
    } catch {
      // 無痕模式或封鎖儲存時忽略，主題仍會在本頁生效
    }
    setCurrent(id);
  }

  return (
    <div role="group" aria-label={label} className="flex flex-wrap items-center gap-1">
      {THEMES.map((t) => (
        <Button
          key={t.id}
          size="sm"
          variant={current === t.id ? 'primary' : 'ghost'}
          aria-pressed={current === t.id}
          onPress={() => apply(t.id)}
        >
          {t.label}
        </Button>
      ))}
    </div>
  );
}
