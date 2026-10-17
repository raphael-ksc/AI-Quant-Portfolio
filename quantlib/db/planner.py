"""增量更新規劃：決定每檔標的要抓哪一段日線，並偵測前復權基準是否改變。

純函式、不連資料庫，方便單元測試。

課程做法（第 4 課 p.37–38）：一條 SQL 查出每檔最新日期，只補缺的日期。
本專案多兩道防呆：
1. 只寫「已收盤」的交易日：盤中執行時不寫入當天還沒走完的 K 線（避免前視偏差）。
2. 每次回看最近 N 個已存交易日：前復權價格在分割或配息後會整段改變，
   若重疊日的收盤價對不上，代表復權基準變了，必須整段重抓，不能只往後補。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd

DEFAULT_START = dt.date(2023, 1, 1)  # 沒有歷史資料時的起點（同課程）
DEFAULT_LOOKBACK = 5
REL_TOLERANCE = 1e-5                 # DECIMAL(18,6) 四捨五入後的比對容忍度


@dataclass(frozen=True)
class MarketHours:
    timezone: str = 'America/New_York'
    close: dt.time = dt.time(16, 0)
    buffer: dt.timedelta = dt.timedelta(minutes=30)  # 收盤後等資料源結算


@dataclass(frozen=True)
class FetchPlan:
    symbol: str
    adjust: str
    start: dt.date | None
    end: dt.date
    reason: str  # full / incremental / up_to_date

    @property
    def skip(self) -> bool:
        return self.reason == 'up_to_date'


def last_closed_session(now: dt.datetime, hours: MarketHours = MarketHours()) -> dt.date:
    """最後一個已收盤的交易日（交易所當地日期）。

    只排除週末，不處理國定假日：假日那天資料源本來就不會回傳 K 線，不影響正確性。
    """
    if now.tzinfo is None:
        raise ValueError('now 必須帶時區')
    local = now.astimezone(ZoneInfo(hours.timezone))
    day = local.date()
    if local.time() < (dt.datetime.combine(day, hours.close) + hours.buffer).time():
        day -= dt.timedelta(days=1)
    while day.weekday() >= 5:  # 週六 5、週日 6
        day -= dt.timedelta(days=1)
    return day


def plan_fetch(symbol: str, adjust: str, *, latest: dt.date | None, overlap_start: dt.date | None,
               last_session: dt.date, mode: str = 'incremental',
               default_start: dt.date = DEFAULT_START) -> FetchPlan:
    """latest：庫中最新日期；overlap_start：庫中倒數第 N 個日期（回看比對的起點）。"""
    if mode not in ('full', 'incremental'):
        raise ValueError(f'mode 只能是 full / incremental：{mode}')
    if mode == 'full' or latest is None:
        return FetchPlan(symbol, adjust, default_start, last_session, 'full')
    if latest >= last_session:
        return FetchPlan(symbol, adjust, None, last_session, 'up_to_date')
    return FetchPlan(symbol, adjust, overlap_start or latest, last_session, 'incremental')


def needs_refresh(stored: pd.DataFrame, fetched: pd.DataFrame, rel_tol: float = REL_TOLERANCE) -> list:
    """比對重疊日的收盤價；回傳對不上的日期清單（空清單 = 基準一致）。

    stored、fetched 皆需有 date、close 欄位。只比兩邊都有的日期。
    """
    if stored.empty or fetched.empty:
        return []
    merged = pd.merge(stored[['date', 'close']], fetched[['date', 'close']],
                      on='date', suffixes=('_db', '_new'))
    diff = (merged['close_db'] - merged['close_new']).abs()
    scale = merged[['close_db', 'close_new']].abs().max(axis=1).clip(lower=1e-9)
    bad = merged.loc[diff / scale > rel_tol, 'date']
    return sorted(bad.tolist())


def trim_unclosed(bars: pd.DataFrame, last_session: dt.date) -> pd.DataFrame:
    """移除晚於最後已收盤交易日的 K 線（盤中執行時當天那根）。"""
    keep = bars['date'].dt.date <= last_session
    return bars.loc[keep].reset_index(drop=True)
