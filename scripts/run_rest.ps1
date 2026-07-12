$ErrorActionPreference = "Stop"
$env:REST_HOST = if ($env:REST_HOST) { $env:REST_HOST } else { "127.0.0.1" }
$env:READONLY_MODE = if ($env:READONLY_MODE) { $env:READONLY_MODE } else { "true" }
& .\.venv\Scripts\python.exe .\src\server.py
