"""資料庫連線設定：一律從環境變數（.env）讀取，不在程式碼或 repo 中出現密碼。

本機 MySQL80 與 Docker 共用同一組欄位，切換時只改 MYSQL_PORT（本機 3306、Docker 3307）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_KEYS = ('MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE')


class DbConfigError(RuntimeError):
    """.env 缺少欄位或格式錯誤。"""


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    database: str
    password: str = field(repr=False)  # repr 不顯示密碼，避免出現在 log 或錯誤訊息

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, *, database: str | None = None,
                 load_dotenv_file: bool = True) -> 'DbConfig':
        """讀取設定；env 為 None 時先載入 Project/.env 再讀 os.environ。"""
        if env is None:
            if load_dotenv_file:
                from dotenv import load_dotenv  # 延遲載入：CI 單元測試不需要 python-dotenv
                load_dotenv(ROOT / '.env')
            env = os.environ
        missing = [k for k in REQUIRED_KEYS if not str(env.get(k, '')).strip()]
        if missing:
            raise DbConfigError(f'.env 缺少或未填：{", ".join(missing)}（範本見 .env.example）')
        try:
            port = int(env['MYSQL_PORT'])
        except ValueError as e:
            raise DbConfigError(f'MYSQL_PORT 必須是整數：{env["MYSQL_PORT"]!r}') from e
        return cls(host=env['MYSQL_HOST'].strip(), port=port, user=env['MYSQL_USER'].strip(),
                   database=(database or env['MYSQL_DATABASE']).strip(), password=env['MYSQL_PASSWORD'])

    def connect(self, *, with_database: bool = True):
        """建立 pymysql 連線（手動 commit）；with_database=False 用於建立資料庫前。"""
        import pymysql  # 延遲載入：CI 單元測試不需要 pymysql
        return pymysql.connect(
            host=self.host, port=self.port, user=self.user, password=self.password,
            database=self.database if with_database else None,
            charset='utf8mb4', autocommit=False, connect_timeout=10,
        )

    def describe(self) -> str:
        """給人看的連線說明（不含密碼）。"""
        return f'{self.user}@{self.host}:{self.port}/{self.database}'
