import type { Metadata } from 'next';
import { getDict, type Locale } from '@/lib/i18n';

export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }): Promise<Metadata> {
  const { locale } = await params;
  return { title: getDict(locale).about.title };
}

export default async function AboutPage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const t = getDict(locale);
  return (
    <article className="max-w-3xl space-y-8">
      <h1 className="text-2xl font-bold text-heading">{t.about.title}</h1>
      {t.about.sections.map((s) => (
        <section key={s.heading} className="space-y-2">
          <h2 className="text-lg font-bold text-heading">{s.heading}</h2>
          <p className="leading-relaxed">{s.body}</p>
        </section>
      ))}
      <p className="rounded border border-border bg-surface-tertiary p-4 text-sm text-muted">{t.disclaimer}</p>
    </article>
  );
}
