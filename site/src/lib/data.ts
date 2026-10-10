// 建置時讀取 site/data/*.json（由 scripts/build_manifest.py 產生），只在 Server Component 使用
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { Category, Checkin, Lesson, Stats } from './types';

const DATA_DIR = join(process.cwd(), 'data');

function load<T>(name: string): T {
  return JSON.parse(readFileSync(join(DATA_DIR, name), 'utf-8')) as T;
}

export function getCheckins(): { checkins: Checkin[]; stats: Stats } {
  return load('checkins.json');
}

export function getCheckin(id: string): Checkin | undefined {
  return getCheckins().checkins.find((c) => c.id === id);
}

export function getLessons(): Lesson[] {
  return load<{ lessons: Lesson[] }>('lessons.json').lessons;
}

export function getCategories(): Category[] {
  return load<{ categories: Category[] }>('knowledge.json').categories;
}

export function getCategory(id: string): Category | undefined {
  return getCategories().find((c) => c.id === id);
}
