import Link from 'next/link';
import { getDict, type Locale } from '@/lib/i18n';
import { LocaleSwitcher } from './LocaleSwitcher';
import { ThemeSwitcher } from './ThemeSwitcher';

const REPO_URL = 'https://github.com/raphael-ksc/AI-Quant-Portfolio';

export function SiteHeader({ locale }: { locale: Locale }) {
  const t = getDict(locale);
  const links = [
    ['', t.nav.home],
    ['checkins/', t.nav.checkins],
    ['lessons/', t.nav.lessons],
    ['knowledge/', t.nav.knowledge],
    ['about/', t.nav.about],
  ] as const;

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href={`/${locale}/`} className="text-lg font-bold text-heading">
          {t.siteName}
        </Link>
        <nav aria-label="main" className="flex flex-wrap gap-4 text-sm">
          {links.map(([href, label]) => (
            <Link key={href} href={`/${locale}/${href}`} className="hover:text-link">
              {label}
            </Link>
          ))}
        </nav>
        <div className="flex flex-wrap items-center gap-3">
          <ThemeSwitcher label={t.theme} />
          <LocaleSwitcher locale={locale} label={t.language} />
        </div>
      </div>
    </header>
  );
}

export function SiteFooter({ locale }: { locale: Locale }) {
  const t = getDict(locale);
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl space-y-2 px-4 py-6 text-sm text-muted">
        <p>{t.disclaimer}</p>
        <p>
          {t.footer}
          <a href={REPO_URL} className="text-link underline" rel="noopener noreferrer" target="_blank">
            github.com/raphael-ksc/AI-Quant-Portfolio
          </a>
        </p>
      </div>
    </footer>
  );
}
