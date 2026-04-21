@echo off
setlocal EnableExtensions EnableDelayedExpansion
title EN MOSTAFA AI AGENT - Launcher

:: =========================
:: Auto Elevation (Run as Admin)
:: =========================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Restarting as Administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: =========================
:: Config
:: =========================
set "ROOT=C:\mcp-agent"
set "REST_PORT=5001"
set "MCP_PORT=8000"
set "PUBLIC_BASE=https://api.devmostafa.com"
set "LOCAL_REST_BASE=http://127.0.0.1:%REST_PORT%"
set "DASHBOARD_URL=%LOCAL_REST_BASE%/wp-dashboard"
set "CLOUDFLARED_EXE=C:\cloudflared\cloudflared.exe"
set "PYTHON_CMD=py -3.11"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%ROOT%"

cls
color 0A
echo.
echo  ===================================================
echo    EN MOSTAFA AI AGENT  -  WordPress Control Center
echo    v2.0  ^|  Admin Mode  ^|  Full Restart
echo  ===================================================
echo.

:: =========================
:: Validate files
:: =========================
if not exist "%ROOT%\server.py" (
    echo [ERROR] server.py not found in %ROOT%
    pause & exit /b 1
)
if not exist "%ROOT%\mcp_server.py" (
    echo [ERROR] mcp_server.py not found in %ROOT%
    pause & exit /b 1
)

:: =========================
:: [0/6] Stop everything first (clean slate)
:: =========================
echo [0/6] Stopping any running services...

:: Kill by port 5001 and 8000
for %%P in (%REST_PORT% %MCP_PORT%) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%%P "') do (
        taskkill /pid %%a /f >nul 2>&1
    )
)

:: Kill python processes running our files
wmic process where "CommandLine like '%%server.py%%'"     delete >nul 2>&1
wmic process where "CommandLine like '%%mcp_server.py%%'" delete >nul 2>&1

:: Wait for ports to free
timeout /t 2 >nul
echo   [OK] Services stopped.
echo.

:: =========================
:: First-Run Setup
:: =========================
if not exist "%ROOT%\agent_state.db" (
    echo [SETUP] First run - initializing system...
    cd /d "%ROOT%"
    %PYTHON_CMD% -W ignore setup.py
    echo.
)

:: =========================
:: [1/6] REST Server (server.py)
:: =========================
echo [1/6] Starting REST Server (port %REST_PORT%)...
cd /d "%ROOT%"
start "REST Server :5001" cmd /k "title REST Server :5001 && cd /d %ROOT% && set PYTHONIOENCODING=utf-8&& set PYTHONPATH=%ROOT%&& set PUBLIC_URL_BASE=%PUBLIC_BASE%&& set REST_PORT=%REST_PORT%&& %PYTHON_CMD% -W ignore -u server.py"

:: Wait for port
echo   Waiting for REST server...
call :wait_for_port %REST_PORT% "REST Server" 30
if errorlevel 1 (
    echo   [ERROR] REST Server failed to start on port %REST_PORT%!
    echo   Check the "REST Server :5001" window for errors.
    pause & exit /b 1
)

:: Verify /healthz responds
echo   Verifying /healthz endpoint...
call :wait_for_http "%LOCAL_REST_BASE%/healthz" "REST /healthz" 15
echo.

:: =========================
:: [2/6] MCP Server (mcp_server.py)
:: =========================
echo [2/6] Starting MCP Server (port %MCP_PORT%)...
start "MCP Server :8000" cmd /k "title MCP Server :8000 && cd /d %ROOT% && set PYTHONIOENCODING=utf-8&& set PYTHONPATH=%ROOT%&& set PUBLIC_URL_BASE=%PUBLIC_BASE%&& set REST_API_BASE=%LOCAL_REST_BASE%&& set MCP_PORT=%MCP_PORT%&& set FASTMCP_PORT=%MCP_PORT%&& %PYTHON_CMD% -W ignore -u mcp_server.py"

call :wait_for_port %MCP_PORT% "MCP Server" 25
echo.

:: =========================
:: [3/6] WordPress Warm-up
:: =========================
echo [3/6] Warming up WordPress integration...
cd /d "%ROOT%"
%PYTHON_CMD% -W ignore warmup.py 2>&1
echo.

:: =========================
:: [4/6] Cloudflare Tunnel
:: =========================
echo [4/6] Cloudflare Tunnel...
tasklist 2>nul | findstr /i "cloudflared" >nul
if not errorlevel 1 (
    echo   [INFO] Already running - skipped
) else (
    if exist "%CLOUDFLARED_EXE%" (
        start "Cloudflare Tunnel" cmd /k ""%CLOUDFLARED_EXE%" tunnel run mcp-agent"
        echo   [OK] Tunnel started
    ) else (
        echo   [WARN] cloudflared.exe not found at %CLOUDFLARED_EXE%
    )
)
echo.

:: =========================
:: [5/6] Status Report
:: =========================
echo [5/6] System Status...
cd /d "%ROOT%"
%PYTHON_CMD% -W ignore status.py 2>&1
echo.

:: =========================
:: [6/6] Open Dashboard
:: =========================
echo [6/6] Opening Dashboard...
timeout /t 1 >nul
start "" "%DASHBOARD_URL%"

echo.
echo  ===================================================
echo    ALL SERVICES RUNNING
echo  ===================================================
echo    REST API  : %LOCAL_REST_BASE%
echo    DASHBOARD : %DASHBOARD_URL%
echo    MCP SSE   : http://127.0.0.1:%MCP_PORT%
echo    PUBLIC    : %PUBLIC_BASE%
echo    HEALTH    : %LOCAL_REST_BASE%/healthz
echo  ===================================================
echo.
echo  Each service runs in its own window.
echo  Press any key to close this launcher.
echo.
pause >nul
exit /b 0


:: =========================
:: :wait_for_port  port  name  max_tries
:: =========================
:wait_for_port
set "_WP=%~1"
set "_WN=%~2"
set "_MAX=%~3"
if "%_MAX%"=="" set "_MAX=30"
set /a _TRY=0
:wfp_loop
set /a _TRY+=1
powershell -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort %_WP% -State Listen -ErrorAction SilentlyContinue; if($c){exit 0}else{exit 1}" >nul 2>nul
if not errorlevel 1 (
    echo   [OK] %_WN% listening on port %_WP%
    exit /b 0
)
if %_TRY% geq %_MAX% (
    echo   [WARN] %_WN% - timeout waiting for port %_WP%
    exit /b 1
)
<nul set /p ".=."
timeout /t 1 >nul
goto wfp_loop


:: =========================
:: :wait_for_http  url  name  max_tries
:: =========================
:wait_for_http
set "_URL=%~1"
set "_HN=%~2"
set "_MAX=%~3"
if "%_MAX%"=="" set "_MAX=15"
set /a _TRY=0
:wfh_loop
set /a _TRY+=1
powershell -NoProfile -Command "try{$r=Invoke-WebRequest '%_URL%' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; if($r.StatusCode -eq 200){exit 0}}catch{exit 1}" >nul 2>nul
if not errorlevel 1 (
    echo   [OK] %_HN% responding
    exit /b 0
)
if %_TRY% geq %_MAX% (
    echo   [WARN] %_HN% not responding after %_MAX%s
    exit /b 1
)
<nul set /p ".=."
timeout /t 1 >nul
goto wfh_loop
