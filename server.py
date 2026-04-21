"""
MOSTAFA AI AGENT v4.0 - EASY MODE 🚀
✅ بدون Wake Token - شغال مباشرة
✅ كل الأدوات متاحة بدون قيود
✅ Live Dashboard Support
"""

from flask import Flask, request, jsonify, send_from_directory, Response, render_template
import os
import logging
import subprocess
import uuid
import fnmatch
import glob
import shutil
import base64
import threading
import time
import json
import asyncio
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext, Playwright
from job_manager import CommandParser, CommandType

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
BACKUP_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Agent_Backups")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

REST_HOST = os.environ.get("REST_HOST", "0.0.0.0")
REST_PORT = int(os.environ.get("REST_PORT", "5001"))
PUBLIC_URL_BASE = os.environ.get("PUBLIC_URL_BASE", f"http://127.0.0.1:{REST_PORT}").rstrip("/")

# ==================== PLAYWRIGHT ====================
# المتغيرات العامة للـ browser (عالمية)
_playwright_pw = None
_playwright_browser = None
_playwright_context = None
_playwright_page = None
_playwright_lock = threading.Lock()

PLAYWRIGHT_BROWSERS = os.environ.get("PLAYWRIGHT_BROWSERS", "0")

# ==================== LIVE DASHBOARD ====================
# Live Dashboard المتغيرات
_dashboard_active = False
_browser_snapshot = {
    "url": "",
    "title": "",
    "status": "stopped",  # stopped, running, idle
    "screenshot": None,
    "last_action": None,
    "last_update": None,
    "logs": [],
    "command_status": None,
    "progress": 0
}
_dashboard_snapshot_lock = threading.Lock()

def broadcast_dashboard_update():
    """تحديث جميع المتصلين بالـ Dashboard"""
    with _dashboard_snapshot_lock:
        snapshot = _browser_snapshot.copy()
    if socketio:
        socketio.emit("dashboard_update", snapshot, namespace="/dashboard")


def append_dashboard_log(message: str, level: str = "info"):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    with _dashboard_snapshot_lock:
        logs = list(_browser_snapshot.get("logs", []))
        logs.append(entry)
        _browser_snapshot["logs"] = logs[-100:]
        _browser_snapshot["last_update"] = datetime.now().isoformat()


def update_dashboard_snapshot(
    *,
    page=None,
    action: str = None,
    screenshot: str = None,
    status: str = None,
    command_status: str = None,
    progress: int = None,
    broadcast: bool = True
):
    with _dashboard_snapshot_lock:
        if page is not None:
            try:
                _browser_snapshot["url"] = page.url or ""
            except Exception:
                pass
            try:
                _browser_snapshot["title"] = page.title() or ""
            except Exception:
                pass
        if action is not None:
            _browser_snapshot["last_action"] = action
        if screenshot is not None:
            _browser_snapshot["screenshot"] = screenshot
        if status is not None:
            _browser_snapshot["status"] = status
        if command_status is not None:
            _browser_snapshot["command_status"] = command_status
        if progress is not None:
            _browser_snapshot["progress"] = progress
        _browser_snapshot["last_update"] = datetime.now().isoformat()

    if broadcast:
        broadcast_dashboard_update()

