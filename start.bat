@echo off
title AI WordPress Control Center v2.0
color 0A
cls

echo.
echo  =========================================
echo   AI WordPress Control Center v2.0
echo   EN MOSTAFA AI AGENT
echo  =========================================
echo.

set "PYTHONPATH=C:\mcp-agent"
set "PYTHONIOENCODING=utf-8"
cd /d C:\mcp-agent

echo [1/4] Checking Python 3.11...
py -3.11 --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.11 not found. Install from python.org
    pause & exit /b 1
)
echo       OK

echo [2/4] Checking dependencies...
py -3.11 -c "import flask" 2>nul
if errorlevel 1 (
    echo       Installing flask...
    py -3.11 -m pip install flask flask-socketio --quiet
)
py -3.11 -c "import playwright" 2>nul
if errorlevel 1 (
    echo       Installing playwright...
    py -3.11 -m pip install playwright --quiet
    py -3.11 -m playwright install chromium --quiet 2>nul
)
echo       OK

echo [3/4] Initializing database...
py -3.11 -c "
import sys; sys.path.insert(0,'.')
from knowledge_manager import knowledge_manager
from feedback_loop import feedback_loop
print('      DB ready')
" 2>&1

echo [4/4] Starting server...
echo.
echo  =========================================
echo   Server    : http://localhost:5001
echo   Dashboard : http://localhost:5001/wp-dashboard
echo   Status    : http://localhost:5001/system/status
echo   MCP Server: http://localhost:8000 (separate)
echo  =========================================
echo.
echo  Press CTRL+C to stop
echo.

py -3.11 server.py

echo.
echo  Server stopped.
pause
