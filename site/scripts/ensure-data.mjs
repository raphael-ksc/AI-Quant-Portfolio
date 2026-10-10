// 建置前準備：
// 1. 檢查 site/data/*.json（由 scripts/build_manifest.py 產生），缺少時提示並中止
// 2. 把各題 outputs/figures 的圖檔複製到 public/，網站才能以相同路徑讀取
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const siteDir = join(dirname(fileURLToPath(import.meta.url)), '..');
const repoDir = join(siteDir, '..');
const dataDir = join(siteDir, 'data');
const required = ['checkins.json', 'lessons.json', 'knowledge.json'];
const missing = required.filter((f) => !existsSync(join(dataDir, f)));

if (missing.length) {
  console.error(`缺少 ${missing.join(', ')}。請先在 Project 根目錄執行：`);
  console.error('  .venv\\Scripts\\python.exe scripts\\build_manifest.py');
  process.exit(1);
}

const publicLessons = join(siteDir, 'public', 'lessons');
rmSync(publicLessons, { recursive: true, force: true });

const { checkins } = JSON.parse(readFileSync(join(dataDir, 'checkins.json'), 'utf-8'));
let copied = 0;
for (const c of checkins) {
  for (const rel of c.figures) {
    const dest = join(siteDir, 'public', rel);
    mkdirSync(dirname(dest), { recursive: true });
    copyFileSync(join(repoDir, rel), dest);
    copied += 1;
  }
}
console.log(`資料檢查通過；已複製 ${copied} 張圖檔`);
