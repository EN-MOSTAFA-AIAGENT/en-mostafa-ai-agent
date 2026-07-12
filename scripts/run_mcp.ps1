$ErrorActionPreference = "Stop"
$env:MCP_HOST = if ($env:MCP_HOST) { $env:MCP_HOST } else { "127.0.0.1" }
$env:READONLY_MODE = if ($env:READONLY_MODE) { $env:READONLY_MODE } else { "true" }
& .\.venv\Scripts\python.exe .\src\mcp_server.py
