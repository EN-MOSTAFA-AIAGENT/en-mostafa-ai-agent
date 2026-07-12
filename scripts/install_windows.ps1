$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher was not found. Install Python 3.11 first."
}

py -3.11 --version
py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m playwright install chromium

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

Write-Host "Installation complete. Safe read-only defaults were copied to .env." -ForegroundColor Green
