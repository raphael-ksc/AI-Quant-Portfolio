import type { Metadata } from 'next';
import { CheckinExplorer, type ExplorerItem, type ExplorerLabels } from '@/components/CheckinExplorer';
import { getCategories, getCheckins, getLessons } from '@/lib/data';
import { getDict, pick, type Locale } from '@/lib/i18n';

export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> {
  const { locale } = await params;
  return { title: getDict(locale).nav.checkins };
}

export default async function CheckinsPage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const t = getDict(locale);
  const { checkins } = getCheckins();

  // 只傳列表需要的欄位給 Client Component，避免把內文打包進前端
  const items: ExplorerItem[] = checkins.map((c) => ({
    id: c.id,
    title: pick(locale, c.title, c.title_en),
    phase: c.phase,
    order: c.order,
    lesson: c.lesson,
    category: c.category,
    status: c.status,
    flagship: c.flagship,
  }));
  const labels: ExplorerLabels = {
    ...t.filters,
    flagship: t.flagship,
    statusNames: t.status,
    phaseNames: t.phases,
    phasePrefix: Object.keys(t.phases).map((p) => `${t.phaseLabel(Number(p))} · ${t.phases[p]}`),
    lessonNames: Object.fromEntries(getLessons().map((l) => [l.id, pick(locale, l.title, l.title_en)])),
    categoryNames: Object.fromEntries(getCategories().map((c) => [c.id, pick(locale, c.title, c.title_en)])),
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-heading">{t.nav.checkins}</h1>
      <CheckinExplorer locale={locale} items={items} labels={labels} />
    </div>
  );
}
