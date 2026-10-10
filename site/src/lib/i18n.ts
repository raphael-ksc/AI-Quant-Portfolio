// 語系設定與介面字串（zh-TW：臺灣繁體中文；en-AU：澳洲英文拼法）

export const LOCALES = ['zh-TW', 'en-AU'] as const;
export type Locale = (typeof LOCALES)[number];

export const HTML_LANG: Record<Locale, string> = { 'zh-TW': 'zh-Hant-TW', 'en-AU': 'en-AU' };

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

/** 依語系取標題：英文缺值時退回中文 */
export function pick(locale: Locale, zh: string, en?: string | null): string {
  return locale === 'en-AU' && en ? en : zh;
}

/** ISO 日期 → 顯示格式（中文：2026年10月10日；英文：10 October 2026） */
export function formatDate(locale: Locale, iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(`${iso}T00:00:00Z`);
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
  }).format(d);
}

const zh = {
  siteName: 'AI 量化交易作品集',
  nav: { home: '首頁', checkins: '打卡', lessons: '課程', knowledge: '知識', about: '關於' },
  theme: '主題',
  language: '語言',
  hero: {
    kicker: '宏觀交易員 × 系統化策略',
    title: '把宏觀判斷，變成可以檢驗的系統',
    subtitle:
      '這是我學習 AI 量化交易的公開紀錄：從多資料源數據管線、含交易成本的回測，到趨勢與區間策略、市場狀態判斷與機器學習驗證。每一題都附上方法、結果、風險檢查與限制。',
    ctaCheckins: '查看打卡進度',
    ctaAbout: '關於這個專案',
  },
  stats: { total: '打卡總數', done: '已完成', wip: '進行中', todo: '未開始', flagship: '代表作' },
  sections: {
    flagship: '代表作',
    flagshipNote: '以交易員視角挑選：回測可信度、宏觀事件數據、趨勢跟蹤、市場狀態切換。',
    roadmap: '執行路線',
    roadmapNote: '依優先級分為 6 個階段，每週約 4 小時推進。',
    capabilities: '能力地圖',
    related: '相關打卡',
    notes: '知識筆記',
    requirements: '題目內容',
    meta: '基本資料',
    noNotes: '尚無筆記',
  },
  phases: {
    '1': '地基', '2': '宏觀優勢', '3': '系統化策略', '4': '驗證', '5': '自動化', '6': '課程完成度與選做',
  } as Record<string, string>,
  status: { todo: '未開始', wip: '進行中', done: '已完成' },
  fields: {
    lesson: '課程', category: '主分類', phase: '階段', order: '順序', date: '完成日',
    confidence: '自評理解度', symbols: '標的', tags: '標籤', source: '課件出處', status: '狀態',
  },
  filters: { all: '全部', byPhase: '依階段', byLesson: '依課程', status: '狀態', category: '分類' },
  flagship: '代表作',
  phaseLabel: (n: number) => `第 ${n} 階段`,
  englishPending: '',
  backToList: '← 回到打卡列表',
  notFound: '找不到這個頁面。',
  disclaimer:
    '⚠️ 免責聲明：本網站所有策略分析、回測結果與訊號探討僅供教育與研究用途，不構成投資建議或收益保證。內容僅使用公開資料與課程材料，與作者任職機構無關。',
  footer: '原始碼與完整紀錄：',
  about: {
    title: '關於這個專案',
    sections: [
      {
        heading: '這是什麼',
        body:
          '我是宏觀交易員，正在系統化地補上量化交易技能。這個網站整理我在 AI 量化交易課程中的 24 題實作打卡，目標是把過去依賴經驗的判斷，轉成可以回測、可以驗證、可以重現的流程。',
      },
      {
        heading: '每題的固定結構',
        body:
          '題目要求 → 方法 → 結果（圖表與指標）→ 風險檢查表（資料洩漏、倖存者偏差、過度擬合、交易成本、流動性）→ 限制與心得。主動寫出限制與失敗，比只展示漂亮的報酬曲線更重要。',
      },
      {
        heading: '資料來源',
        body:
          '研究使用 Moomoo OpenAPI（原課程為 QMT，已全面改寫為 Moomoo 版本）；公開重現使用 yfinance，任何人不需帳號即可執行。網站只展示彙總後的圖表與指標，不公開原始行情與財報數據。資料源之間的差異（例如 Moomoo 財報期末日偏移一天）會記錄在知識筆記中。',
      },
      {
        heading: '範圍',
        body: '目前專注於股票市場。外匯與加密貨幣的延伸應用會在之後另外驗證，回測結論不跨市場類推。',
      },
      {
        heading: '技術架構',
        body:
          '打卡內容以 Markdown 撰寫，由 Python 腳本驗證並轉成 JSON；網站使用 Next.js 靜態匯出、HeroUI 與 Tailwind CSS，透過 GitHub Actions 自動部署到 GitHub Pages。',
      },
    ],
  },
};

