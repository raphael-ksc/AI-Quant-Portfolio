"""掃描 lessons/ 與 knowledge/ 的 Markdown front-matter，驗證後輸出網站用 JSON。

輸出（預設 site/data/）：
    checkins.json   24 題打卡的元資料與內文（中文、英文）
    lessons.json    課程清單
    knowledge.json  知識分類與筆記

用法：
    python scripts/build_manifest.py              # 驗證並輸出
    python scripts/build_manifest.py --check      # 只驗證，不輸出
任何驗證錯誤都會列出並以結束碼 1 離開，讓 CI 擋下部署。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

CATEGORIES = (
    'data-engineering', 'fundamentals', 'technical-analysis', 'backtesting',
    'strategies', 'machine-learning', 'ai-agents', 'risk-management',
)
STATUSES = ('todo', 'wip', 'done')
REQUIRED_CHECKIN = (
    'id', 'lesson', 'title', 'title_en', 'category', 'knowledge', 'tags',
    'status', 'phase', 'order', 'flagship', 'source',
)
REQUIRED_LESSON = ('id', 'title', 'title_en')
REQUIRED_CATEGORY = ('id', 'title', 'title_en', 'description', 'description_en')
REQUIRED_NOTE = ('title', 'title_en', 'category', 'date')

FM_RE = re.compile(r'\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z', re.S)
CHECKIN_ID_RE = re.compile(r'^C\d{2}$')
LESSON_ID_RE = re.compile(r'^L\d{2}$')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
EN_SUFFIX = '.en-AU.md'


class ManifestError(Exception):
    """收集所有驗證錯誤後一次拋出。"""

    def __init__(self, errors: list[str]):
        super().__init__('\n'.join(errors))
        self.errors = errors


def parse_front_matter(path: Path) -> tuple[dict, str]:
    """拆出 YAML front-matter 與內文；沒有 front-matter 時拋 ValueError。"""
    text = path.read_text(encoding='utf-8')
    m = FM_RE.match(text)
    if not m:
        raise ValueError('缺少 front-matter')
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, 'problem_mark', None)
        line = f'第 {mark.line + 2} 行' if mark else ''
        raise ValueError(f'front-matter YAML 格式錯誤 {line}（含冒號的值請加引號）') from e
    if not isinstance(meta, dict):
        raise ValueError('front-matter 不是 key-value 格式')
    return meta, m.group(2).lstrip('\n')


def normalise_date(value) -> str | None:
    """YAML 會把 2026-10-10 解析成 date 物件；統一轉回 ISO 字串。"""
    if value is None or value == '':
        return None
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def missing_fields(meta: dict, required: tuple[str, ...]) -> list[str]:
    return [k for k in required if k not in meta or meta[k] in (None, '')]


def load_lessons(root: Path, errors: list[str]) -> dict[str, dict]:
    lessons = {}
    for readme in sorted(root.glob('lessons/L*/README.md')):
        where = rel(readme, root)
        try:
            meta, _ = parse_front_matter(readme)
        except ValueError as e:
            errors.append(f'{where}: {e}')
            continue
        for k in missing_fields(meta, REQUIRED_LESSON):
            errors.append(f'{where}: 缺少欄位 {k}')
        lid = meta.get('id')
        if lid and not readme.parent.name.startswith(f'{lid}-'):
            errors.append(f'{where}: id {lid} 與資料夾名稱 {readme.parent.name} 不符')
        if lid:
            lessons[lid] = {
                'id': lid,
                'title': meta.get('title'),
                'title_en': meta.get('title_en'),
                'path': rel(readme.parent, root),
            }
    return lessons


def validate_checkin(meta: dict, cdir: Path, root: Path, today: dt.date) -> list[str]:
    """單題打卡的欄位驗證；回傳錯誤訊息清單。"""
    where = rel(cdir / 'checkin.md', root)
    errs = [f'{where}: 缺少欄位 {k}' for k in missing_fields(meta, REQUIRED_CHECKIN)]

    cid = meta.get('id')
    if cid is not None:
        if not CHECKIN_ID_RE.match(str(cid)):
            errs.append(f'{where}: id 格式錯誤（應為 C01–C99）：{cid}')
        elif not cdir.name.startswith(f'{cid}-'):
            errs.append(f'{where}: id {cid} 與資料夾名稱 {cdir.name} 不符')
    lesson = meta.get('lesson')
    if lesson is not None and not cdir.parent.name.startswith(f'{lesson}-'):
        errs.append(f'{where}: lesson {lesson} 與上層資料夾 {cdir.parent.name} 不符')

    if meta.get('category') not in (None, '') and meta['category'] not in CATEGORIES:
        errs.append(f'{where}: category 不合法：{meta["category"]}')
    knowledge = meta.get('knowledge') or []
    if not isinstance(knowledge, list):
        errs.append(f'{where}: knowledge 必須是清單')
    else:
        errs += [f'{where}: knowledge 不合法：{k}' for k in knowledge if k not in CATEGORIES]
        if meta.get('category') and meta['category'] not in knowledge:
            errs.append(f'{where}: knowledge 必須包含主分類 {meta["category"]}')
    for key in ('tags', 'symbols'):
        if meta.get(key) is not None and not isinstance(meta[key], list):
            errs.append(f'{where}: {key} 必須是清單')

    status = meta.get('status')
    if status is not None and status not in STATUSES:
        errs.append(f'{where}: status 不合法：{status}')
    if not isinstance(meta.get('phase'), int) or not 1 <= meta.get('phase', 0) <= 6:
        errs.append(f'{where}: phase 必須是 1–6 的整數')
    if not isinstance(meta.get('order'), int) or meta.get('order', 0) < 1:
        errs.append(f'{where}: order 必須是正整數')
    if not isinstance(meta.get('flagship'), bool):
        errs.append(f'{where}: flagship 必須是 true / false')

    date = normalise_date(meta.get('date'))
    if date is not None:
        if not DATE_RE.match(date):
            errs.append(f'{where}: date 格式應為 YYYY-MM-DD：{date}')
        elif dt.date.fromisoformat(date) > today:
            errs.append(f'{where}: date 不可晚於今天（記錄實際完成日）：{date}')
    confidence = meta.get('confidence')
    if confidence is not None and (not isinstance(confidence, int) or not 1 <= confidence <= 5):
        errs.append(f'{where}: confidence 必須是 1–5 的整數')
    if status == 'done':
        if date is None:
            errs.append(f'{where}: status 為 done 時必須填 date（完成日）')
        if confidence is None:
            errs.append(f'{where}: status 為 done 時必須填 confidence')

    outputs = meta.get('outputs') or {}
    if not isinstance(outputs, dict):
        errs.append(f'{where}: outputs 格式錯誤')
        outputs = {}
    for fig in outputs.get('figures') or []:
        if not (cdir / fig).is_file():
            errs.append(f'{where}: 找不到圖檔 {fig}')
    metrics = outputs.get('metrics')
    if metrics and not (cdir / metrics).is_file():
        errs.append(f'{where}: 找不到指標檔 {metrics}')
    return errs


INLINE_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)')
ABSOLUTE_URL_RE = re.compile(r'^([a-z][a-z0-9+.-]*:|//|/)', re.I)


def inline_image_errors(where: str, bodies: list[str], figures: list[str]) -> list[str]:
    """內文用相對路徑插的圖，必須列在 outputs.figures：網站建置時只會複製這些圖到 public/。"""
    listed = {str(Path(p).as_posix()).removeprefix('./') for p in figures}
    errs = []
    for body in bodies:
        for src in INLINE_IMAGE_RE.findall(body):
            if ABSOLUTE_URL_RE.match(src):
                continue
            if src.removeprefix('./') not in listed:
                errs.append(f'{where}: 內文圖片 {src} 沒有列在 outputs.figures（網站上會顯示不出來）')
    return sorted(set(errs))


def load_checkins(root: Path, lessons: dict, errors: list[str], today: dt.date) -> list[dict]:
    checkins = []
    for f in sorted(root.glob('lessons/L*/C*/checkin.md')):
        cdir = f.parent
        try:
            meta, body = parse_front_matter(f)
        except ValueError as e:
            errors.append(f'{rel(f, root)}: {e}')
            continue
        errs = validate_checkin(meta, cdir, root, today)
        if meta.get('lesson') and meta['lesson'] not in lessons:
            errs.append(f'{rel(f, root)}: 找不到課程 {meta["lesson"]} 的 README')
        errors += errs

        en_file = cdir / f'checkin{EN_SUFFIX}'
        body_en = None
        if en_file.is_file():
            text = en_file.read_text(encoding='utf-8')
            m = FM_RE.match(text)
            body_en = (m.group(2) if m else text).lstrip('\n')

        outputs = meta.get('outputs') if isinstance(meta.get('outputs'), dict) else {}
        errors += inline_image_errors(rel(f, root), [body, body_en or ''], outputs.get('figures') or [])
        base = rel(cdir, root)
        checkins.append({
            'id': meta.get('id'),
            'lesson': meta.get('lesson'),
            'title': meta.get('title'),
            'title_en': meta.get('title_en'),
            'category': meta.get('category'),
            'knowledge': meta.get('knowledge') or [],
            'tags': meta.get('tags') or [],
            'symbols': meta.get('symbols') or [],
            'status': meta.get('status'),
            'phase': meta.get('phase'),
            'order': meta.get('order'),
            'flagship': meta.get('flagship'),
            'date': normalise_date(meta.get('date')),
            'confidence': meta.get('confidence'),
            'source': meta.get('source'),
            'path': base,
            'figures': [f'{base}/{p}' for p in (outputs.get('figures') or [])],
            'metrics': f'{base}/{outputs["metrics"]}' if outputs.get('metrics') else None,
            'body': body,
            'body_en': body_en,
        })

    for key in ('id', 'order'):
        seen: dict = {}
        for c in checkins:
            v = c[key]
            if v is None:
                continue
            if v in seen:
                errors.append(f'{key} 重複：{v}（{seen[v]} 與 {c["path"]}）')
            seen[v] = c['path']
    checkins.sort(key=lambda c: (c['order'] if isinstance(c['order'], int) else 999, str(c['id'])))
    return checkins


def load_knowledge(root: Path, checkin_ids: set, errors: list[str]) -> list[dict]:
    categories = []
    for key in CATEGORIES:
        readme = root / 'knowledge' / key / 'README.md'
        where = rel(readme, root) if readme.exists() else f'knowledge/{key}/README.md'
        if not readme.is_file():
            errors.append(f'{where}: 檔案不存在')
            continue
        try:
            meta, _ = parse_front_matter(readme)
        except ValueError as e:
            errors.append(f'{where}: {e}')
            continue
        errors += [f'{where}: 缺少欄位 {k}' for k in missing_fields(meta, REQUIRED_CATEGORY)]
        if meta.get('id') != key:
            errors.append(f'{where}: id 應為 {key}')

        notes = []
        for note in sorted(readme.parent.glob('*.md')):
            if note.name == 'README.md' or note.name.endswith(EN_SUFFIX):
                continue
            nwhere = rel(note, root)
            try:
                nmeta, nbody = parse_front_matter(note)
            except ValueError as e:
                errors.append(f'{nwhere}: {e}')
                continue
            errors += [f'{nwhere}: 缺少欄位 {k}' for k in missing_fields(nmeta, REQUIRED_NOTE)]
            if nmeta.get('category') not in (None, key):
                errors.append(f'{nwhere}: category 應為 {key}')
            related = nmeta.get('related') or []
            errors += [f'{nwhere}: related 找不到打卡 {r}' for r in related if r not in checkin_ids]
            en_file = note.with_name(note.stem + EN_SUFFIX)
            en_body = en_file.read_text(encoding='utf-8') if en_file.is_file() else ''
            errors += inline_image_errors(nwhere, [nbody, en_body], [])  # 筆記的圖片不會被複製到網站
            notes.append({
                'slug': note.stem,
                'title': nmeta.get('title'),
                'title_en': nmeta.get('title_en'),
                'date': normalise_date(nmeta.get('date')),
                'tags': nmeta.get('tags') or [],
                'related': related,
                'path': nwhere,
                'body': nbody,
                'body_en': en_file.read_text(encoding='utf-8') if en_file.is_file() else None,
            })
        categories.append({
            'id': key,
            'title': meta.get('title'),
            'title_en': meta.get('title_en'),
            'description': meta.get('description'),
            'description_en': meta.get('description_en'),
            'notes': notes,
        })
    return categories


def build(root: Path, today: dt.date | None = None) -> dict:
    """讀取並驗證整個 repo；有錯誤時拋 ManifestError。"""
    today = today or dt.date.today()
    errors: list[str] = []
    lessons = load_lessons(root, errors)
    checkins = load_checkins(root, lessons, errors, today)
    knowledge = load_knowledge(root, {c['id'] for c in checkins}, errors)
    if errors:
        raise ManifestError(errors)

    stats = {
        'total': len(checkins),
        'by_status': {s: sum(c['status'] == s for c in checkins) for s in STATUSES},
        'by_phase': {str(p): sum(c['phase'] == p for c in checkins) for p in range(1, 7)},
        'flagship': [c['id'] for c in checkins if c['flagship']],
    }
    return {
        'lessons': sorted(lessons.values(), key=lambda x: x['id']),
        'checkins': checkins,
        'knowledge': knowledge,
        'stats': stats,
    }


def write_outputs(manifest: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        'checkins.json': {'checkins': manifest['checkins'], 'stats': manifest['stats']},
        'lessons.json': {'lessons': manifest['lessons']},
        'knowledge.json': {'categories': manifest['knowledge']},
    }
    for name, data in files.items():
        (out_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                                    encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, default=None, help='輸出目錄（預設 <root>/site/data）')
    parser.add_argument('--check', action='store_true', help='只驗證，不輸出檔案')
    args = parser.parse_args(argv)

    try:
        manifest = build(args.root)
    except ManifestError as e:
        print(f'驗證失敗，共 {len(e.errors)} 個錯誤：', file=sys.stderr)
        for err in e.errors:
            print(f'  - {err}', file=sys.stderr)
        return 1

    s = manifest['stats']
    print(f'驗證通過：{s["total"]} 題打卡，狀態 {s["by_status"]}，代表作 {s["flagship"]}')
    if not args.check:
        out = args.out or args.root / 'site' / 'data'
        write_outputs(manifest, out)
        print(f'已輸出至 {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
