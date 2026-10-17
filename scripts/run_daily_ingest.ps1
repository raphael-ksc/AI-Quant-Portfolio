# C06 每日日線增量更新（給 Windows 工作排程器呼叫）
#
# 排程：週二至週六 06:00（台北時間），對應美股週一至週五收盤後。
# 前置條件：Moomoo OpenD 已啟動並登入（127.0.0.1:11111）、本機 MySQL80 執行中、.env 已設定。
# 紀錄：data/logs/ingest_daily_YYYYMMDD.log（data/ 不進 repo）。
# 某天失敗沒關係：下一次成功執行時，增量規劃會自動補齊缺的日期。
# 排程執行時不更新 outputs/metrics.json，避免每天產生 git 變更。

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root 'data\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("ingest_daily_{0}.log" -f (Get-Date -Format 'yyyyMMdd'))

function Write-Log([string]$Message) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $Log -Value $line -Encoding UTF8
}

Set-Location $Root
$env:PYTHONIOENCODING = 'utf-8'
Write-Log '開始執行'

# 先確認 OpenD 有在聽 11111 埠；沒開就記錄後結束，不嘗試連線
$opend = Test-NetConnection -ComputerName 127.0.0.1 -Port 11111 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $opend) {
    Write-Log '失敗：Moomoo OpenD 沒有啟動（127.0.0.1:11111），本次略過'
    exit 1
}

$python = Join-Path $Root '.venv\Scripts\python.exe'
$script = Join-Path $Root 'lessons\L04-data-pipeline\C06-market-data-collection\src\ingest_daily.py'
# Moomoo SDK 的連線訊息寫在 stderr；PowerShell 5.1 會把 stderr 包成錯誤物件，這段改回 Continue 以免中斷
$ErrorActionPreference = 'Continue'
$output = & $python $script --no-metrics 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'open_context_base' }
$code = $LASTEXITCODE
$output | ForEach-Object { Write-Log "$_" }
Write-Log ("結束，exit code = {0}" -f $code)
exit $code
