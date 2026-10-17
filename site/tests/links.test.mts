// 相對路徑改寫的單元測試：node --test（Node 24 原生支援 TypeScript 型別剝除）
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REPO_BLOB, REPO_TREE, joinRepoPath, resolveUrl } from '../src/lib/links.ts';

const C13 = { baseDir: 'lessons/L05-backtrader/C13-backtrader-backtest', basePath: '/AI-Quant-Portfolio', locale: 'zh-TW' };
const NOTE = { baseDir: 'knowledge/backtesting', basePath: '/AI-Quant-Portfolio', locale: 'en-AU' };

test('joinRepoPath 處理 ./ 與 ../', () => {
  assert.equal(joinRepoPath('a/b', './c/d.png'), 'a/b/c/d.png');
  assert.equal(joinRepoPath('a/b', '../../x.md'), 'x.md');
  assert.equal(joinRepoPath('a', '../../x.md'), null);
});

test('內文圖片改寫成網站路徑', () => {
  assert.equal(resolveUrl('outputs/figures/c13_returns_2025.png', 'image', C13),
    '/AI-Quant-Portfolio/lessons/L05-backtrader/C13-backtrader-backtest/outputs/figures/c13_returns_2025.png');
});

test('本機開發（basePath 為空）時圖片仍是根目錄絕對路徑', () => {
  assert.equal(resolveUrl('outputs/figures/a.png', 'image', { ...C13, basePath: '' }),
    '/lessons/L05-backtrader/C13-backtrader-backtest/outputs/figures/a.png');
});

test('非圖片檔連到 GitHub', () => {
  assert.equal(resolveUrl('outputs/metrics.json', 'link', C13),
    `${REPO_BLOB}/lessons/L05-backtrader/C13-backtrader-backtest/outputs/metrics.json`);
  assert.equal(resolveUrl('../../../config/costs.yaml', 'link', C13), `${REPO_BLOB}/config/costs.yaml`);
});

test('其他打卡的 checkin.md 連到網站頁面（保留語系）', () => {
  assert.equal(resolveUrl('../../lessons/L05-backtrader/C13-backtrader-backtest/checkin.md', 'link', NOTE),
    '/AI-Quant-Portfolio/en-AU/checkins/C13/');
  assert.equal(resolveUrl('../../lessons/L04-data-pipeline/C06-market-data-collection/checkin.en-AU.md#結果', 'link', NOTE),
    '/AI-Quant-Portfolio/en-AU/checkins/C06/#結果');
});

test('資料夾連到 GitHub tree', () => {
  assert.equal(resolveUrl('../data-engineering/', 'link', NOTE), `${REPO_TREE}/knowledge/data-engineering/`);
});

test('絕對網址、站內路徑與錨點不改', () => {
  for (const url of ['https://www.sec.gov/x', '//cdn.x/y.png', '/AI-Quant-Portfolio/zh-TW/', '#方法', 'mailto:a@b.c']) {
    assert.equal(resolveUrl(url, 'link', C13), url);
    assert.equal(resolveUrl(url, 'image', C13), url);
  }
});

test('超出 repo 根目錄的路徑維持原樣', () => {
  assert.equal(resolveUrl('../../../../../x.png', 'image', C13), '../../../../../x.png');
});
