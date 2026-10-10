import type { Metadata } from 'next';
import Link from 'next/link';
import { getCategories, getCheckins } from '@/lib/data';
import { formatDate, getDict, pick, type Locale } from '@/lib/i18n';

export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> {
  const { locale } = await params;
  return { title: getDict(locale).nav.knowledge };
}

export default async function KnowledgePage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const t = getDict(locale);
  const { checkins } = getCheckins();

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-heading">{t.nav.knowledge}</h1>
      {getCategories().map((cat) => {
        const related = checkins.filter((c) => c.knowledge.includes(cat.id));
        return (
          <section key={cat.id} id={cat.id} className="card card--default scroll-mt-6">
            <div className="card__header">
              <h2 className="card__title text-lg">{pick(locale, cat.title, cat.title_en)}</h2>
              <p className="card__description">{pick(locale, cat.description, cat.description_en)}</p>
            </div>
            <div className="card__content grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-semibold text-muted">{t.sections.notes}</h3>
                {cat.notes.length === 0 ? (
                  <p className="text-sm text-muted">{t.sections.noNotes}</p>
                ) : (
                  <ul className="space-y-1">
                    {cat.notes.map((n) => (
                      <li key={n.slug}>
                        <Link href={`/${locale}/knowledge/${cat.id}/${n.slug}/`} className="text-link hover:underline">
                          {pick(locale, n.title, n.title_en)}
                        </Link>
                        <span className="ml-2 text-xs text-muted">{formatDate(locale, n.date)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h3 className="mb-2 text-sm font-semibold text-muted">{t.sections.related}</h3>
                <ul className="flex flex-wrap gap-2">
                  {related.map((c) => (
                    <li key={c.id}>
                      <Link
                        href={`/${locale}/checkins/${c.id}/`}
                        title={pick(locale, c.title, c.title_en)}
                        className={`chip chip--sm ${c.category === cat.id ? 'chip--soft chip--accent' : 'chip--secondary'}`}
                      >
                        <span className="chip__label font-mono">{c.id}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}
