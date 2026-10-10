"""
app.py
======
本機端 Flask 伺服器，提供網頁按鈕觸發即時抓取資料的 API。

啟動方式：
    cd webapp
    python app.py
啟動後在瀏覽器打開 http://127.0.0.1:5000

重要：
- PLTR / IREN 需要 Moomoo OpenD 已在本機啟動並登入，否則會回傳錯誤訊息。
- BHP 使用 yfinance，不需要任何本機服務，直接可用。
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# 讓 webapp/ 底下的程式碼可以 import 上一層的 loaders/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from loaders import moomoo_loader, screener, unify_schema, yfinance_loader  # noqa: E402

app = Flask(__name__)

TODAY = dt.date.today()


# ------------------------------------------------------------------
# 頁面路由
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", tickers=unify_schema.TICKER_CONFIG)


@app.route("/notes")
def notes():
    return render_template("notes.html")


@app.route("/screener")
def screener_page():
    return render_template("screener.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ------------------------------------------------------------------
# API 路由
# ------------------------------------------------------------------
@app.route("/api/kline/<ticker>")
def api_kline(ticker: str):
    """
    取得 K 線資料。
    Query 參數：timeframe = "daily"（預設）或 "minute"
    """
    ticker = ticker.upper()
    if ticker not in unify_schema.TICKER_CONFIG:
        return jsonify({"error": f"未知的股票代碼：{ticker}"}), 400

    timeframe = request.args.get("timeframe", "daily")
    cfg = unify_schema.TICKER_CONFIG[ticker]

    try:
        if cfg["source"] == "moomoo":
            if timeframe == "daily":
                start = (TODAY - dt.timedelta(days=365)).isoformat()
                end = TODAY.isoformat()
                df = moomoo_loader.get_daily_kline(cfg["code"], start, end)
                date_col = "date"
            else:
                start = (TODAY - dt.timedelta(days=5)).isoformat()
                end = TODAY.isoformat()
                df = moomoo_loader.get_minute_kline(cfg["code"], start, end)
                date_col = "datetime"
        else:  # yfinance
            if timeframe == "daily":
                start = (TODAY - dt.timedelta(days=365)).isoformat()
                end = TODAY.isoformat()
                df = yfinance_loader.get_daily_kline(cfg["code"], start, end)
                date_col = "date"
            else:
                df = yfinance_loader.get_minute_kline(
                    cfg["code"], period="5d", interval="1m"
                )
                date_col = "datetime"
    except Exception as exc:  # noqa: BLE001 — 統一回傳給前端顯示
        return jsonify({"error": str(exc)}), 502

    payload = {
        "ticker": ticker,
        "currency": cfg["currency"],
        "timeframe": timeframe,
        "candles": [
            {
                "time": row[date_col].strftime("%Y-%m-%d")
                if timeframe == "daily"
                else row[date_col].strftime("%Y-%m-%d %H:%M"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for _, row in df.iterrows()
        ],
    }
    return jsonify(payload)


@app.route("/api/financials/<ticker>")
def api_financials(ticker: str):
    ticker = ticker.upper()
    if ticker not in unify_schema.TICKER_CONFIG:
        return jsonify({"error": f"未知的股票代碼：{ticker}"}), 400

    cfg = unify_schema.TICKER_CONFIG[ticker]

    try:
        if cfg["source"] == "moomoo":
            df = moomoo_loader.get_financials(cfg["code"], num_quarters=8)
        else:
            df = yfinance_loader.get_financials(cfg["code"], num_quarters=8)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 502

    # 統一轉成「欄位 = 期別，列 = 財務科目」的簡單 JSON 格式
    granularity = df.attrs.get("granularity", "quarterly")
    df = df.astype(object).where(df.notna(), None)
    payload = {
        "ticker": ticker,
        "currency": cfg["currency"],
        "granularity": granularity,
        "columns": [str(c) for c in df.columns],
        "rows": [
            {"label": str(idx), "values": list(row.values)}
            for idx, row in df.iterrows()
        ],
    }
    return jsonify(payload)


@app.route("/api/screen")
def api_screen():
    """
    Query 參數：
      plate  - 板塊關鍵字，例如 "semiconductor"（必填）
      roe    - ROE 門檻，百分比數字，例如 15 代表 15%（預設 15）
      max_n  - 候選股數量上限（預設 30）
    """
    plate = request.args.get("plate", "").strip()
    if not plate:
        return jsonify({"error": "請提供板塊關鍵字（plate 參數）"}), 400

    roe_pct = float(request.args.get("roe", 15))
    max_n = int(request.args.get("max_n", 30))

    try:
        df = screener.run_screen(plate, roe_threshold=roe_pct / 100.0, max_candidates=max_n)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 502

    if df.empty:
        return jsonify({"plate": plate, "rows": []})

    df = df.astype(object).where(df.notna(), None)
    payload = {
        "plate": plate,
        "roe_threshold": roe_pct,
        "rows": df.to_dict(orient="records"),
    }
    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
