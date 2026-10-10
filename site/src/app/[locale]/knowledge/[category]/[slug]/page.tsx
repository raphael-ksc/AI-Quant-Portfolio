import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { MarkdownBody, Notice } from '@/components/ui';
import { getCategories, getCategory, getCheckins } from '@/lib/data';
import { LOCALES, formatDate, getDict, pick, type Locale } from '@/lib/i18n';

export const dynamicParams = false;

export function generateStaticParams() {
  return LOCALES.flatMap((locale) =>
    getCategories().flatMap((cat) => cat.notes.map((n) => ({ locale, category: cat.id, slug: n.slug }))),
  );
}

type Params = Promise<{ locale: Locale; category: string; slug: string }>;

function findNote(category: string, slug: string) {
  const cat = getCategory(category);
  return { cat, note: cat?.notes.find((n) => n.slug === slug) };
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, category, slug } = await params;
  const { note } = findNote(category, slug);
  return note ? { title: pick(locale, note.title, note.title_en) } : {};
}

export default async function NotePage({ params }: { params: Params }) {
  const { locale, category, slug } = await params;
  const { cat, note } = findNote(category, slug);
  if (!cat || !note) notFound();
  const t = getDict(locale);
  const titles = Object.fromEntries(getCheckins().checkins.map((c) => [c.id, pick(locale, c.title, c.title_en)]));

  return (
    <article className="space-y-6">
      <Link href={`/${locale}/knowledge/#${cat.id}`} className="text-sm text-link">
        ← {pick(locale, cat.title, cat.title_en)}
      </Link>
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-heading sm:text-3xl">{pick(locale, note.title, note.title_en)}</h1>
        <p className="text-sm text-muted">{formatDate(locale, note.date)}</p>
        {note.related.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted">{t.sections.related}</span>
            {note.related.map((id) => (
              <Link key={id} href={`/${locale}/checkins/${id}/`} title={titles[id]} className="chip chip--sm chip--secondary">
                <span className="chip__label font-mono">{id}</span>
              </Link>
            ))}
          </div>
        )}
      </header>
      {locale === 'en-AU' && !note.body_en && <Notice>{t.englishPending}</Notice>}
      <MarkdownBody source={locale === 'en-AU' && note.body_en ? note.body_en : note.body} />
    </article>
  );
}
