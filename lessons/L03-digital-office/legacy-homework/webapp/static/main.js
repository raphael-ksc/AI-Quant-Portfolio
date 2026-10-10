// main.js
// 前端邏輯：語言切換（EN/繁中）、標的與週期選擇、按鈕觸發抓取、
// 用 Lightweight Charts 畫 K 線（國際盤色系：漲=綠、跌=紅），
// 並把財務數據填入表格。

const I18N = {
  zh: {
    site_title: "量化自選股數據終端",
    nav_notes: "學習筆記",
    nav_dashboard: "回到終端",
    nav_screener: "多因子選股",
    nav_about: "架構說明",
    label_ticker: "選擇標的",
    label_timeframe: "K線週期",
    tf_daily: "日線",
    tf_minute: "分鐘線",
    btn_fetch: "抓取數據",
    chart_placeholder: "請選擇標的並按下「抓取數據」",
    financials_title: "季度財務數據（近 8 季）",
    table_metric: "科目",
    status_fetching: "抓取中，請稍候…",
    status_done: "抓取完成",
    status_error: "發生錯誤：",
    label_plate: "板塊關鍵字",
    label_roe: "ROE 門檻（TTM，%）",
    label_maxn: "候選股數量上限",
    btn_screen: "執行篩選",
    label_criteria: "篩選條件",
    results_title: "篩選結果",
    col_ticker: "股票代碼",
    col_roe: "ROE (TTM)",
    col_capex: "Capex 強度趨勢",
    col_ocf: "OCF 覆蓋率趨勢",
    col_fcf: "FCF Margin（最新季）",
    col_passed: "通過",
    status_screening: "正在抓取候選股財務數據並計算因子，可能需要一些時間…",
    status_screen_done: "篩選完成",
    criteria_1: "ROE (TTM) > 門檻",
    criteria_2: "資本支出強度（Capex Intensity）呈上升趨勢",
    criteria_3: "營運現金流覆蓋率（OCF Coverage）呈上升趨勢",
  },
  en: {
    site_title: "Quant Watchlist Terminal",
    nav_notes: "Learning Notes",
    nav_dashboard: "Back to Terminal",
    nav_screener: "Factor Screener",
    nav_about: "About This Project",
    label_ticker: "Select ticker",
    label_timeframe: "Chart timeframe",
    tf_daily: "Daily",
    tf_minute: "Minute",
    btn_fetch: "Fetch data",
    chart_placeholder: "Select a ticker, then press \u201cFetch data\u201d",
    financials_title: "Quarterly financials (last 8 quarters)",
    table_metric: "Metric",
    status_fetching: "Fetching, please wait\u2026",
    status_done: "Done",
    status_error: "Error: ",
    label_plate: "Sector keyword",
    label_roe: "ROE threshold (TTM, %)",
    label_maxn: "Max candidates",
    btn_screen: "Run screen",
    label_criteria: "Screening criteria",
    results_title: "Results",
    col_ticker: "Ticker",
    col_roe: "ROE (TTM)",
    col_capex: "Capex intensity trend",
    col_ocf: "OCF coverage trend",
    col_fcf: "FCF margin (latest qtr)",
    col_passed: "Passed",
    status_screening: "Fetching candidate financials and computing factors, this may take a moment\u2026",
    status_screen_done: "Screen complete",
    criteria_1: "ROE (TTM) above threshold",
    criteria_2: "Capex intensity trending upward",
    criteria_3: "OCF coverage of capex trending upward",
  },
};

let currentLang = localStorage.getItem("quant_lang") || "zh";
let selectedTicker = null;
let selectedTimeframe = "daily";
let chart = null;
let candleSeries = null;

function applyLanguage() {
  const dict = I18N[currentLang];
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });

  const langBtn = document.getElementById("langToggle");
  if (langBtn) langBtn.textContent = currentLang === "zh" ? "EN" : "\u4e2d\u6587";

  document.documentElement.lang = currentLang === "zh" ? "zh-Hant" : "en-AU";

  // notes.html / about.html 用整段內容切換（class 為 lang-zh / lang-en），
  // 而非逐字 data-i18n，因為內容是長篇文章而非短標籤。
  document.querySelectorAll(".lang-zh").forEach((el) => {
    el.classList.toggle("hidden", currentLang !== "zh");
  });
  document.querySelectorAll(".lang-en").forEach((el) => {
    el.classList.toggle("hidden", currentLang !== "en");
  });
}

function initLangToggle() {
  const btn = document.getElementById("langToggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    currentLang = currentLang === "zh" ? "en" : "zh";
    localStorage.setItem("quant_lang", currentLang);
    applyLanguage();
  });
}

