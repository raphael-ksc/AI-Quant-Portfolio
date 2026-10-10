'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LOCALES, type Locale } from '@/lib/i18n';

const LABELS: Record<Locale, string> = { 'zh-TW': '繁中', 'en-AU': 'EN' };

/** 切換語系時保留目前頁面路徑 */
export function LocaleSwitcher({ locale, label }: { locale: Locale; label: string }) {
  const pathname = usePathname() || `/${locale}/`;
  const rest = pathname.replace(/^\/(zh-TW|en-AU)/, '');

  return (
    <nav aria-label={label} className="flex items-center gap-2 text-sm">
      {LOCALES.map((l) =>
        l === locale ? (
          <span key={l} aria-current="true" className="font-bold text-accent">
            {LABELS[l]}
          </span>
        ) : (
          <Link key={l} href={`/${l}${rest || '/'}`} className="text-muted hover:text-link">
            {LABELS[l]}
          </Link>
        ),
      )}
    </nav>
  );
}
