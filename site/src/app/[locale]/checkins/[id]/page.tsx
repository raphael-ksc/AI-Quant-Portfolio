import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { FlagshipChip, MarkdownBody, Notice, StatusChip } from '@/components/ui';
import { getCategories, getCheckin, getCheckins, getLessons } from '@/lib/data';
import { LOCALES, formatDate, getDict, pick, type Locale } from '@/lib/i18n';

const REPO_TREE = 'https://github.com/raphael-ksc/AI-Quant-Portfolio/tree/main';
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? '';

export const dynamicParams = false;

export function generateStaticParams() {
  const { checkins } = getCheckins();
  return LOCALES.flatMap((locale) => checkins.map((c) => ({ locale, id: c.id })));
}

type Params = Promise<{ locale: Locale; id: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, id } = await params;
  const c = getCheckin(id);
  return c ? { title: `${c.id} ${pick(locale, c.title, c.title_en)}` } : {};
}

export default async function CheckinPage({ params }: { params: Params }) {
  const { locale, id } = await params;
  const c = getCheckin(id);
  if (!c) notFound();
  const t = getDict(locale);
  const lesson = getLessons().find((l) => l.id === c.lesson);
  const cats = Object.fromEntries(getCategories().map((x) => [x.id, pick(locale, x.title, x.title_en)]));
  const useEnglish = locale === 'en-AU' && c.body_en;

  const meta: [string, React.ReactNode][] = [
    [t.fields.lesson, lesson ? `${lesson.id} · ${pick(locale, lesson.title, lesson.title_en)}` : c.lesson],
    [t.fields.category, cats[c.category]],
    [t.fields.phase, `${t.phaseLabel(c.phase)} · ${t.phases[String(c.phase)]}`],
    [t.fields.order, `${c.order} / 24`],
    [t.fields.date, formatDate(locale, c.date)],
    [t.fields.confidence, c.confidence ? `${c.confidence} / 5` : '—'],
    [t.fields.symbols, c.symbols.length ? c.symbols.join(', ') : '—'],
    [t.fields.source, c.source],
  ];

  // 內文已經用 ![](…) 插入的圖，不在上方圖片區重複顯示
  const body = useEnglish ? c.body_en! : c.body;
  const gallery = c.figures.filter((f) => !body.includes(f.slice(c.path.length + 1)));
  return (
    <article className="space-y-6">
      <Link href={`/${locale}/checkins/`} className="text-sm text-link">
        {t.backToList}
      </Link>
      <header className="space-y-3">
        <p className="font-mono text-sm text-muted">{c.id}</p>
        <h1 className="text-2xl font-bold text-heading sm:text-3xl">{pick(locale, c.title, c.title_en)}</h1>
        {locale === 'en-AU' && <p className="text-sm text-muted">{c.title}</p>}
        <div className="flex flex-wrap gap-2">
          <StatusChip locale={locale} status={c.status} />
          {c.flagship && <FlagshipChip locale={locale} />}
          {c.knowledge.map((k) => (
            <Link key={k} href={`/${locale}/knowledge/#${k}`} className="chip chip--sm chip--secondary">
              <span className="chip__label">{cats[k]}</span>
            </Link>
          ))}
        </div>
      </header>

      <section className="card card--default">
        <div className="card__content">
          <h2 className="mb-2 font-semibold">{t.sections.meta}</h2>
          <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-[10rem_1fr]">
            {meta.map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="text-muted">{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          {c.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {c.tags.map((tag) => (
                <span key={tag} className="chip chip--sm chip--tertiary">
                  <span className="chip__label">#{tag}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </section>

      {gallery.length > 0 && (
        <section className="grid gap-4 sm:grid-cols-2">
          {gallery.map((f) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={f} src={`${BASE_PATH}/${f}`} alt={f.split('/').pop() ?? ''} className="w-full rounded border border-border" />
          ))}
        </section>
      )}

      <section>
        {locale === 'en-AU' && !c.body_en && <Notice>{t.englishPending}</Notice>}
        <MarkdownBody source={body} baseDir={c.path} locale={locale} />
      </section>

      <p className="text-sm">
        <a href={`${REPO_TREE}/${c.path}`} className="text-link underline" rel="noopener noreferrer" target="_blank">
          GitHub: {c.path}
        </a>
      </p>
    </article>
  );
}
