import type { Metadata } from 'next';
import Link from 'next/link';
import { StatusChip } from '@/components/ui';
import { getCheckins, getLessons } from '@/lib/data';
import { getDict, pick, type Locale } from '@/lib/i18n';

export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> {
  const { locale } = await params;
  return { title: getDict(locale).nav.lessons };
}

export default async function LessonsPage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const t = getDict(locale);
  const { checkins } = getCheckins();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-heading">{t.nav.lessons}</h1>
      <ol className="grid gap-4 md:grid-cols-2">
        {getLessons().map((l) => {
          const list = checkins.filter((c) => c.lesson === l.id).sort((a, b) => a.id.localeCompare(b.id));
          return (
            <li key={l.id} className="card card--default">
              <div className="card__header">
                <p className="font-mono text-xs text-muted">{l.id}</p>
                <h2 className="card__title">{pick(locale, l.title, l.title_en)}</h2>
              </div>
              <ul className="card__content space-y-2">
                {list.map((c) => (
                  <li key={c.id} className="flex flex-wrap items-center justify-between gap-2">
                    <Link href={`/${locale}/checkins/${c.id}/`} className="hover:text-link">
                      <span className="mr-2 font-mono text-sm text-muted">{c.id}</span>
                      {pick(locale, c.title, c.title_en)}
                    </Link>
                    <StatusChip locale={locale} status={c.status} />
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