// ------------------------------------------------------------
// Dashboard-only logic (index.html)
// ------------------------------------------------------------
function initDashboard() {
  const tickerList = document.getElementById("tickerList");
  if (!tickerList) return; // 不是 index.html，略過

  tickerList.querySelectorAll(".ticker-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      tickerList.querySelectorAll(".ticker-item").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedTicker = btn.dataset.ticker;
    });
  });

  document.querySelectorAll(".tf-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tf-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedTimeframe = btn.dataset.timeframe;
    });
  });

  document.getElementById("fetchBtn").addEventListener("click", fetchAndRender);

  chart = LightweightCharts.createChart(document.getElementById("chartContainer"), {
    layout: {
      background: { color: "transparent" },
      textColor: "#dbe6ff",
      fontFamily: "IBM Plex Mono, monospace",
    },
    grid: {
      vertLines: { color: "rgba(171,210,250,0.06)" },
      horzLines: { color: "rgba(171,210,250,0.06)" },
    },
    rightPriceScale: { borderColor: "rgba(171,210,250,0.18)" },
    timeScale: { borderColor: "rgba(171,210,250,0.18)" },
  });

  // 國際盤色系：漲 = 綠，跌 = 紅（Lightweight Charts 預設方向即符合此需求）
  candleSeries = chart.addCandlestickSeries({
    upColor: "#2fbf71",
    downColor: "#ef4d5e",
    borderUpColor: "#2fbf71",
    borderDownColor: "#ef4d5e",
    wickUpColor: "#2fbf71",
    wickDownColor: "#ef4d5e",
  });

  window.addEventListener("resize", () => {
    const container = document.getElementById("chartContainer");
    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
  });
}

function setStatus(message, type) {
  const el = document.getElementById("statusLine");
  el.textContent = message;
  el.className = "status-line" + (type ? " " + type : "");
}

async function fetchAndRender() {
  const dict = I18N[currentLang];
  if (!selectedTicker) {
    setStatus(currentLang === "zh" ? "請先選擇標的" : "Please select a ticker first", "error");
    return;
  }

  const fetchBtn = document.getElementById("fetchBtn");
  fetchBtn.disabled = true;
  setStatus(dict.status_fetching, "");

  try {
    const [klineRes, finRes] = await Promise.all([
      fetch(`/api/kline/${selectedTicker}?timeframe=${selectedTimeframe}`),
      fetch(`/api/financials/${selectedTicker}`),
    ]);

    const klineJson = await klineRes.json();
    if (klineJson.error) throw new Error(klineJson.error);
    renderChart(klineJson);

    const finJson = await finRes.json();
    if (finJson.error) throw new Error(finJson.error);
    renderFinancials(finJson);

    setStatus(dict.status_done, "ok");
  } catch (err) {
    setStatus(dict.status_error + err.message, "error");
  } finally {
    fetchBtn.disabled = false;
  }
}

function renderChart(data) {
  const title = document.getElementById("chartTitle");
  title.textContent = `${data.ticker} \u00b7 ${selectedTimeframe === "daily" ? I18N[currentLang].tf_daily : I18N[currentLang].tf_minute}`;
  document.getElementById("currencyTag").textContent = data.currency;

  const formatted = data.candles.map((c) => ({
    time: selectedTimeframe === "daily" ? c.time : Math.floor(new Date(c.time.replace(" ", "T") + "Z").getTime() / 1000),
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  }));

  candleSeries.setData(formatted);
  chart.timeScale().fitContent();
}

function renderFinancials(data) {
  const note = document.getElementById("granularityNote");
  if (data.granularity === "annual") {
    note.textContent =
      currentLang === "zh"
        ? "\u26a0\ufe0f 此標的僅提供年報數據（該市場公司多採半年報／年報制度，非季報），下表為近幾年年報，並非季報。"
        : "\u26a0\ufe0f Only annual data is available for this ticker (companies in this market typically report half-yearly/annually rather than quarterly). The table below shows recent annual reports, not quarterly ones.";
    note.classList.remove("hidden");
  } else {
    note.classList.add("hidden");
  }

  const table = document.getElementById("financialsTable");
  const thead = table.querySelector("thead tr");
  const tbody = table.querySelector("tbody");

  thead.innerHTML = `<th data-i18n="table_metric">${I18N[currentLang].table_metric}</th>` +
    data.columns.map((c) => `<th>${c}</th>`).join("");

  tbody.innerHTML = data.rows
    .map(
      (row) =>
        `<tr><td>${row.label}</td>` +
        row.values
          .map((v) => `<td>${v === null ? "\u2014" : formatNumber(v)}</td>`)
          .join("") +
        "</tr>"
    )
    .join("");
}

function formatNumber(v) {
  if (typeof v !== "number") return v;
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// ------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initLangToggle();
  applyLanguage();
  initDashboard();
});
