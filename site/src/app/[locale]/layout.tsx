import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { SiteFooter, SiteHeader } from '@/components/SiteChrome';
import { DEFAULT_THEME, THEMES, themeInitScript } from '@/components/theme';
import { HTML_LANG, LOCALES, getDict, isLocale } from '@/lib/i18n';
import '../globals.css';

export const dynamicParams = false;

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const t = getDict(locale);
  return {
    title: { default: t.siteName, template: `%s | ${t.siteName}` },
    description: t.hero.title,
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const defaultClass = THEMES.find((t) => t.id === DEFAULT_THEME)!.className;

  return (
    <html lang={HTML_LANG[locale]} data-theme={DEFAULT_THEME} className={defaultClass} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="bg-background text-foreground">
        <SiteHeader locale={locale} />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <SiteFooter locale={locale} />
      </body>
    </html>
  );
}
