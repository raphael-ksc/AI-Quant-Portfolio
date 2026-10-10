// 伺服器端共用元件：直接使用 HeroUI 的 BEM CSS class（card、chip），不需載入 React 互動層
import Link from 'next/link';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDict, pick, type Locale } from '@/lib/i18n';
import type { Checkin, Status } from '@/lib/types';

const STATUS_COLOR: Record<Status, string> = {
  done: 'chip--success',
  wip: 'chip--warning',
  todo: 'chip--default',
};

export function Chip({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`chip chip--sm chip--soft ${className}`}>
      <span className="chip__label">{children}</span>
    </span>
  );
}

export function StatusChip({ locale, status }: { locale: Locale; status: Status }) {
  return <Chip className={STATUS_COLOR[status]}>{getDict(locale).status[status]}</Chip>;
}

export function FlagshipChip({ locale }: { locale: Locale }) {
  return <Chip className="chip--accent">★ {getDict(locale).flagship}</Chip>;
}

export function CheckinCard({
  locale,
  checkin,
  categoryTitle,
}: {
  locale: Locale;
  checkin: Checkin;
  categoryTitle: string;
}) {
  const t = getDict(locale);
  return (
    <Link
      href={`/${locale}/checkins/${checkin.id}/`}
      className="card card--default block transition hover:ring-1 hover:ring-accent"
    >
      <div className="card__header">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
          <span className="font-mono">{checkin.id}</span>
          <span>·</span>
          <span>{t.phaseLabel(checkin.phase)}</span>
        </div>
        <h3 className="card__title">{pick(locale, checkin.title, checkin.title_en)}</h3>
        <p className="card__description">{categoryTitle}</p>
      </div>
      <div className="card__footer flex flex-wrap gap-2">
        <StatusChip locale={locale} status={checkin.status} />
        {checkin.flagship && <FlagshipChip locale={locale} />}
      </div>
    </Link>
  );
}

export function MarkdownBody({ source }: { source: string }) {
  return (
    <div className="prose">
      <Markdown remarkPlugins={[remarkGfm]}>{source}</Markdown>
    </div>
  );
}

export function SectionTitle({ title, note }: { title: string; note?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-xl font-bold text-heading">{title}</h2>
      {note && <p className="mt-1 text-sm text-muted">{note}</p>}
    </div>
  );
}

export function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded border border-border bg-surface-tertiary px-3 py-2 text-sm text-muted">{children}</p>
  );
}