# ==================== DASHBOARD HTML ====================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MOSTAFA AI Agent Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; }
        .header h1 { font-size: 2.5em; background: linear-gradient(90deg, #00d4ff, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
        .header p { color: #888; }
        .status-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 0 5px; }
        .status-running { background: #22c55e; color: white; }
        .status-stopped { background: #ef4444; color: white; }
        .status-idle { background: #f59e0b; color: white; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; border: 1px solid rgba(255,255,255,0.1); }
        .card h3 { color: #00d4ff; margin-bottom: 15px; font-size: 1.2em; }
        .screen-container { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 10px; overflow: hidden; }
        .screen { width: 100%; height: 100%; object-fit: contain; }
        .status-overlay { position: absolute; top: 10px; right: 10px; padding: 5px 12px; border-radius: 15px; font-size: 0.8em; font-weight: bold; }
        .control-panel { display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: all 0.3s; font-size: 1em; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-start { background: linear-gradient(135deg, #22c55e, #16a34a); color: white; }
        .btn-stop { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
        .btn-refresh { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
        .btn-refresh:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(59,130,246,0.4); }
        .command-box { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        .command-input { flex: 1; min-width: 180px; padding: 12px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.15); background: rgba(0,0,0,0.25); color: #fff; }
        .quick-actions { margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn-quick { background: rgba(255,255,255,0.08); color: white; border: 1px solid rgba(255,255,255,0.12); }
        .info-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .info-item:last-child { border-bottom: none; }
        .info-label { color: #888; }
        .info-value { color: #fff; font-weight: bold; }
        .log-panel { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 15px; height: 200px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9em; }
        .log-entry { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .log-time { color: #00d4ff; }
        .log-info { color: #888; }
        .log-success { color: #22c55e; }
        .log-error { color: #ef4444; }
        .loading { animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .live-indicator { display: inline-block; width: 10px; height: 10px; background: #22c55e; border-radius: 50%; animation: blink 1s infinite; margin-right: 8px; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 MOSTAFA AI Agent</h1>
            <p id="status-text" class="status-badge status-stopped">غير متصل</p>
            <p style="margin-top: 10px; color: #666;">
                <span id="live-indicator" class="live-indicator" style="display: none;"></span>
                <span id="connection-status">Connecting...</span>
            </p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🖥️ Live Screen</h3>
                <div class="screen-container">
                    <div id="status-overlay" class="status-overlay status-stopped">STOPPED</div>
                    <img id="screen" class="screen" src="" alt="Browser Screen">
                </div>
                <div class="control-panel" style="margin-top: 15px;">
                    <button id="btn-start" class="btn btn-start" onclick="startAgent()">▶️ Start Agent</button>
                    <button id="btn-stop" class="btn btn-stop" onclick="stopAgent()">⏹️ Stop Agent</button>
                    <button id="btn-refresh" class="btn btn-refresh" onclick="refreshScreenshot()">🔄 Refresh</button>
                </div>
                <div class="command-box">
                    <input id="command-input" class="command-input" type="text" placeholder="اكتب أمرًا للوكيل أو رابطًا..." onkeydown="handleCommandKey(event)">
                    <button class="btn btn-refresh" onclick="sendCommand()">Send</button>
                </div>
                <div class="quick-actions">
                    <button class="btn btn-quick" onclick="sendQuickCommand('reload')">Reload</button>
                    <button class="btn btn-quick" onclick="sendQuickCommand('back')">Back</button>
                    <button class="btn btn-quick" onclick="sendQuickCommand('لقطة شاشة')">Screenshot</button>
                    <button class="btn btn-quick" onclick="sendQuickCommand('scroll down')">Scroll Down</button>
                </div>
            </div>

            <div class="card">
                <h3>📊 Agent Status</h3>
                <div class="info-item">
                    <span class="info-label">Status:</span>
                    <span id="info-status" class="info-value">Stopped</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Current URL:</span>
                    <span id="info-url" class="info-value">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Page Title:</span>
                    <span id="info-title" class="info-value">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Last Action:</span>
                    <span id="info-action" class="info-value">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Last Update:</span>
                    <span id="info-update" class="info-value">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Command Status:</span>
                    <span id="info-command" class="info-value">-</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Progress:</span>
                    <span id="info-progress" class="info-value">0%</span>
                </div>
            </div>

            <div class="card">
                <h3>📝 System Logs</h3>
                <div id="log-panel" class="log-panel">
                    <div class="log-entry"><span class="log-time">System:</span> <span class="log-info">Initializing dashboard...</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let socket;
        let updateInterval;
        let lastScreenshot = '';

        function connect() {
            socket = io('/dashboard', {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });

            socket.on('connect', function() {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').style.color = '#22c55e';
                addLog('Connected to agent dashboard', 'success');
            });

            socket.on('disconnect', function() {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').style.color = '#ef4444';
                addLog('Disconnected from agent', 'error');
            });

            socket.on('dashboard_update', function(data) {
                updateDashboard(data);
            });

            socket.on('connect_error', function(error) {
                addLog('Connection error: ' + error.message, 'error');
            });

            socket.on('reconnect', function() {
                addLog('Reconnected to agent', 'success');
            });

            socket.on('reconnect_error', function(error) {
                addLog('Reconnection error: ' + error.message, 'error');
            });
        }

        function updateDashboard(data) {
            // Update status badge
            const statusBadge = document.getElementById('status-text');
            const statusOverlay = document.getElementById('status-overlay');
            statusBadge.className = 'status-badge';
            statusOverlay.className = 'status-overlay';

            if (data.status === 'running') {
                statusBadge.classList.add('status-running');
                statusOverlay.classList.add('status-running');
                document.getElementById('live-indicator').style.display = 'inline-block';
                startAutoRefresh();
            } else if (data.status === 'idle') {
                statusBadge.classList.add('status-idle');
                statusOverlay.classList.add('status-idle');
                stopAutoRefresh();
            } else {
                statusBadge.classList.add('status-stopped');
                statusOverlay.classList.add('status-stopped');
                document.getElementById('live-indicator').style.display = 'none';
                stopAutoRefresh();
            }

            // Update info panel
            document.getElementById('info-status').textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            document.getElementById('info-url').textContent = data.url || '-';
            document.getElementById('info-title').textContent = data.title || '-';
            document.getElementById('info-action').textContent = data.last_action || '-';
            document.getElementById('info-update').textContent = data.last_update || '-';
            document.getElementById('info-command').textContent = data.command_status || '-';
            document.getElementById('info-progress').textContent = (data.progress ?? 0) + '%';

            // Update screenshot
            if (data.screenshot && data.screenshot !== lastScreenshot) {
                lastScreenshot = data.screenshot;
                document.getElementById('screen').src = data.screenshot;
            }

            if (Array.isArray(data.logs)) {
                renderLogs(data.logs);
            }
        }

        async function startAgent() {
            try {
                addLog('Starting agent...', 'info');
                const response = await fetch('/agent/running', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({running: true})
                });
                const result = await response.json();
                addLog('Agent started: ' + (result.running ? 'Running' : 'Failed'), result.running ? 'success' : 'error');
            } catch (error) {
                addLog('Error starting agent: ' + error.message, 'error');
            }
        }

        async function stopAgent() {
            try {
                addLog('Stopping agent...', 'info');
                const response = await fetch('/agent/running', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({running: false})
                });
                const result = await response.json();
                addLog('Agent stopped: ' + (result.running ? 'Running' : 'Stopped'), result.running ? 'success' : 'error');
            } catch (error) {
                addLog('Error stopping agent: ' + error.message, 'error');
            }
        }

        async function refreshScreenshot() {
            try {
                addLog('Refreshing screenshot...', 'info');
                const response = await fetch('/agent/screenshot', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const result = await response.json();
                if (result.success) {
                    addLog('Screenshot refreshed successfully', 'success');
                    document.getElementById('screen').src = result.url;
                    lastScreenshot = result.url;
                } else {
                    addLog('Error refreshing screenshot: ' + result.error, 'error');
                }
            } catch (error) {
                addLog('Error refreshing screenshot: ' + error.message, 'error');
            }
        }

        function addLog(message, type) {
            const logPanel = document.getElementById('log-panel');
            const time = new Date().toLocaleTimeString('en-US', {hour12: false});
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-${type}">${message}</span>`;
            logPanel.appendChild(logEntry);
            logPanel.scrollTop = logPanel.scrollHeight;
        }

        function renderLogs(logs) {
            const logPanel = document.getElementById('log-panel');
            logPanel.innerHTML = '';
            logs.forEach((entry) => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerHTML = `<span class="log-time">[${entry.time}]</span> <span class="log-${entry.level || 'info'}">${entry.message}</span>`;
                logPanel.appendChild(logEntry);
            });
            logPanel.scrollTop = logPanel.scrollHeight;
        }

        async function sendCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            if (!command) return;

            try {
                addLog('Sending command: ' + command, 'info');
                const response = await fetch('/agent/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command})
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    input.value = '';
                    addLog('Command executed: ' + result.action, 'success');
                } else {
                    addLog('Command failed: ' + (result.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                addLog('Command error: ' + error.message, 'error');
            }
        }

        function sendQuickCommand(command) {
            document.getElementById('command-input').value = command;
            sendCommand();
        }

        function handleCommandKey(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        }

        function renderLogs(logs) {
            const logPanel = document.getElementById('log-panel');
            logPanel.innerHTML = '';
            logs.forEach((entry) => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.innerHTML = `<span class="log-time">[${entry.time}]</span> <span class="log-${entry.level || 'info'}">${entry.message}</span>`;
                logPanel.appendChild(logEntry);
            });
            logPanel.scrollTop = logPanel.scrollHeight;
        }

        async function sendCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            if (!command) return;

            try {
                addLog('Sending command: ' + command, 'info');
                const response = await fetch('/agent/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command})
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    input.value = '';
                    addLog('Command executed: ' + result.action, 'success');
                } else {
                    addLog('Command failed: ' + (result.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                addLog('Command error: ' + error.message, 'error');
            }
        }

        function sendQuickCommand(command) {
            document.getElementById('command-input').value = command;
            sendCommand();
        }

        function handleCommandKey(event) {
            if (event.key === 'Enter') {
                sendCommand();
            }
        }

        // Auto-refresh screenshot every 3 seconds when running
        function startAutoRefresh() {
            if (updateInterval) return;
            updateInterval = setInterval(refreshScreenshot, 3000);
        }

        function stopAutoRefresh() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }

        // Initialize
        connect();
        addLog('Dashboard initialized', 'info');
    </script>
</body>
</html>
"""

DASHBOARD_WS_HTML = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>Mostafa AI - Live Stream</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0f0f1a; color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }
        .container { text-align: center; padding: 20px; }
        .status { font-size: 2em; margin: 20px 0; }
        .status.connected { color: #22c55e; }
        .status.disconnected { color: #ef4444; }
        .video-container { width: 100%; max-width: 1200px; margin: 20px auto; background: #000; border-radius: 10px; overflow: hidden; }
        .stream-image { width: 100%; display: block; min-height: 300px; object-fit: contain; }
        .controls { margin: 20px 0; }
        button { padding: 15px 30px; font-size: 1.1em; margin: 5px; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; border-radius: 8px; transition: transform 0.2s; }
        button:hover { transform: scale(1.05); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .log { margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.5); border-radius: 8px; max-height: 150px; overflow-y: auto; font-family: monospace; font-size: 0.9em; }
        .log-entry { margin: 5px 0; }
        .success { color: #22c55e; }
        .error { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Mostafa AI - Live Stream</h1>
        <div id="status" class="status disconnected">Disconnected</div>
        <div class="video-container">
            <img id="stream-image" class="stream-image" alt="Live stream frame">
        </div>
        <div class="controls">
            <button id="btn-start" onclick="startStream()">Start Stream</button>
            <button id="btn-stop" onclick="stopStream()" disabled>Stop Stream</button>
        </div>
        <div id="log" class="log"></div>
    </div>

    <script>
        const streamImage = document.getElementById('stream-image');
        const status = document.getElementById('status');
        const btnStart = document.getElementById('btn-start');
        const btnStop = document.getElementById('btn-stop');
        const log = document.getElementById('log');
        let stream;
        let lastFrame = '';

        function addLog(msg, type) {
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + type;
            entry.textContent = msg;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }

        function startStream() {
            try {
                addLog('Connecting to stream events...', 'info');
                stream = new EventSource('/stream/events');

                stream.onopen = function() {
                    status.className = 'status connected';
                    status.textContent = 'Connected';
                    btnStart.disabled = true;
                    btnStop.disabled = false;
                    addLog('Live stream connected successfully!', 'success');
                };

                stream.onmessage = function(e) {
                    const data = JSON.parse(e.data);
                    if (data.base64) {
                        const src = 'data:image/png;base64,' + data.base64;
                        if (src !== lastFrame) {
                            streamImage.src = src;
                            lastFrame = src;
                            addLog('New frame received', 'info');
                        }
                    }
                };

                stream.onerror = function() {
                    status.className = 'status disconnected';
                    status.textContent = 'Disconnected';
                    btnStart.disabled = false;
                    btnStop.disabled = true;
                    if (stream) {
                        stream.close();
                        stream = null;
                    }
                    addLog('Live stream disconnected', 'error');
                };

            } catch (error) {
                addLog('Error: ' + error.message, 'error');
            }
        }

        function stopStream() {
            if (stream) {
                stream.close();
                stream = null;
                status.className = 'status disconnected';
                status.textContent = 'Disconnected';
                btnStart.disabled = false;
                btnStop.disabled = true;
                addLog('Stream stopped by user', 'info');
            }
        }
    </script>
</body>
</html>
"""

# WebSocket handlers
def handle_websocket(websocket, path):
    """WebSocket handler للـ Live Stream"""
    return None

    try:
        # Send initial snapshot
        snapshot = _browser_snapshot.copy()
        websocket.send(json.dumps(snapshot))

        # Send updates periodically
        while True:
            with _dashboard_snapshot_lock:
                snapshot = _browser_snapshot.copy()
            websocket.send(json.dumps(snapshot))
            time.sleep(1)  # Update every second

    except websockets.exceptions.ConnectionClosed:
        _dashboard_active = False
    except Exception as e:
        _dashboard_active = False

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MOSTAFA_AI")

# ==================== KEEP-ALIVE PING ====================
def keep_alive_ping():
    """Ping دوري للحفاظ على الاتصال"""
    while True:
        time.sleep(30)
        try:
            import urllib.request
            urllib.request.urlopen(f"{PUBLIC_URL_BASE}/healthz", timeout=5)
            logger.debug("Keep-alive ping sent")
        except:
            pass

keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
keep_alive_thread.start()
logger.info("Keep-alive started (30s interval)")

def get_browser_context():
    """Initialize Playwright browser context"""
    global _playwright_pw, _playwright_browser, _playwright_context, _playwright_page

    if _playwright_pw is None:
        _playwright_pw = sync_playwright().start()
        _playwright_browser = _playwright_pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        _playwright_context = _playwright_browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        _playwright_page = _playwright_context.new_page()

    return _playwright_pw, _playwright_browser, _playwright_context


def capture_live_frame(page=None, full_page: bool = False):
    page = page or _playwright_page
    if page is None:
        return None
    img = page.screenshot(type="png", full_page=full_page)
    return f"data:image/png;base64,{base64.b64encode(img).decode('utf-8')}"


def execute_dashboard_command(page, command):
    if not page:
        raise RuntimeError("No browser active")

    parsed = CommandParser.parse(command) if command else None
    if not parsed and command and command.strip().startswith(("http://", "https://")):
        page.goto(command.strip(), wait_until="domcontentloaded", timeout=30000)
        return "goto"
    if not parsed:
        raise RuntimeError("Unsupported command")

    if parsed.type == CommandType.GOTO:
        target_url = parsed.params.get("url")
        if not target_url:
            raise RuntimeError("Missing target URL")
        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        return "goto"

    if parsed.type == CommandType.BACK:
        page.go_back()
        return "back"

    if parsed.type == CommandType.RELOAD:
        page.reload(wait_until="domcontentloaded")
        return "reload"

    if parsed.type == CommandType.WAIT_LOAD:
        page.wait_for_load_state("networkidle", timeout=30000)
        return "wait_load"

    if parsed.type == CommandType.SCREENSHOT:
        return "screenshot"

    if parsed.type == CommandType.SCROLL:
        pages = max(1, int(parsed.params.get("pages", 1)))
        direction = parsed.params.get("direction", "down")
        multiplier = 1 if direction == "down" else -1
        page.evaluate(
            "(distance) => window.scrollBy({ top: distance, behavior: 'smooth' })",
            page.viewport_size["height"] * pages * multiplier if page.viewport_size else 800 * pages * multiplier
        )
        page.wait_for_timeout(600)
        return f"scroll_{direction}"

    raise RuntimeError(f"Unsupported command type: {parsed.type.value}")

# ==================== CONFIG ====================
READONLY_MODE = os.environ.get("READONLY_MODE", "false").lower() == "true"
app = Flask(__name__)
socketio = None

# Initialize SocketIO
def init_socketio():
    global socketio
    from flask_socketio import SocketIO
    # Use eventlet for async support to fix Python 3.11 compatibility
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')
def register_socketio_handlers():
    @socketio.on("connect", namespace="/dashboard")
    def dash_connect():
        logger.info("✅ Dashboard connected")
        with _dashboard_snapshot_lock:
            snapshot = _browser_snapshot.copy()
        socketio.emit("dashboard_update", snapshot, namespace="/dashboard")

    @socketio.on("disconnect", namespace="/dashboard")
    def dash_disconnect():
        logger.info("❌ Dashboard disconnected")


# ==================== AGENT STATE ====================
agent_status = {
    "running": False,
    "last_screenshot": None,
    "last_action": None,
    "current_url": None,
    "started_at": None
}
agent_status_lock = threading.RLock()


def resolve_screenshot_base64(screenshot_ref):
    """Resolve a screenshot reference to raw base64 for live streaming."""
    if not screenshot_ref:
        return None

    if isinstance(screenshot_ref, str) and screenshot_ref.startswith("data:"):
        parts = screenshot_ref.split(",", 1)
        return parts[1] if len(parts) == 2 else None

    local_path = None
    if isinstance(screenshot_ref, str):
        public_prefix = f"{PUBLIC_URL_BASE}/screenshots/"
        if screenshot_ref.startswith(public_prefix):
            filename = screenshot_ref[len(public_prefix):]
            local_path = os.path.join(SCREENSHOTS_DIR, filename)
        elif os.path.isabs(screenshot_ref):
            local_path = screenshot_ref
        else:
            local_path = os.path.join(SCREENSHOTS_DIR, screenshot_ref)

    if not local_path or not os.path.exists(local_path):
        return None

    with open(local_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_stream_snapshot():
    with _dashboard_snapshot_lock:
        snapshot = _browser_snapshot.copy()

    return {
        "type": "snapshot",
        "url": snapshot.get("url", ""),
        "title": snapshot.get("title", ""),
        "status": snapshot.get("status", "stopped"),
        "last_action": snapshot.get("last_action"),
        "last_update": snapshot.get("last_update"),
        "base64": resolve_screenshot_base64(snapshot.get("screenshot")),
    }

# ==================== BASIC ROUTES (Diagnostics) ====================

@app.route("/", methods=["GET", "HEAD"])
def root():
    return jsonify({"service": "MOSTAFA AI", "ok": True,
                   "screenshots": f"{PUBLIC_URL_BASE}/screenshots/"})


@app.route("/healthz", methods=["GET", "HEAD"])
def healthz():
    return jsonify({
        "ok": True,
        "readonly_mode": READONLY_MODE
    }), 200

@app.route("/screenshots/<filename>", methods=["GET"])
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)

@app.route('/mcp/screenshot/save', methods=['POST'])
def save_screenshot():
    """حفظ Screenshot من Base64 وإرجاع public_url"""
    data = request.json
    b64 = data.get("base64", "").split(",")[-1]
    filename = data.get("filename") or f"shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    if not filename.endswith(('.png', '.jpg')):
        filename += '.png'
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64))

    # تحديث حالة الـ Agent
    with agent_status_lock:
        agent_status["last_screenshot"] = f"{PUBLIC_URL_BASE}/screenshots/{filename}"
        agent_status["last_action"] = "screenshot_taken"

    update_dashboard_snapshot(
        action="screenshot_saved",
        screenshot=f"{PUBLIC_URL_BASE}/screenshots/{filename}",
        status="running" if agent_status.get("running") else "idle"
    )
    append_dashboard_log("Screenshot saved from external source", "success")

    return jsonify({
        "success": True,
        "public_url": f"{PUBLIC_URL_BASE}/screenshots/{filename}",
        "local_path": filepath
    })

@app.route('/agent/status', methods=['GET'])
def get_agent_status():
    """حالة الـ Agent الحالية"""
    with agent_status_lock:
        return jsonify(agent_status.copy())

@app.route('/agent/screenshot', methods=['POST'])
def agent_screenshot():
    """أخذ لقطة من الـ Agent الحالي"""
    global _playwright_page

    with agent_status_lock:
        if not agent_status["running"]:
            return jsonify({"error": "Agent not running"}), 400

    try:
        # استخدام المتغير العام للـ page
        if _playwright_page is None:
            return jsonify({"error": "No browser active"}), 400

        # أخذ لقطة
        import base64
        img = _playwright_page.screenshot(type="png", full_page=True)
        b64 = base64.b64encode(img).decode("utf-8")

        # حفظ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"agent_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, fname)
        with open(filepath, "wb") as f:
            f.write(img)

        url = f"{PUBLIC_URL_BASE}/screenshots/{fname}"

        with agent_status_lock:
            agent_status["last_screenshot"] = url
            agent_status["last_action"] = "screenshot"

        update_dashboard_snapshot(
            page=_playwright_page,
            action="screenshot",
            screenshot=f"data:image/png;base64,{b64}",
            status="running" if agent_status.get("running") else "idle"
        )
        append_dashboard_log("Live screenshot captured", "success")

        return jsonify({
            "success": True,
            "url": url,
            "base64": b64
            })
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/agent/running', methods=['GET', 'POST'])
def set_agent_running():
    """تعيين حالة الـ Agent (يعمل أو متوقف)"""
    if request.method == 'GET':
        with agent_status_lock:
            return jsonify({
                "success": True,
                "running": agent_status["running"],
                "status": agent_status.copy()
            })

    if request.method == 'POST':
        data = request.json or {}
        running = data.get('running', False)
        with agent_status_lock:
            if running and not agent_status["running"]:
                agent_status["running"] = True
                agent_status["started_at"] = datetime.now().isoformat()
                logging.info("🟢 Agent marked as RUNNING")

                # Ensure browser/page is active when agent starts
                with _playwright_lock:
                    get_browser_context()

            elif (not running) and agent_status["running"]:
                agent_status["running"] = False
                agent_status["last_action"] = "stopped"
                logging.info("🔴 Agent marked as STOPPED")

        # Update dashboard snapshot (برا الـ lock بتاع agent_status عادي)
        with _dashboard_snapshot_lock:
            _browser_snapshot["status"] = "running" if running else "stopped"
            _browser_snapshot["last_action"] = "agent_state_change"
            _browser_snapshot["last_update"] = datetime.now().isoformat()

        append_dashboard_log(
            "Agent started" if running else "Agent stopped",
            "success" if running else "error"
        )
        broadcast_dashboard_update()
        return jsonify({"success": True, "running": agent_status["running"]})


@app.route('/agent/dashboard/update', methods=['POST'])
def update_agent_dashboard():
    """Receive live dashboard updates from external agent processes."""
    data = request.json or {}
    screenshot_base64 = data.get("screenshot_base64")
    screenshot = f"data:image/png;base64,{screenshot_base64}" if screenshot_base64 else None

    with _dashboard_snapshot_lock:
        if data.get("url") is not None:
            _browser_snapshot["url"] = data.get("url") or ""
        if data.get("title") is not None:
            _browser_snapshot["title"] = data.get("title") or ""
        if data.get("last_action") is not None:
            _browser_snapshot["last_action"] = data.get("last_action")
        if data.get("status") is not None:
            _browser_snapshot["status"] = data.get("status")
        if data.get("command_status") is not None:
            _browser_snapshot["command_status"] = data.get("command_status")
        if data.get("progress") is not None:
            _browser_snapshot["progress"] = data.get("progress")
        if screenshot is not None:
            _browser_snapshot["screenshot"] = screenshot
        _browser_snapshot["last_update"] = datetime.now().isoformat()

    message = data.get("log_message")
    if message:
        append_dashboard_log(message, data.get("log_level", "info"))
    broadcast_dashboard_update()
    return jsonify({"success": True})


@app.route('/agent/command', methods=['POST'])
def agent_command():
    """Execute dashboard command against the shared browser session."""
    global _playwright_page
    data = request.json or {}
    command = (data.get("command") or "").strip()
    if not command:
        return jsonify({"error": "command required"}), 400

    with _playwright_lock:
        if _playwright_page is None:
            get_browser_context()
        page = _playwright_page

    try:
        action_name = execute_dashboard_command(page, command)
        live_frame = capture_live_frame(page)
        update_dashboard_snapshot(
            page=page,
            action=action_name,
            screenshot=live_frame,
            status="running",
            command_status=f"Executed: {command}"
        )
        append_dashboard_log(f"Dashboard command executed: {command}", "success")
        return jsonify({
            "success": True,
            "action": action_name,
            "url": page.url,
            "title": page.title() if page else "",
            "screenshot": live_frame
        })
    except Exception as e:
        append_dashboard_log(f"Dashboard command failed: {command} ({e})", "error")
        update_dashboard_snapshot(
            page=page,
            action="command_failed",
            status="idle",
            command_status=f"Failed: {command}"
        )
        return jsonify({"error": str(e)}), 500

# ==================== INFERENCE ====================
def infer_extension_from_content(content) -> str:
    """استنتاج امتداد الملف من المحتوى"""
    if isinstance(content, dict):
        return "json"
    if not isinstance(content, str):
        return "bin"
    sample = content[:500].lower()
    
    if "import " in sample or "def " in sample or "class " in sample:
        return "py"
    if sample.strip().startswith("#") or "```" in sample:
        return "md"
    if "," in sample and sample.count("\n") > 2:
        return "csv"
    if "<html" in sample or "<!doctype" in sample:
        return "html"
    if "function " in sample or "const " in sample or "=>" in sample:
        return "js"
    
    return "txt"

def smart_add_extension(path: str, content) -> str:
    """إضافة امتداد تلقائي إذا لم يكن موجوداً"""
    if os.path.splitext(path)[1]:
        return path
    ext = infer_extension_from_content(content)
    return f"{path}.{ext}"

# ==================== CAPABILITIES ====================
@app.route('/capabilities', methods=['GET'])
def get_capabilities():
    """إرجاع صلاحيات الـ Agent"""
    return jsonify({
        "mode": "easy" if not READONLY_MODE else "readonly",
        "tools": {
            "safe": ["generate_uuid", "read_file", "list_dir", "get_file_metadata", "list_desktop_snapshot", "search_files"],
            "power": ["create_file", "create_folder", "execute_shell", "batch_mkdir_and_copy"],
            "playwright": ["launch_browser", "navigate", "get_text", "get_attribute", "click", "type_text", "screenshot", "wait_for_selector", "click_by_text", "close_browser", "evaluate_js", "get_current_url"]
        },
        "protection": "minimal"
    })

# ==================== FILE API (no restrictions, auto-fix permissions) ====================

def _grant_permissions(path: str):
    """icacls: grant Everyone full access"""
    import subprocess
    target = path if os.path.exists(path) else os.path.dirname(path)
    try:
        subprocess.run(
            ["icacls", target, "/grant", "Everyone:(F)", "/T", "/C", "/Q"],
            capture_output=True, timeout=15
        )
    except Exception:
        pass

def _read_file_direct(path: str) -> str:
    for enc in ["utf-8", "cp1256", "cp1252", "latin-1"]:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                return f.read(200000)
        except UnicodeDecodeError:
            continue
    return None

@app.route('/read-file', methods=['GET', 'POST'])
def read_file_api():
    """Read any file — GET ?path=C:\\file.py  or  POST {path}"""
    path = (request.args.get('path') or (request.json or {}).get('path', '')) if request.method in ('GET','POST') else ''
    if not path:
        return jsonify({"error": "path required"}), 400
    if not os.path.exists(path):
        return jsonify({"error": f"File not found: {path}"}), 404
    try:
        content = _read_file_direct(path)
        if content is None:
            return jsonify({"error": "Binary file"}), 400
        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    except PermissionError:
        _grant_permissions(path)
        try:
            content = _read_file_direct(path)
            return content or "", 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as e:
            return jsonify({"error": f"Permission denied even after fix: {e}"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/write-file', methods=['POST'])
def write_file_api():
    """Write/overwrite any file — POST {path, content}"""
    data = request.json or {}
    path = data.get('path', '')
    content = data.get('content', '')
    if not path:
        return jsonify({"error": "path required"}), 400
    def _write():
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    try:
        _write()
        return jsonify({"success": True, "path": path, "bytes": len(content)})
    except PermissionError:
        _grant_permissions(path)
        try:
            _write()
            return jsonify({"success": True, "path": path, "bytes": len(content), "note": "permissions auto-fixed"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/list-dir', methods=['GET', 'POST'])
def list_dir_api():
    """List directory contents — GET ?path=C:\\mcp-agent"""
    path = request.args.get('path') or (request.json or {}).get('path', 'C:\\mcp-agent')
    try:
        entries = []
        for e in os.listdir(path):
            full = os.path.join(path, e)
            try:
                size = os.path.getsize(full) if os.path.isfile(full) else 0
            except Exception:
                size = 0
            entries.append({"name": e, "type": "dir" if os.path.isdir(full) else "file", "size": size})
        return jsonify({"path": path, "entries": entries, "count": len(entries)})
    except PermissionError:
        _grant_permissions(path)
        try:
            entries = [{"name": e, "type": "dir" if os.path.isdir(os.path.join(path, e)) else "file"} for e in os.listdir(path)]
            return jsonify({"path": path, "entries": entries, "count": len(entries)})
        except Exception as e:
            return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/exec', methods=['POST'])
def exec_api():
    """Execute any shell command — POST {cmd, timeout?}
    Returns stdout, stderr, returncode"""
    import subprocess
    data = request.json or {}
    cmd = data.get('cmd') or data.get('command', '')
    timeout = int(data.get('timeout', 30))
    if not cmd:
        return jsonify({"error": "cmd required"}), 400
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='replace'
        )
        return jsonify({"stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode, "success": r.returncode == 0})
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Timeout after {timeout}s", "success": False}), 408
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/fix-permissions', methods=['POST', 'GET'])
def fix_permissions_api():
    """Grant Everyone full access to a path — POST {path} or GET ?path=..."""
    path = request.args.get('path') or (request.json or {}).get('path', '')
    if not path:
        return jsonify({"error": "path required"}), 400
    _grant_permissions(path)
    return jsonify({"success": True, "path": path, "action": "icacls /grant Everyone:(F) /T /C"})

# ==================== UNIFIED ENDPOINT ====================
@app.route('/mcp/safe', methods=['POST'])
def mcp_safe():
    """عمليات القراءة الآمنة"""
    data = request.json
    action = data.get("action")
    path = data.get("path")

    try:
        if action == "generate_uuid":
            return jsonify({"uuid": str(uuid.uuid4())})

        elif action == "read_file":
            if not os.path.exists(path):
                return jsonify({"error": "File not found"}), 404
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(50000)
                return jsonify({"content": content})
            except UnicodeDecodeError:
                return jsonify({"error": "Binary file - cannot read as text"}), 400
            except PermissionError:
                return jsonify({"error": "Permission denied"}), 403

        elif action == "list_dir":
            if not os.path.exists(path):
                return jsonify({"error": "Path not found"}), 404
            entries = os.listdir(path)
            return jsonify({"entries": entries})

        elif action == "get_file_metadata":
            if not os.path.exists(path):
                return jsonify({"error": "Path not found"}), 404
            stat = os.stat(path)
            return jsonify({
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_dir": os.path.isdir(path)
            })

        elif action == "list_desktop_snapshot":
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                return jsonify({"entries": []})
            entries = [
                {"name": e, "type": "dir" if os.path.isdir(os.path.join(desktop, e)) else "file"} 
                for e in os.listdir(desktop)
            ]
            return jsonify({"entries": entries})

        elif action == "search_files":
            # ✅ بحث في أي مكان بالجهاز (كل الـ drives)
            path = data.get('path')  # None = كل الجهاز
            pattern = data.get('pattern', '*')
            matches = []
            
            try:
                # لو مفيش path محدد، ابحث في كل الـ drives
                if path is None:
                    import string
                    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
                    search_paths = drives
                else:
                    search_paths = [path]
                
                # البحث في كل المسارات
                for search_path in search_paths:
                    try:
                        for root, dirs, files in os.walk(search_path):
                            # تخطي مجلدات النظام الحساسة
                            dirs[:] = [d for d in dirs if d not in ['System Volume Information', '$Recycle.Bin', 'Windows']]
                            
                            for file in fnmatch.filter(files, pattern):
                                matches.append(os.path.join(root, file))
                                
                                # حد أقصى 1000 نتيجة لتجنب التحميل الزائد
                                if len(matches) >= 1000:
                                    break
                            if len(matches) >= 1000:
                                break
                    except PermissionError:
                        continue  # تخطي المجلدات المحمية
                    except Exception:
                        continue
                        
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            
            return jsonify({
                "files": matches[:100],
                "total_found": len(matches),
                "truncated": len(matches) > 100,
                "searched_paths": search_paths if path is None else [path]
            })

        return jsonify({"error": "Unknown action"}), 400
    
    except Exception as e:
        logging.error(f"Error in safe operation: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== POWER ENDPOINT ====================
@app.route('/mcp/power', methods=['POST'])
def mcp_power():
    """عمليات الكتابة والتنفيذ - بدون Wake Token! 🔓"""
    
    if READONLY_MODE:
        return jsonify({"error": "System is in READONLY mode"}), 403

    data = request.json
    action = data.get("action")

    try:
        if action == "create_file":
            path = data.get("path")
            content = data.get("content", "")
            path = smart_add_extension(path, content)
            
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"✅ File created: {path}")
            return jsonify({"status": "success", "path": path})

        elif action == "create_folder":
            path = data.get("path")
            os.makedirs(path, exist_ok=True)
            logging.info(f"✅ Folder created: {path}")
            return jsonify({"status": "success", "path": path})

        elif action == "execute_shell":
            command = data.get("command")
            timeout = data.get("timeout", 30)
            
            logging.warning(f"⚠️ Executing: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            return jsonify({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })

        elif action == "batch_mkdir_and_copy":
            source_pattern = data.get('source_pattern')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_base = data.get("dest_base") or os.path.join(BACKUP_DIR, f"copy_{timestamp}")
            if not source_pattern:
                return jsonify({"error": "source_pattern required"}), 400
            for forbidden in ["C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)"]:
                if source_pattern.upper().startswith(forbidden.upper()):
                    return jsonify({"error": f"Blocked: {forbidden}"}), 403
            os.makedirs(dest_base, exist_ok=True)
            files = glob.glob(source_pattern, recursive=True)
            copied = []
            for fp in files:
                try:
                    dest = os.path.join(dest_base, os.path.basename(fp))
                    shutil.copy2(fp, dest)
                    copied.append(dest)
                except Exception as e:
                    logger.warning(f"Failed to copy {fp}: {e}")
            logger.info(f"Copied {len(copied)} files to {dest_base}")
            return jsonify({
                "success": True,
                "copied": len(copied),
                "destination": dest_base,
                "files": copied,
                "message": f"تم نسخ {len(copied)} ملف\nالمسار: {dest_base}"
            })

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        logging.error(f"Error in power operation: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== PLAYWRIGHT ENDPOINTS ====================
@app.route('/mcp/playwright', methods=['POST'])
def playwright_action():
    """Browser automation endpoints"""

    if READONLY_MODE:
        return jsonify({"error": "System is in READONLY mode"}), 403

    # ✅ Use global shared browser/page (IMPORTANT)
    global _playwright_pw, _playwright_browser, _playwright_context, _playwright_page

    data = request.json or {}
    action = data.get("action")

    try:
        if action == "launch_browser":
            # Launch browser (and keep page globally)
            with _playwright_lock:
                pw, br, ctx = get_browser_context()
                _playwright_pw, _playwright_browser, _playwright_context = pw, br, ctx

                if _playwright_page is None:
                    _playwright_page = _playwright_context.new_page()

            return jsonify({
                "status": "success",
                "browser": "chromium",
                "viewport": {"width": 1280, "height": 720}
            })

        elif action == "navigate":
            url = data.get("url", "")
            timeout = data.get("timeout", 30000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                return jsonify({"status": "success", "url": url})
            return jsonify({"error": "No active page"}), 400

        elif action == "get_text":
            selector = data.get("selector")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                element = page.wait_for_selector(selector, timeout=timeout)
                text = element.inner_text() if element else ""
                return jsonify({"text": text.strip()})
            return jsonify({"error": "No active page"}), 400

        elif action == "get_attribute":
            selector = data.get("selector")
            attribute = data.get("attribute")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                element = page.wait_for_selector(selector, timeout=timeout)
                value = element.get_attribute(attribute) if element else ""
                return jsonify({"value": value})
            return jsonify({"error": "No active page"}), 400

        elif action == "click":
            selector = data.get("selector")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                page.wait_for_selector(selector, timeout=timeout)
                page.click(selector)
                return jsonify({"status": "success"})
            return jsonify({"error": "No active page"}), 400

        elif action == "type_text":
            selector = data.get("selector")
            text = data.get("text", "")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                page.wait_for_selector(selector, timeout=timeout)
                page.fill(selector, text)
                return jsonify({"status": "success"})
            return jsonify({"error": "No active page"}), 400

        elif action == "screenshot":
            output_path = data.get("path")
            selector = data.get("selector", None)
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if not page:
                return jsonify({"error": "No active page"}), 400

            if selector:
                element = page.wait_for_selector(selector, timeout=timeout)
                if not element:
                    return jsonify({"error": "Selector not found"}), 404
                element.screenshot(path=output_path)
            else:
                page.screenshot(path=output_path, full_page=True)

            return jsonify({"status": "success", "path": output_path})

        elif action == "wait_for_selector":
            selector = data.get("selector")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                page.wait_for_selector(selector, timeout=timeout)
                return jsonify({"status": "success"})
            return jsonify({"error": "No active page"}), 400

        elif action == "click_by_text":
            text = data.get("text", "")
            timeout = data.get("timeout", 10000)

            with _playwright_lock:
                page = _playwright_page

            if page:
                page.click(f"text={text}", timeout=timeout)
                return jsonify({"status": "success"})
            return jsonify({"error": "No active page"}), 400

        elif action == "evaluate_js":
            script = data.get("script")

            with _playwright_lock:
                page = _playwright_page

            if page:
                result = page.evaluate(script)
                return jsonify({"result": result})
            return jsonify({"error": "No active page"}), 400

        elif action == "get_current_url":
            with _playwright_lock:
                page = _playwright_page

            if page:
                return jsonify({"url": page.url})
            return jsonify({"error": "No active page"}), 400

        elif action == "close_browser":
            with _playwright_lock:
                try:
                    if _playwright_context:
                        _playwright_context.close()
                    if _playwright_browser:
                        _playwright_browser.close()
                    if _playwright_pw:
                        _playwright_pw.stop()
                finally:
                    _playwright_page = None
                    _playwright_context = None
                    _playwright_browser = None
                    _playwright_pw = None

            return jsonify({"status": "success"})

        return jsonify({"error": "Unknown action"}), 400

    except Exception as e:
        logging.error(f"Error in playwright operation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ws/stream', methods=['GET'])
def stream_websocket():
    """WebSocket endpoint للـ Live Stream"""
    return jsonify({
        "error": "This endpoint is not a WebSocket endpoint.",
        "stream_endpoint": "/stream/events"
    }), 410

@app.route('/stream/events', methods=['GET'])
def stream_events():
    """SSE endpoint for the live stream page."""
    def event_stream():
        global _dashboard_active
        _dashboard_active = True
        try:
            last_payload = None
            while True:
                payload = build_stream_snapshot()
                serialized = json.dumps(payload)
                if serialized != last_payload:
                    yield f"data: {serialized}\n\n"
                    last_payload = serialized
                time.sleep(1)
        except GeneratorExit:
            _dashboard_active = False
        finally:
            _dashboard_active = False

    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Return the Live Dashboard HTML"""
    return render_template("dashboard.html")

@app.route('/stream', methods=['GET'])
def stream_page():
    """Return the Live Stream HTML"""
    return render_template("stream.html")

@app.route('/api/dashboard/status', methods=['GET'])
def get_dashboard_status():
    """Get current dashboard status"""
    with _dashboard_snapshot_lock:
        return jsonify({
            "active": _dashboard_active,
            "snapshot": _browser_snapshot.copy()
        })



# ======================================================
#  WordPress Integration Layer
# ======================================================
try:
    from wp_routes        import wp_bp
    from system_awareness import system_awareness
    from feedback_loop    import feedback_loop
    from knowledge_manager import knowledge_manager
    from llm_bridge       import llm_bridge
    from tool_registry    import tool_registry, ToolType
    from agent_core       import AgentCore as _AgentCore
    from wp_manager       import wp_manager as _wp_manager

    app.register_blueprint(wp_bp)

    _shared_agent = None

    def _get_agent():
        global _shared_agent
        if _shared_agent is None:
            _shared_agent = _AgentCore()
            tool_registry.register("memory_engine",   ToolType.MEMORY,    _shared_agent.memory,    "Execution memory",    1)
            tool_registry.register("pattern_engine",  ToolType.ANALYSIS,  _shared_agent.pattern,   "Error patterns",      2)
            tool_registry.register("strategy_engine", ToolType.ANALYSIS,  _shared_agent.strategy,  "Strategy engine",     2)
            tool_registry.register("system_executor", ToolType.EXECUTION, _shared_agent.executor,  "Shell execution",     3)
            tool_registry.register("knowledge_mgr",   ToolType.KNOWLEDGE, knowledge_manager,        "Knowledge base",      1)
            tool_registry.register("llm_bridge",      ToolType.LLM,       llm_bridge,               "LLM interface",       1)
            tool_registry.register("wp_manager",      ToolType.WP,        _wp_manager,              "WP multi-site",       1)
            feedback_loop.on_result(
                lambda r: logger.info("[FB] " + ("OK" if r["success"] else "FAIL") + " " + r["task"][:40])
            )
        return _shared_agent

    _get_agent()
    system_awareness.start_heartbeat(_wp_manager, interval=60)
    _wp_manager.start_heartbeat(interval=60)
    logger.info("WordPress Integration Layer loaded OK")

except Exception as _wp_init_err:
    import logging as _log
    _log.getLogger("server").warning(f"WordPress layer optional: {_wp_init_err}")


@app.route("/run", methods=["POST"])
def run_task():
    import time as _t
    data      = request.get_json(force=True) or {}
    task      = data.get("task", "")
    site      = data.get("site")
    all_sites = data.get("all_sites", False)
    explain   = data.get("explain", False)
    if not task:
        return jsonify({"error": "task required"}), 400
    try:
        agent = _get_agent()
        system_awareness.begin_task(task, tool="agent_core", site=site)
        t0 = _t.time()
        if all_sites:
            result = agent.execute_on_all_sites(task)
        elif site:
            result = agent.execute_wordpress_task(site, task)
        else:
            result = agent.handle_task(task, explain=explain)
        dur    = _t.time() - t0
        r_dict = result if isinstance(result, dict) else {"result": result, "status": "completed"}
        r_dict.setdefault("success", True)
        r_dict.setdefault("status", "completed")
        system_awareness.end_task(success=True)
        feedback_loop.record(
            task=task, result=r_dict, tool="agent_core",
            site=site or "", duration=dur,
            memory_engine=agent.memory,
            strategy_engine=agent.strategy
        )
        return jsonify(r_dict)
    except Exception as e:
        system_awareness.end_task(success=False)
        return jsonify({"error": str(e), "status": "failed"}), 500


@app.route("/knowledge/upload", methods=["POST"])
def knowledge_upload():
    import tempfile as _tmp
    f    = request.files.get("file")
    tags = request.form.get("tags", "").split(",")
    if not f:
        return jsonify({"success": False, "reason": "no file"}), 400
    ext  = os.path.splitext(f.filename)[1]
    tmp  = _tmp.mktemp(suffix=ext)
    f.save(tmp)
    res  = knowledge_manager.learn_from_file(tmp, tags=[t.strip() for t in tags if t.strip()])
    try:
        os.remove(tmp)
    except Exception:
        pass
    return jsonify(res)


@app.route("/system/status", methods=["GET"])
def system_full_status():
    return jsonify({
        "awareness":    system_awareness.get_snapshot(),
        "tools":        tool_registry.get_all_status(),
        "tools_health": tool_registry.health_check(),
        "feedback":     feedback_loop.get_stats(),
        "knowledge":    knowledge_manager.get_stats(),
        "llm":          llm_bridge.get_config(),
        "improvements": feedback_loop.suggest_improvements(),
    })


@app.route("/llm/configure", methods=["POST"])
def configure_llm():
    data = request.get_json(force=True) or {}
    llm_bridge.configure(
        provider=data.get("provider", "mock"),
        api_key=data.get("api_key", ""),
        model=data.get("model", ""),
        base_url=data.get("base_url", ""),
    )
    return jsonify({"success": True, "config": llm_bridge.get_config()})


@app.route("/wp-dashboard", methods=["GET"])
def wp_dashboard_page():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "wp-dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        return content, 200, headers
    return "WordPress Dashboard not found", 404



# ══════════════════════════════════════════════
#  Startup: Restore Sites + Health Monitor
# ══════════════════════════════════════════════

try:
    from sites_store   import sites_store, restore_sites_to_manager
    from health_monitor import health_monitor
    from wp_manager    import wp_manager as _wpm_startup

    # Restore saved sites from DB
    _restored = restore_sites_to_manager(_wpm_startup)
    if _restored:
        logger.info(f"Restored {_restored} WordPress sites from database")

    # Start health monitoring
    health_monitor.start(_wpm_startup, interval=60)

    # Wire health events to dashboard
    def _on_health_event(event):
        append_dashboard_log(
            f"[HEALTH] {event['type']} — {event['source']}",
            "warn" if "down" in event["type"] else "info"
        )
    health_monitor.on_event(_on_health_event)

    # Add /health route
    @app.route("/health", methods=["GET"])
    def agent_health():
        return jsonify({
            "status":  "ok",
            "monitor": health_monitor.get_summary(),
            "system":  system_awareness.get_snapshot(),
        })

    @app.route("/health/events", methods=["GET"])
    def health_events_direct():
        return jsonify({
            "events": health_monitor.get_recent_events(
                int(request.args.get("limit", 50))
            )
        })

    # Patch /wp/register-site to also persist
    _orig_register = None  # wp_routes handles this already

    logger.info("Health Monitor + Sites Store active")

except Exception as _hm_err:
    logger.warning(f"Health Monitor optional: {_hm_err}")

if __name__ == "__main__":
    local_base = f"http://127.0.0.1:{REST_PORT}"
    logger.info(f"REST Server on {REST_HOST}:{REST_PORT}")
    logger.info(f"Screenshots: {PUBLIC_URL_BASE}/screenshots/")
    logger.info("Keep-alive: 30s interval")
    logger.info(f"Dashboard (local): {local_base}/dashboard")
    logger.info(f"Live Stream (local): {local_base}/stream")
    if PUBLIC_URL_BASE != local_base:
        logger.info(f"Dashboard (public): {PUBLIC_URL_BASE}/dashboard")
        logger.info(f"Live Stream (public): {PUBLIC_URL_BASE}/stream")

    # Initialize SocketIO
    init_socketio()
    register_socketio_handlers()

    # Run with SocketIO
    socketio.run(app, host=REST_HOST, port=REST_PORT)
