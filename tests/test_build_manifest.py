"""build_manifest.py 單元測試：用 tmp_path 建立迷你 repo，逐一驗證各種錯誤情境。"""
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import build_manifest as bm  # noqa: E402

TODAY = dt.date(2026, 10, 10)

CHECKIN_FM = {
    'id': 'C01',
    'lesson': 'L01',
    'title': '測試題',
    'title_en': 'Test Check-in',
    'category': 'backtesting',
    'knowledge': '[backtesting]',
    'tags': '[MACD]',
    'symbols': '[]',
    'status': 'todo',
    'phase': '1',
    'order': '1',
    'flagship': 'false',
    'date': '',
    'confidence': '',
    'source': 'course.pdf p.1',
}


def write_fm(path: Path, fields: dict, body: str = '# 內文\n') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{k}: {v}' for k, v in fields.items()]
    path.write_text('---\n' + '\n'.join(lines) + '\n---\n\n' + body, encoding='utf-8')


def make_repo(root: Path, checkins: list[dict] | None = None) -> Path:
    """建立一個最小但合法的 repo 結構。"""
    write_fm(root / 'lessons/L01-test/README.md',
             {'id': 'L01', 'title': '測試課', 'title_en': 'Test Lesson'})
    for key in bm.CATEGORIES:
        write_fm(root / f'knowledge/{key}/README.md',
                 {'id': key, 'title': key, 'title_en': key,
                  'description': '說明', 'description_en': 'desc'})
    for i, overrides in enumerate(checkins or [{}], start=1):
        fields = {**CHECKIN_FM, 'id': f'C{i:02d}', 'order': str(i), **overrides}
        cid = fields['id']
        write_fm(root / f'lessons/L01-test/{cid}-demo/checkin.md', fields)
    return root


def errors_of(root: Path) -> list[str]:
    with pytest.raises(bm.ManifestError) as exc:
        bm.build(root, today=TODAY)
    return exc.value.errors


def assert_error(root: Path, fragment: str) -> None:
    errs = errors_of(root)
    assert any(fragment in e for e in errs), errs


# ---------- 正常情境 ----------

def test_valid_repo_builds(tmp_path):
    m = bm.build(make_repo(tmp_path), today=TODAY)
    assert m['stats']['total'] == 1
    c = m['checkins'][0]
    assert c['id'] == 'C01' and c['status'] == 'todo' and c['date'] is None
    assert c['path'] == 'lessons/L01-test/C01-demo'
    assert m['lessons'][0]['title_en'] == 'Test Lesson'
    assert len(m['knowledge']) == len(bm.CATEGORIES)


def test_done_with_date_and_confidence(tmp_path):
    root = make_repo(tmp_path, [{'status': 'done', 'date': '2026-10-09', 'confidence': '4'}])
    c = bm.build(root, today=TODAY)['checkins'][0]
    assert c['date'] == '2026-10-09' and c['confidence'] == 4


def test_sorted_by_order(tmp_path):
    root = make_repo(tmp_path, [{'order': '2'}, {'order': '1'}])
    ids = [c['id'] for c in bm.build(root, today=TODAY)['checkins']]
    assert ids == ['C02', 'C01']


def test_english_body_loaded(tmp_path):
    root = make_repo(tmp_path)
    (root / 'lessons/L01-test/C01-demo/checkin.en-AU.md').write_text('# English\n', encoding='utf-8')
    assert bm.build(root, today=TODAY)['checkins'][0]['body_en'] == '# English\n'


def test_outputs_existing_files_pass(tmp_path):
    root = make_repo(tmp_path)
    cdir = root / 'lessons/L01-test/C01-demo'
    (cdir / 'outputs/figures').mkdir(parents=True)
    (cdir / 'outputs/figures/eq.png').write_bytes(b'png')
    (cdir / 'outputs/metrics.json').write_text('{}', encoding='utf-8')
    text = (cdir / 'checkin.md').read_text(encoding='utf-8').replace(
        'source: course.pdf p.1',
        'source: course.pdf p.1\noutputs:\n  figures: [outputs/figures/eq.png]\n  metrics: outputs/metrics.json')
    (cdir / 'checkin.md').write_text(text, encoding='utf-8')
    c = bm.build(root, today=TODAY)['checkins'][0]
    assert c['figures'] == ['lessons/L01-test/C01-demo/outputs/figures/eq.png']
    assert c['metrics'] == 'lessons/L01-test/C01-demo/outputs/metrics.json'


def test_inline_images_must_be_listed_in_figures():
    figures = ['outputs/figures/eq.png']
    ok = '![淨值](outputs/figures/eq.png) ![外部](https://x.org/a.png) ![站內](/logo.png) ![點](./outputs/figures/eq.png)'
    assert bm.inline_image_errors('c.md', [ok], figures) == []
    errs = bm.inline_image_errors('c.md', ['![漏列](outputs/figures/dd.png)'], figures)
    assert len(errs) == 1 and 'outputs/figures/dd.png' in errs[0]


