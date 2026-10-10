'use client';

// 打卡列表：依階段或課程分組，並可依狀態、分類篩選
import { Button } from '@heroui/react';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import type { Status } from '@/lib/types';

export interface ExplorerItem {
  id: string;
  title: string;
  phase: number;
  order: number;
  lesson: string;
  category: string;
  status: Status;
  flagship: boolean;
}

export interface ExplorerLabels {
  all: string;
  byPhase: string;
  byLesson: string;
  status: string;
  category: string;
  flagship: string;
  statusNames: Record<Status, string>;
  phaseNames: Record<string, string>;
  phasePrefix: string[]; // 各階段的顯示標題，例如「第 1 階段 · 地基」
  lessonNames: Record<string, string>;
  categoryNames: Record<string, string>;
}

const STATUS_COLOR: Record<Status, string> = {
  done: 'chip--success',
  wip: 'chip--warning',
  todo: 'chip--default',
};

export function CheckinExplorer({
  locale,
  items,
  labels,
}: {
  locale: string;
  items: ExplorerItem[];
  labels: ExplorerLabels;
}) {
  const [groupBy, setGroupBy] = useState<'phase' | 'lesson'>('phase');
  const [status, setStatus] = useState<Status | 'all'>('all');
  const [category, setCategory] = useState<string>('all');

  const groups = useMemo(() => {
    const filtered = items.filter(
      (c) => (status === 'all' || c.status === status) && (category === 'all' || c.category === category),
    );
    const map = new Map<string, ExplorerItem[]>();
    for (const c of filtered) {
      const key = groupBy === 'phase' ? String(c.phase) : c.lesson;
      map.set(key, [...(map.get(key) ?? []), c]);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b, 'en', { numeric: true }));
  }, [items, groupBy, status, category]);

  const groupTitle = (key: string) =>
    groupBy === 'phase' ? labels.phasePrefix[Number(key) - 1] : `${key} · ${labels.lessonNames[key] ?? ''}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-1">
          {(['phase', 'lesson'] as const).map((g) => (
            <Button key={g} size="sm" variant={groupBy === g ? 'primary' : 'secondary'} onPress={() => setGroupBy(g)}>
              {g === 'phase' ? labels.byPhase : labels.byLesson}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1">
          <span className="mr-1 text-sm text-muted">{labels.status}</span>
          {(['all', 'done', 'wip', 'todo'] as const).map((s) => (
            <Button key={s} size="sm" variant={status === s ? 'primary' : 'ghost'} onPress={() => setStatus(s)}>
              {s === 'all' ? labels.all : labels.statusNames[s]}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1">
          <span className="mr-1 text-sm text-muted">{labels.category}</span>
          {['all', ...Object.keys(labels.categoryNames)].map((c) => (
            <Button key={c} size="sm" variant={category === c ? 'primary' : 'ghost'} onPress={() => setCategory(c)}>
              {c === 'all' ? labels.all : labels.categoryNames[c]}
            </Button>
          ))}
        </div>
      </div>

      {groups.length === 0 && <p className="text-muted">—</p>}
      {groups.map(([key, list]) => (
        <section key={key}>
          <h2 className="mb-2 text-lg font-bold text-heading">{groupTitle(key)}</h2>
          <ul className="divide-y divide-separator rounded border border-border bg-surface">
            {list.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/${locale}/checkins/${c.id}/`}
                  className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-surface-tertiary"
                >
                  <span className="w-10 font-mono text-sm text-muted">{c.id}</span>
                  <span className="flex-1 font-medium">{c.title}</span>
                  <span className="text-xs text-muted">{labels.categoryNames[c.category]}</span>
                  {c.flagship && (
                    <span className="chip chip--sm chip--soft chip--accent">
                      <span className="chip__label">★ {labels.flagship}</span>
                    </span>
                  )}
                  <span className={`chip chip--sm chip--soft ${STATUS_COLOR[c.status]}`}>
                    <span className="chip__label">{labels.statusNames[c.status]}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