export type Dict = typeof zh;

const en: Dict = {
  siteName: 'AI Quant Portfolio',
  nav: { home: 'Home', checkins: 'Check-ins', lessons: 'Lessons', knowledge: 'Knowledge', about: 'About' },
  theme: 'Theme',
  language: 'Language',
  hero: {
    kicker: 'Macro trader × systematic strategies',
    title: 'Turning macro judgement into testable systems',
    subtitle:
      'A public record of my AI quantitative trading studies — from multi-source data pipelines and cost-aware backtests to trend and range strategies, regime detection and machine-learning validation. Every check-in documents its method, results, risk checks and limitations.',
    ctaCheckins: 'View progress',
    ctaAbout: 'About this project',
  },
  stats: { total: 'Check-ins', done: 'Completed', wip: 'In progress', todo: 'Not started', flagship: 'Flagship' },
  sections: {
    flagship: 'Flagship work',
    flagshipNote:
      "Chosen from a trader's perspective: backtest credibility, macro event data, trend following and regime switching.",
    roadmap: 'Roadmap',
    roadmapNote: 'Six phases ordered by priority, progressed at roughly four hours a week.',
    capabilities: 'Capability map',
    related: 'Related check-ins',
    notes: 'Knowledge notes',
    requirements: 'Content',
    meta: 'Details',
    noNotes: 'No notes yet',
  },
  phases: {
    '1': 'Foundations', '2': 'Macro edge', '3': 'Systematic strategies', '4': 'Validation',
    '5': 'Automation', '6': 'Course completion & electives',
  },
  status: { todo: 'Not started', wip: 'In progress', done: 'Completed' },
  fields: {
    lesson: 'Lesson', category: 'Category', phase: 'Phase', order: 'Order', date: 'Completed',
    confidence: 'Self-rated understanding', symbols: 'Symbols', tags: 'Tags', source: 'Course source',
    status: 'Status',
  },
  filters: { all: 'All', byPhase: 'By phase', byLesson: 'By lesson', status: 'Status', category: 'Category' },
  flagship: 'Flagship',
  phaseLabel: (n: number) => `Phase ${n}`,
  englishPending: 'English version coming soon — showing the Traditional Chinese original.',
  backToList: '← Back to check-ins',
  notFound: 'Page not found.',
  disclaimer:
    "⚠️ Disclaimer: all strategy analysis, backtest results and signal discussion on this site are for educational and research purposes only and do not constitute investment advice or any guarantee of returns. Content uses only public data and course materials and is unrelated to the author's employer.",
  footer: 'Source code and full records: ',
  about: {
    title: 'About this project',
    sections: [
      {
        heading: 'What this is',
        body:
          "I'm a macro trader systematically adding quantitative trading skills. This site collects my 24 hands-on check-ins from an AI quantitative trading course, with one goal: turning judgement built on experience into processes that can be backtested, validated and reproduced.",
      },
      {
        heading: 'Structure of every check-in',
        body:
          'Requirements → method → results (charts and metrics) → risk checklist (data leakage, survivorship bias, overfitting, transaction costs, liquidity) → limitations and reflections. Stating limitations and failures openly matters more than showing a flattering equity curve.',
      },
      {
        heading: 'Data sources',
        body:
          'Research uses the Moomoo OpenAPI (the original course used QMT; everything has been rewritten for Moomoo). Public reproduction uses yfinance, so anyone can run it without an account. The site shows only aggregated charts and metrics — raw market and financial statement data are not published. Differences between sources (such as Moomoo financial period-end dates being one day early) are documented in the knowledge notes.',
      },
      {
        heading: 'Scope',
        body:
          'The current focus is equities. FX and crypto extensions will be validated separately later; backtest conclusions are not generalised across markets.',
      },
      {
        heading: 'Architecture',
        body:
          'Check-ins are written in Markdown, validated and converted to JSON by a Python script. The site is a Next.js static export styled with HeroUI and Tailwind CSS, deployed automatically to GitHub Pages via GitHub Actions.',
      },
    ],
  },
};

const DICTS: Record<Locale, Dict> = { 'zh-TW': zh, 'en-AU': en };

export function getDict(locale: Locale): Dict {
  return DICTS[locale];
}
