// screener.js
// 多因子選股頁的按鈕邏輯：呼叫 /api/screen，把結果畫成表格，
// 通過篩選（passed=true）的列用強調樣式標示。

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("screenBtn");
  if (!btn) return; // 不是 screener.html，略過

  btn.addEventListener("click", runScreen);
});

async function runScreen() {
  const plate = document.getElementById("plateInput").value.trim();
  const roe = document.getElementById("roeInput").value;
  const maxN = document.getElementById("maxnInput").value;
  const statusEl = document.getElementById("screenStatus");
  const btn = document.getElementById("screenBtn");

  if (!plate) {
    statusEl.textContent = currentLang === "zh" ? "請輸入板塊關鍵字" : "Please enter a sector keyword";
    statusEl.className = "status-line error";
    return;
  }

  btn.disabled = true;
  statusEl.textContent = I18N[currentLang].status_screening;
  statusEl.className = "status-line";

  try {
    const res = await fetch(`/api/screen?plate=${encodeURIComponent(plate)}&roe=${roe}&max_n=${maxN}`);
    const json = await res.json();
    if (json.error) throw new Error(json.error);

    renderResults(json.rows || []);
    statusEl.textContent = I18N[currentLang].status_screen_done;
    statusEl.className = "status-line ok";
  } catch (err) {
    statusEl.textContent = I18N[currentLang].status_error + err.message;
    statusEl.className = "status-line error";
  } finally {
    btn.disabled = false;
  }
}

function renderResults(rows) {
  const tbody = document.querySelector("#resultsTable tbody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="6">${
      currentLang === "zh" ? "沒有找到候選股" : "No candidates found"
    }</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row) => {
      const rowClass = row.passed ? "row-passed" : "";
      const roeText = row.roe_ttm === null ? "\u2014" : (row.roe_ttm * 100).toFixed(1) + "%";
      const fcfText = row.fcf_margin_latest === null ? "\u2014" : (row.fcf_margin_latest * 100).toFixed(1) + "%";
      const passedText = row.passed ? "\u2713" : "\u2014";
      return `<tr class="${rowClass}">
        <td>${row.ticker}</td>
        <td>${roeText}</td>
        <td>${row.capex_intensity_trend}</td>
        <td>${row.ocf_coverage_trend}</td>
        <td>${fcfText}</td>
        <td>${passedText}</td>
      </tr>`;
    })
    .join("");
}