def test_write_outputs(tmp_path):
    m = bm.build(make_repo(tmp_path / 'repo'), today=TODAY)
    bm.write_outputs(m, tmp_path / 'out')
    data = json.loads((tmp_path / 'out/checkins.json').read_text(encoding='utf-8'))
    assert data['checkins'][0]['title'] == '測試題'
    assert (tmp_path / 'out/lessons.json').is_file()
    assert (tmp_path / 'out/knowledge.json').is_file()


# ---------- 錯誤情境 ----------

@pytest.mark.parametrize('field', ['title', 'title_en', 'category', 'status', 'source'])
def test_missing_required_field(tmp_path, field):
    assert_error(make_repo(tmp_path, [{field: ''}]), f'缺少欄位 {field}')


def test_invalid_category(tmp_path):
    assert_error(make_repo(tmp_path, [{'category': 'astrology'}]), 'category 不合法')


def test_invalid_knowledge(tmp_path):
    assert_error(make_repo(tmp_path, [{'knowledge': '[backtesting, astrology]'}]), 'knowledge 不合法')


def test_knowledge_must_include_category(tmp_path):
    assert_error(make_repo(tmp_path, [{'knowledge': '[strategies]'}]), '必須包含主分類')


def test_invalid_status(tmp_path):
    assert_error(make_repo(tmp_path, [{'status': 'finished'}]), 'status 不合法')


def test_done_requires_date(tmp_path):
    assert_error(make_repo(tmp_path, [{'status': 'done', 'confidence': '3'}]), '必須填 date')


def test_done_requires_confidence(tmp_path):
    assert_error(make_repo(tmp_path, [{'status': 'done', 'date': '2026-10-01'}]), '必須填 confidence')


def test_future_date_rejected(tmp_path):
    assert_error(make_repo(tmp_path, [{'date': '2026-12-31'}]), '不可晚於今天')


def test_bad_date_format(tmp_path):
    assert_error(make_repo(tmp_path, [{'date': '10/10/2026'}]), 'YYYY-MM-DD')


@pytest.mark.parametrize('value', ['0', '6', '3.5'])
def test_confidence_range(tmp_path, value):
    assert_error(make_repo(tmp_path, [{'confidence': value}]), 'confidence 必須是 1–5')


@pytest.mark.parametrize('field,value,msg', [
    ('phase', '7', 'phase 必須是'),
    ('order', '0', 'order 必須是'),
    ('flagship', 'maybe', 'flagship 必須是'),
])
def test_phase_order_flagship(tmp_path, field, value, msg):
    assert_error(make_repo(tmp_path, [{field: value}]), msg)


def test_duplicate_order(tmp_path):
    assert_error(make_repo(tmp_path, [{'order': '1'}, {'order': '1'}]), 'order 重複')


def test_id_folder_mismatch(tmp_path):
    root = make_repo(tmp_path)
    src = root / 'lessons/L01-test/C01-demo'
    src.rename(root / 'lessons/L01-test/C09-demo')
    assert_error(root, '與資料夾名稱')


def test_unknown_lesson(tmp_path):
    assert_error(make_repo(tmp_path, [{'lesson': 'L02'}]), '與上層資料夾')


def test_missing_figure(tmp_path):
    root = make_repo(tmp_path)
    f = root / 'lessons/L01-test/C01-demo/checkin.md'
    f.write_text(f.read_text(encoding='utf-8').replace(
        'source: course.pdf p.1',
        'source: course.pdf p.1\noutputs:\n  figures: [outputs/figures/none.png]'), encoding='utf-8')
    assert_error(root, '找不到圖檔')


def test_missing_front_matter(tmp_path):
    root = make_repo(tmp_path)
    (root / 'lessons/L01-test/C01-demo/checkin.md').write_text('# 沒有 front-matter\n', encoding='utf-8')
    assert_error(root, '缺少 front-matter')


def test_invalid_yaml_reported_not_crash(tmp_path):
    root = make_repo(tmp_path, [{'title_en': 'Hermes: Unquoted Colon'}])
    assert_error(root, 'YAML 格式錯誤')


def test_note_related_unknown_checkin(tmp_path):
    root = make_repo(tmp_path)
    write_fm(root / 'knowledge/backtesting/costs.md',
             {'title': '成本', 'title_en': 'Costs', 'category': 'backtesting',
              'date': '2026-10-10', 'related': '[C99]'})
    assert_error(root, 'related 找不到打卡 C99')


def test_collects_all_errors(tmp_path):
    errs = errors_of(make_repo(tmp_path, [{'category': 'x', 'status': 'y'}]))
    assert len(errs) >= 2


# ---------- 真實 repo ----------

def test_real_repo_is_valid():
    """repo 本身的 36 題打卡必須通過驗證（CI 也會跑）。"""
    m = bm.build(ROOT)
    assert m['stats']['total'] == 36
    assert sorted(m['stats']['flagship']) == ['C08', 'C11', 'C13', 'C17', 'C21']
    assert [c['order'] for c in m['checkins']] == list(range(1, 37))
