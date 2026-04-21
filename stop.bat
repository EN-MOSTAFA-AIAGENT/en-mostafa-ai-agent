@echo off
title EN MOSTAFA AI AGENT - Stop All Services
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo  Stopping EN MOSTAFA AI AGENT services...
echo.

:: Kill by window title
taskkill /fi "WINDOWTITLE eq REST Server*"     /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq MCP Server*"      /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Cloudflare*"      /f >nul 2>&1

:: Kill by port (safer)
for %%P in (5001 8000) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P "') do (
        taskkill /pid %%a /f >nul 2>&1
    )
)

:: Kill python processes running our files
wmic process where "CommandLine like '%%server.py%%'"    delete >nul 2>&1
wmic process where "CommandLine like '%%mcp_server.py%%'" delete >nul 2>&1

echo  [OK] All services stopped.
echo.
timeout /t 2 >nul
