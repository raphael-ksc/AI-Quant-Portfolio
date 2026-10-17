"""scan_secrets.py 單元測試。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import scan_secrets as ss  # noqa: E402


@pytest.mark.parametrize('line', [
    'MYSQL_PASSWORD=hunter2secret',
    "api_key: 'abcdef123456'",
    'token = "s3cr3tvalue99"',
    'ghp_' + 'a' * 36,
    '-----BEGIN RSA PRIVATE KEY-----',
])
def test_detects_secrets(line):
    assert ss.scan_text(line)


@pytest.mark.parametrize('line', [
    'MYSQL_PASSWORD=',                         # .env.example 空白欄位
    'WUCAI_SQL_PASSWORD=',
    'password = os.environ["MYSQL_PASSWORD"]',  # 從環境變數讀取
    "password=os.getenv('MYSQL_PASSWORD')",
    'password=config.mysql_password',
    'host=self.host, user=self.user, password=self.password,',  # 函式參數，結尾有逗號
    'password: ${{ secrets.DB_PASSWORD }}',
    '設環境變數 `WUCAI_SQL_PASSWORD`，絕不可 commit',
])
def test_ignores_placeholders(line):
    assert not ss.scan_text(line)


def test_repo_is_clean():
    assert ss.main() == 0
