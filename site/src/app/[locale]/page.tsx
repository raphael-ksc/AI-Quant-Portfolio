import Link from 'next/link';
import { CheckinCard, SectionTitle } from '@/components/ui';
import { getCategories, getCheckins } from '@/lib/data';
import { getDict, pick, type Locale } from '@/lib/i18n';

export default async function HomePage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const t = getDict(locale);
  const { checkins, stats } = getCheckins();
  const categories = getCategories();
  const catTitle = Object.fromEntries(categories.map((c) => [c.id, pick(locale, c.title, c.title_en)]));
  const flagship = checkins.filter((c) => c.flagship);
  const pct = stats.total ? Math.round((stats.by_status.done / stats.total) * 100) : 0;

  const statTiles = [
    [t.stats.total, stats.total],
    [t.stats.done, stats.by_status.done],
    [t.stats.wip, stats.by_status.wip],
    [t.stats.todo, stats.by_status.todo],
  ] as const;

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="space-y-4 pt-4">
        <p className="text-sm font-semibold tracking-wide text-accent">{t.hero.kicker}</p>
        <h1 className="text-3xl font-bold leading-tight text-heading sm:text-4xl">{t.hero.title}</h1>
        <p className="max-w-3xl text-muted">{t.hero.subtitle}</p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link href={`/${locale}/checkins/`} className="button button--primary button--md">
            {t.hero.ctaCheckins}
          </Link>
          <Link href={`/${locale}/about/`} className="button button--secondary button--md">
            {t.hero.ctaAbout}
          </Link>
        </div>
      </section>

      {/* 進度統計 */}
      <section>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {statTiles.map(([label, value]) => (
            <div key={label} className="card card--default">
              <div className="card__content">
                <p className="text-sm text-muted">{label}</p>
                <p className="font-mono text-3xl font-bold">{value}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4" aria-label={`${t.stats.done} ${pct}%`}>
          <div className="h-2 w-full overflow-hidden rounded bg-default">
            <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-1 text-right font-mono text-xs text-muted">{pct}%</p>
        </div>
      </section>

      {/* 代表作 */}
      <section>
        <SectionTitle title={t.sections.flagship} note={t.sections.flagshipNote} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {flagship.map((c) => (
            <CheckinCard key={c.id} locale={locale} checkin={c} categoryTitle={catTitle[c.category]} />
          ))}
        </div>
      </section>

      {/* 執行路線 */}
      <section>
        <SectionTitle title={t.sections.roadmap} note={t.sections.roadmapNote} />
        <ol className="space-y-3">
          {Object.keys(t.phases).map((p) => {
            const list = checkins.filter((c) => String(c.phase) === p);
            return (
              <li key={p} className="card card--default">
                <div className="card__content flex flex-col gap-2 sm:flex-row sm:items-center">
                  <p className="w-56 shrink-0 font-semibold">
                    {t.phaseLabel(Number(p))} · {t.phases[p]}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {list.map((c) => (
                      <Link
                        key={c.id}
                        href={`/${locale}/checkins/${c.id}/`}
                        title={pick(locale, c.title, c.title_en)}
                        className={`chip chip--sm ${
                          c.status === 'done' ? 'chip--primary chip--success' : c.status === 'wip' ? 'chip--soft chip--warning' : 'chip--secondary chip--default'
                        }`}
                      >
                        <span className="chip__label font-mono">
                          {c.flagship ? '★ ' : ''}
                          {c.id}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </section>

      {/* 能力地圖 */}
      <section>
        <SectionTitle title={t.sections.capabilities} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map((cat) => {
            const related = checkins.filter((c) => c.knowledge.includes(cat.id));
            return (
              <Link key={cat.id} href={`/${locale}/knowledge/#${cat.id}`} className="card card--default block hover:ring-1 hover:ring-accent">
                <div className="card__header">
                  <h3 className="card__title">{pick(locale, cat.title, cat.title_en)}</h3>
                  <p className="card__description">{pick(locale, cat.description, cat.description_en)}</p>
                </div>
                <div className="card__footer font-mono text-xs text-muted">
                  {related.filter((c) => c.status === 'done').length} / {related.length}
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
