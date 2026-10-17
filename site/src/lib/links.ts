// Markdown 內文的相對路徑改寫：打卡與筆記在 repo 裡用相對路徑插圖、連結（GitHub 上可正常顯示），
// 但網站頁面的網址是 /<locale>/checkins/<id>/，相對路徑會解析錯位置，所以在顯示時改寫：
//   圖片                      → 網站上的實際路徑（ensure-data.mjs 會把 outputs/figures 複製到 public/）
//   其他打卡的 checkin.md      → 網站上該題的頁面
//   其他檔案（.md、.json、.py…）→ GitHub repo 裡的檔案
// 純函式、不依賴 Next.js，用 node --test 測試（tests/links.test.mts）。

export const REPO_BLOB = 'https://github.com/raphael-ksc/AI-Quant-Portfolio/blob/main';
export const REPO_TREE = 'https://github.com/raphael-ksc/AI-Quant-Portfolio/tree/main';

const ABSOLUTE = /^([a-z][a-z0-9+.-]*:|\/\/|\/|#)/i;
const CHECKIN_MD = /(?:^|\/)lessons\/[^/]+\/(C\d{2})-[^/]+\/checkin(?:\.en-AU)?\.md$/;

/** 把 baseDir 與相對路徑合併並正規化（處理 ./ 與 ../）；超出 repo 根目錄時回傳 null。 */
export function joinRepoPath(baseDir: string, relative: string): string | null {
  const parts = baseDir.split('/').filter(Boolean);
  for (const seg of relative.split('/')) {
    if (seg === '' || seg === '.') continue;
    if (seg === '..') {
      if (parts.length === 0) return null;
      parts.pop();
    } else {
      parts.push(seg);
    }
  }
  return parts.join('/');
}

export interface ResolveContext {
  baseDir: string;   // 這份 Markdown 所在的 repo 目錄，例如 lessons/L05-backtrader/C13-backtrader-backtest
  basePath: string;  // 網站部署的子路徑，例如 /AI-Quant-Portfolio（本機開發為空字串）
  locale: string;    // zh-TW / en-AU
}

/** 改寫單一網址；kind 為 'image'（<img src>）或 'link'（<a href>）。 */
export function resolveUrl(url: string, kind: 'image' | 'link', ctx: ResolveContext): string {
  if (!url || ABSOLUTE.test(url)) return url;
  const [pathPart, hash = ''] = url.split('#', 2);
  const anchor = hash ? `#${hash}` : '';
  const isDir = pathPart.endsWith('/');
  const target = joinRepoPath(ctx.baseDir, pathPart);
  if (target === null) return url;

  if (kind === 'image') return `${ctx.basePath}/${target}`;
  const checkin = target.match(CHECKIN_MD);
  if (checkin) return `${ctx.basePath}/${ctx.locale}/checkins/${checkin[1]}/${anchor}`;
  return `${isDir || target === '' ? REPO_TREE : REPO_BLOB}/${target}${isDir ? '/' : ''}${anchor}`;
}
