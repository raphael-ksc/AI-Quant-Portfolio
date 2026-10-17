"""掃描 git 追蹤的檔案，找出疑似密碼、金鑰等敏感資訊；發現即以結束碼 1 離開。

本 repo 公開展示，CI 在部署前執行此檢查（CLAUDE.md 第 10.4 節）。
用法：python scripts/scan_secrets.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 「關鍵字 = 值」且值看起來像真的密碼（至少 6 個非空白字元，排除佔位符）
ASSIGNMENT = re.compile(
    r'(?i)(?<![a-z])(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|unlock[_-]?pwd)\w*\s*[:=]\s*'
    r'["\']?(?P<value>[^\s"\'#]{6,})'
)
PATTERNS = {
    'GitHub token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}'),
    'AWS access key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'Private key': re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'OpenAI/Anthropic key': re.compile(r'\bsk-(ant-)?[A-Za-z0-9_-]{20,}'),
}
# 值是程式運算式（例：os.environ["X"]、getenv("X")、config.password）時不視為硬編碼密碼
CODE_EXPR = re.compile(r'^[A-Za-z_][\w.]*([\(\[]|$)')
PLACEHOLDERS = {'your_password', 'changeme', 'xxxxxx', '********', 'example', 'placeholder'}
FORBIDDEN_FILES = re.compile(r'(^|/)\.env$|\.pem$|\.p12$|\.key$')
SKIP_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.woff', '.woff2'}
SKIP_FILES = {'package-lock.json', 'scripts/scan_secrets.py', 'tests/test_scan_secrets.py'}


def tracked_files() -> list[str]:
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    return [p for p in out.stdout.decode('utf-8').split('\0') if p]


def scan_text(text: str) -> list[str]:
    """回傳一段文字中命中的規則名稱（每行一筆，附行號）。"""
    hits = []
    for no, line in enumerate(text.splitlines(), start=1):
        m = ASSIGNMENT.search(line)
        if m:
            value = m.group('value').rstrip(',;)')  # 函式參數 password=self.password, 的結尾符號
            is_code = bool(CODE_EXPR.match(value)) and any(ch in value for ch in '.([')
            if (value.lower() not in PLACEHOLDERS and not is_code
                    and not value.startswith(('$', '{', '<', '%'))):
                hits.append(f'第 {no} 行：疑似 {m.group(1)} 賦值')
        hits += [f'第 {no} 行：疑似 {name}' for name, p in PATTERNS.items() if p.search(line)]
    return hits


def main() -> int:
    problems = []
    for rel in tracked_files():
        if FORBIDDEN_FILES.search(rel):
            problems.append(f'{rel}：不應提交此類檔案')
            continue
        if Path(rel).suffix.lower() in SKIP_SUFFIXES or rel in SKIP_FILES or rel.endswith('/package-lock.json'):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        problems += [f'{rel}：{h}' for h in scan_text(text)]

    if problems:
        print('發現疑似敏感資訊，請確認後再提交：', file=sys.stderr)
        for p in problems:
            print(f'  - {p}', file=sys.stderr)
        return 1
    print('敏感資訊掃描通過')
    return 0


if __name__ == '__main__':
    sys.exit(main())
