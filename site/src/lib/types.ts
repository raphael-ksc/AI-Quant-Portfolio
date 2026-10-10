// 對應 scripts/build_manifest.py 輸出的 JSON 結構

export type Status = 'todo' | 'wip' | 'done';

export interface Checkin {
  id: string;
  lesson: string;
  title: string;
  title_en: string;
  category: string;
  knowledge: string[];
  tags: string[];
  symbols: string[];
  status: Status;
  phase: number;
  order: number;
  flagship: boolean;
  date: string | null;
  confidence: number | null;
  source: string;
  path: string;
  figures: string[];
  metrics: string | null;
  body: string;
  body_en: string | null;
}

export interface Stats {
  total: number;
  by_status: Record<Status, number>;
  by_phase: Record<string, number>;
  flagship: string[];
}

export interface Lesson {
  id: string;
  title: string;
  title_en: string;
  path: string;
}

export interface Note {
  slug: string;
  title: string;
  title_en: string;
  date: string | null;
  tags: string[];
  related: string[];
  path: string;
  body: string;
  body_en: string | null;
}

export interface Category {
  id: string;
  title: string;
  title_en: string;
  description: string;
  description_en: string;
  notes: Note[];
}
