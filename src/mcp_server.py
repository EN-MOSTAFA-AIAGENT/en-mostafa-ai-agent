from fastmcp import FastMCP
import base64
import httpx
import logging
import os
import asyncio
import re
import atexit
import signal
from playwright.async_api import async_playwright, Error as PlaywrightError
from datetime import datetime
from contextlib import asynccontextmanager
from memory import agent_memory
import socket

READONLY_MODE = os.environ.get("READONLY_MODE", "true").lower() == "true"
REST_API_BASE = os.environ.get("REST_API_BASE", "http://127.0.0.1:5001").rstrip("/")
PUBLIC_URL_BASE = os.environ.get("PUBLIC_URL_BASE", REST_API_BASE).rstrip("/")
os.environ.setdefault("FASTMCP_HOST", os.environ.get("MCP_HOST", "127.0.0.1"))
os.environ.setdefault("FASTMCP_PORT", os.environ.get("MCP_PORT", "8000"))
SAFE_URL = f"{REST_API_BASE}/mcp/safe"
POWER_URL = f"{REST_API_BASE}/mcp/power"
DASHBOARD_UPDATE_URL = f"{REST_API_BASE}/agent/dashboard/update"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MCP")
app = FastMCP("MOSTAFA AI 🚀")

# ==================== RETRY HELPER ====================
async def retry_async(func, max_retries: int = 2, delay: float = 1.0, *args, **kwargs):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                logger.warning(f"Timeout on attempt {attempt+1}/{max_retries+1}")
            elif "connection" in error_msg or "network" in error_msg:
                logger.warning(f"Network error on attempt {attempt+1}/{max_retries+1}")
            elif "not found" in error_msg or "404" in error_msg:
                logger.error(f"Resource not found - no retry")
                raise
            else:
                logger.warning(f"Error on attempt {attempt+1}/{max_retries+1}: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 1.5
    logger.error(f"All {max_retries+1} attempts failed")
    raise last_error

# ==================== ASYNC HTTP WITH KEEP-ALIVE ====================
_async_client: httpx.AsyncClient = None

async def get_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0, read=45.0, write=30.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=60.0
            )
        )
    return _async_client

async def call_api(url: str, action: str, payload: dict = None, timeout: int = 30) -> dict:
    async def _call():
        client = await get_client()
        data = {"action": action, **(payload or {})}
        resp = await client.post(url, json=data, timeout=timeout)
        if resp.status_code >= 400:
            body = resp.text[:200] if resp.text else "No details"
            raise RuntimeError(f"API Error {resp.status_code}: {body}")
        return resp.json()
    return await retry_async(_call, max_retries=2, delay=1.0)


async def push_dashboard_update(
    *,
    page=None,
    action: str = None,
    status: str = "running",
    log_message: str = None,
    log_level: str = "info",
    include_screenshot: bool = False,
    command_status: str = None,
    progress: int = None
) -> None:
    payload = {
        "status": status,
        "last_action": action,
        "command_status": command_status,
        "progress": progress,
        "log_message": log_message,
        "log_level": log_level,
    }
    if page is not None:
        try:
            payload["url"] = page.url
        except Exception:
            pass
        try:
            payload["title"] = await page.title()
        except Exception:
            pass
        if include_screenshot:
            try:
                img = await page.screenshot(type="png")
                payload["screenshot_base64"] = base64.b64encode(img).decode("utf-8")
            except Exception:
                pass

    try:
        client = await get_client()
        await client.post(DASHBOARD_UPDATE_URL, json=payload, timeout=10.0)
    except Exception as e:
        logger.debug(f"Dashboard update skipped: {e}")

# ==================== BROWSER POOL WITH KEEP-ALIVE ====================
class BrowserPool:
    def __init__(self, size: int = 3):
        self.size = size
        self._pool, self._lock, self._pw = [], asyncio.Lock(), None
        self._last_used = {}

    async def init(self):
        if self._pw: return
        self._pw = await async_playwright().start()
        for _ in range(self.size):
            browser = await self._pw.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
            )
            ctx = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self._pool.append({"browser": browser, "context": ctx, "busy": False})
        logger.info(f"Browser pool: {self.size}")

    @asynccontextmanager
    async def get_page(self):
        page, entry = None, None
        async with self._lock:
            for e in self._pool:
                if not e["busy"]:
                    e["busy"], entry = True, e
                    page = await e["context"].new_page()
                    break
        if not page:
            logger.warning("Browser pool busy, waiting...")
            await asyncio.sleep(0.5)
            async with self._lock:
                for e in self._pool:
                    if not e["busy"]:
                        e["busy"], entry = True, e
                        page = await e["context"].new_page()
                        break
        if not page:
            raise RuntimeError("Browser pool exhausted")
        try:
            yield page
        finally:
            async with self._lock:
                if page:
                    try: await page.close()
                    except: pass
                if entry:
                    entry["busy"] = False

    async def close(self):
        for e in self._pool:
            try:
                await e["context"].close()
                await e["browser"].close()
            except: pass
        if self._pw:
            await self._pw.stop()
        self._pw = None
        logger.info("Browser pool closed")

browser_pool = BrowserPool()

# ==================== CLEANUP ====================
async def cleanup():
    global _async_client
    if _async_client:
        await _async_client.aclose()
        _async_client = None
    await browser_pool.close()
    logger.info("Cleanup done")

def sync_cleanup():
    try: asyncio.get_event_loop().run_until_complete(cleanup())
    except: pass

atexit.register(sync_cleanup)
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda s,f: (sync_cleanup(), exit(0)))

# ==================== MEMORY TOOLS ====================
@app.tool()
def set_context(key: str, value: str) -> str:
    agent_memory.store(key, value)
    return f"Saved: {key}"

@app.tool()
def get_context(key: str) -> str:
    return str(agent_memory.retrieve(key) or "Not found")

@app.tool()
def get_memory_summary() -> str:
    return agent_memory.get_context_summary()

@app.tool()
def clear_memory() -> str:
    agent_memory.clear_all()
    return "Cleared"

@app.tool()
def set_project(name: str, desc: str = "") -> str:
    agent_memory.store("project_name", name)
    agent_memory.store("project_description", desc)
    return f"Project: {name}"

# ==================== FILE TOOLS ====================
@app.tool()
async def generate_uuid() -> str:
    """توليد UUID فريد"""
    result = await call_api(SAFE_URL, "generate_uuid")
    logger.info("✅ UUID generated")
    return result.get("uuid", "")

@app.tool()
async def read_file(path: str) -> str:
    cached = agent_memory.retrieve(f"file:{path}")
    if cached:
        logger.info(f"Cache hit: {path}")
        return cached
    try:
        result = await call_api(SAFE_URL, "read_file", {"path": path})
        content = result.get("content", "")
        agent_memory.store(f"file:{path}", content, ttl=300)
        return content
    except Exception as e:
        if "Binary file" in str(e):
            return "Cannot read: Binary file"
        raise

@app.tool()
async def list_dir(path: str) -> list:
    return (await call_api(SAFE_URL, "list_dir", {"path": path})).get("entries", [])

@app.tool()
async def get_file_metadata(path: str) -> dict:
    return await call_api(SAFE_URL, "get_file_metadata", {"path": path})

@app.tool()
async def list_desktop_snapshot() -> dict:
    return await call_api(SAFE_URL, "list_desktop_snapshot")

@app.tool()
async def search_files(path: str = None, pattern: str = "*") -> dict:
    return await call_api(SAFE_URL, "search_files", {"path": path, "pattern": pattern}, timeout=60)

@app.tool()
async def create_file(path: str, content: str = "") -> dict:
    return await call_api(POWER_URL, "create_file", {"path": path, "content": content})

@app.tool()
async def create_folder(path: str) -> dict:
    return await call_api(POWER_URL, "create_folder", {"path": path})

@app.tool()
async def execute_shell(cmd: str, timeout: int = 30) -> dict:
    r = await call_api(POWER_URL, "execute_shell", {"command": cmd, "timeout": timeout}, timeout=timeout+5)
    return {"output": r.get("stdout",""), "error": r.get("stderr",""), "success": r.get("returncode",0)==0}

@app.tool()
async def batch_mkdir_and_copy(source_root: str, pattern: str = "**/*", dest_base: str = None) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_base or os.path.join(os.path.expanduser("~"), "Desktop", "Agent_Backups", f"copy_{timestamp}")
    for forbidden in ["C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)"]:
        if source_root.upper().startswith(forbidden.upper()):
            return {"error": f"Blocked: {forbidden}"}
    return await call_api(POWER_URL, "batch_mkdir_and_copy", {"source_pattern": f"{source_root}\\{pattern}", "dest_base": dest})

# ==================== PAGE LOAD WITH RETRY ====================
async def wait_loaded(page, timeout=45000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightError:
        pass
    try:
        await page.evaluate("""() => Promise.all(
            Array.from(document.images).filter(i => !i.complete)
            .map(i => new Promise(r => {i.onload=i.onerror=()=>r(); setTimeout(r,5000)}))
        )""")
    except: pass
    try:
        await page.evaluate("() => document.fonts.ready")
    except: pass
    try:
        await page.evaluate("window.scrollTo(0,document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo(0,0)")
        await page.wait_for_timeout(2000)
    except: pass

async def safe_navigate(page, url: str, timeout: int = 45000) -> bool:
    async def _navigate():
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        return True
    try:
        return await retry_async(_navigate, max_retries=2, delay=2.0)
    except Exception as e:
        logger.error(f"Failed to navigate to {url}: {e}")
        return False

async def analyze_dom(page) -> dict:
    try:
        return await page.evaluate("""() => ({
            heading_count: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
            image_count: document.querySelectorAll('img').length,
            link_count: document.querySelectorAll('a').length,
            h1_count: document.querySelectorAll('h1').length,
            has_viewport: !!document.querySelector('meta[name="viewport"]'),
            images_no_alt: document.querySelectorAll('img:not([alt])').length,
            ux_score: Math.max(0, 100 - document.querySelectorAll('img:not([alt])').length*5 - (document.querySelectorAll('h1').length>1?10:0) - (!document.querySelector('meta[name="viewport"]')?20:0))
        })""")
    except Exception:
        return {}

# ==================== SMART SCREENSHOT WITH RETRY ====================
@app.tool()
async def smart_screenshot(url: str, full_page: bool = True, analyze: bool = True) -> dict:
    await browser_pool.init()
    async def _take_screenshot():
        async with browser_pool.get_page() as page:
            if not await safe_navigate(page, url):
                raise RuntimeError(f"Failed to load: {url}")
            await wait_loaded(page)
            title = await page.title() or ""
            final_url = page.url
            dom = await analyze_dom(page) if analyze else {}
            img = await page.screenshot(type="png", full_page=full_page)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{re.sub(r'[^a-zA-Z0-9]','_',url)[:40]}_{ts}.png"
            with open(os.path.join(SCREENSHOTS_DIR, fname), "wb") as f:
                f.write(img)
            public_url = f"{PUBLIC_URL_BASE}/screenshots/{fname}"
            agent_memory.add_interaction({"action": "screenshot", "url": url, "result": public_url})
            return {
                "success": True, "url": final_url, "title": title,
                "screenshot_url": public_url, "dom_analysis": dom,
                "message": f"Screenshot saved!\n{public_url}\nUX Score: {dom.get('ux_score','?')}/100"
            }
    return await retry_async(_take_screenshot, max_retries=2, delay=2.0)

# ==================== UX ANALYSIS WITH RETRY ====================
@app.tool()
async def analyze_ux(url: str) -> dict:
    await browser_pool.init()
    async def _analyze():
        async with browser_pool.get_page() as page:
            if not await safe_navigate(page, url):
                raise RuntimeError(f"Failed to load: {url}")
            await wait_loaded(page)
            ux = await page.evaluate("""() => {
                const r = {
                    title: document.title, url: location.href, lang: document.documentElement.lang||'?',
                    words: document.body.innerText.split(/\\s+/).length,
                    headings: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
                    images: document.querySelectorAll('img').length, links: document.querySelectorAll('a').length,
                    img_alt: document.querySelectorAll('img[alt]').length,
                    img_no_alt: document.querySelectorAll('img:not([alt])').length,
                    h1_count: document.querySelectorAll('h1').length,
                    has_viewport: !!document.querySelector('meta[name="viewport"]'),
                    issues: [], score: 100
                };
                if(r.img_no_alt>0) { r.issues.push(`${r.img_no_alt} images missing alt`); r.score-=10; }
                if(r.h1_count===0) { r.issues.push('No H1'); r.score-=15; }
                else if(r.h1_count>1) { r.issues.push(`Multiple H1: ${r.h1_count}`); r.score-=5; }
                if(!r.has_viewport) { r.issues.push('No viewport'); r.score-=20; }
                r.score = Math.max(0, r.score);
                return r;
            }""")
            img = await page.screenshot(type="png", full_page=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"ux_{ts}.png"
            with open(os.path.join(SCREENSHOTS_DIR, fname), "wb") as f:
                f.write(img)
            ux["screenshot_url"] = f"{PUBLIC_URL_BASE}/screenshots/{fname}"
            ux["summary"] = f"UX Score: {ux['score']}/100\nIssues: {len(ux['issues'])}\n{ux['screenshot_url']}"
            return ux
    return await retry_async(_analyze, max_retries=2, delay=2.0)

# ==================== WEBSITE SUMMARY WITH RETRY ====================
@app.tool()
async def website_summary(url: str) -> dict:
    await browser_pool.init()
    async def _summary():
        async with browser_pool.get_page() as page:
            if not await safe_navigate(page, url):
                raise RuntimeError(f"Failed to load: {url}")
            await wait_loaded(page)
            s = await page.evaluate("""() => {
                const m = n => document.querySelector(`meta[name="${n}"],meta[property="${n}"]`)?.content;
                return {
                    title: document.title, url: location.href,
                    desc: m('description')||m('og:description'),
                    lang: document.documentElement.lang||'?',
                    h1: document.querySelector('h1')?.textContent?.trim()||'None',
                    h2_count: document.querySelectorAll('h2').length,
                    images: document.querySelectorAll('img').length,
                    links: document.querySelectorAll('a').length,
                    viewport: !!document.querySelector('meta[name="viewport"]')
                };
            }""")
            img = await page.screenshot(type="jpeg", quality=80, full_page=False)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"summary_{ts}.jpg"
            with open(os.path.join(SCREENSHOTS_DIR, fname), "wb") as f:
                f.write(img)
            s["screenshot_url"] = f"{PUBLIC_URL_BASE}/screenshots/{fname}"
            return s
    return await retry_async(_summary, max_retries=2, delay=2.0)

# ==================== BACKWARD-COMPATIBLE PLAYWRIGHT TOOLS ====================
_browser_context = {"playwright": None, "browser": None, "context": None, "page": None}
_browser_lock = asyncio.Lock()

async def _ensure_browser_internal() -> None:
    """Ensure Playwright browser/page are ready (internal)."""
    if _browser_context.get("page"):
        return
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context(viewport={'width': 1280, 'height': 720}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = await ctx.new_page()
    _browser_context.update({"playwright": pw, "browser": browser, "context": ctx, "page": page})

async def _close_browser_internal() -> None:
    """Close page/context/browser/playwright safely (internal)."""
    try:
        if _browser_context.get("page"): await _browser_context["page"].close()
        if _browser_context.get("context"): await _browser_context["context"].close()
        if _browser_context.get("browser"): await _browser_context["browser"].close()
        if _browser_context.get("playwright"): await _browser_context["playwright"].stop()
    except: pass
    finally: _browser_context.update({"page": None, "context": None, "browser": None, "playwright": None})


def is_port_listening(host: str, port: int) -> bool:
    probe_host = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((probe_host, port)) == 0

@app.tool()
async def launch_browser() -> str:
    logger.info("Launching browser...")
    async with _browser_lock:
        if _browser_context.get("page"):
            await _close_browser_internal()
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await push_dashboard_update(
        page=page,
        action="launch_browser",
        status="idle",
        log_message="Browser launched from MCP",
        log_level="success",
        include_screenshot=True,
        command_status="Browser ready"
    )
    logger.info("Browser launched successfully")
    return "Browser launched: Chromium headless mode (1280x720)"

@app.tool()
async def navigate(url: str, timeout: int = 30000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    logger.info(f"🚀 Navigating to: {url}")
    await page.goto(url, timeout=timeout, wait_until="networkidle")
    await page.wait_for_timeout(1500)
    await push_dashboard_update(
        page=page,
        action="navigate",
        status="running",
        log_message=f"Navigated to {url}",
        log_level="success",
        include_screenshot=True,
        command_status=f"Navigated: {url}"
    )
    logger.info("✅ Navigated successfully")
    return f"Successfully navigated to: {url}"

@app.tool()
async def get_text(selector: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    element = await page.wait_for_selector(selector, timeout=timeout)
    text = await element.inner_text()
    await push_dashboard_update(
        page=page,
        action="get_text",
        status="idle",
        log_message=f"Read text from selector: {selector}",
        command_status=f"Read selector: {selector}"
    )
    return text.strip()

@app.tool()
async def get_attribute(selector: str, attribute: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    element = await page.wait_for_selector(selector, timeout=timeout)
    value = await element.get_attribute(attribute)
    await push_dashboard_update(
        page=page,
        action="get_attribute",
        status="idle",
        log_message=f"Read attribute {attribute} from {selector}",
        command_status=f"Read attribute: {attribute}"
    )
    return value or ""

@app.tool()
async def click(selector: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await page.wait_for_selector(selector, timeout=timeout)
    await page.click(selector)
    await push_dashboard_update(
        page=page,
        action="click",
        status="running",
        log_message=f"Clicked selector: {selector}",
        log_level="success",
        include_screenshot=True,
        command_status=f"Clicked: {selector}"
    )
    return "Element clicked successfully"

@app.tool()
async def type_text(selector: str, text: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await page.wait_for_selector(selector, timeout=timeout)
    await page.fill(selector, text)
    await push_dashboard_update(
        page=page,
        action="type_text",
        status="running",
        log_message=f"Typed text into selector: {selector}",
        log_level="success",
        include_screenshot=True,
        command_status=f"Typed into: {selector}"
    )
    return "Text typed successfully"

@app.tool()
async def screenshot(path: str, selector: str = None, full_page: bool = False, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if selector:
        element = await page.wait_for_selector(selector, timeout=timeout)
        await element.screenshot(path=path)
    else:
        await page.screenshot(path=path, full_page=full_page)
    await push_dashboard_update(
        page=page,
        action="screenshot",
        status="running",
        log_message=f"Screenshot saved to: {path}",
        log_level="success",
        include_screenshot=True,
        command_status="Screenshot captured"
    )
    return f"Screenshot saved to: {path}"

@app.tool()
async def wait_for_selector(selector: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await page.wait_for_selector(selector, timeout=timeout)
    await push_dashboard_update(
        page=page,
        action="wait_for_selector",
        status="idle",
        log_message=f"Selector became available: {selector}",
        command_status=f"Found: {selector}"
    )
    return "Element found"

@app.tool()
async def click_by_text(text: str, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await page.click(f"text={text}", timeout=timeout)
    await push_dashboard_update(
        page=page,
        action="click_by_text",
        status="running",
        log_message=f"Clicked text: {text}",
        log_level="success",
        include_screenshot=True,
        command_status=f"Clicked text: {text}"
    )
    return "Element clicked by text"

@app.tool()
async def evaluate_js(script: str) -> dict:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    result = await page.evaluate(script)
    await push_dashboard_update(
        page=page,
        action="evaluate_js",
        status="idle",
        log_message="Executed custom JavaScript",
        command_status="JavaScript executed"
    )
    return {"result": result}

@app.tool()
async def get_current_url() -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await push_dashboard_update(
        page=page,
        action="get_current_url",
        status="idle",
        command_status="Fetched current URL"
    )
    return page.url

@app.tool()
async def close_browser() -> str:
    current_page = None
    async with _browser_lock:
        current_page = _browser_context.get("page")
        await _close_browser_internal()
    await push_dashboard_update(
        page=current_page,
        action="close_browser",
        status="stopped",
        log_message="Browser closed from MCP",
        log_level="error",
        command_status="Browser closed"
    )
    logger.info("✅ Browser and Playwright stopped successfully")
    return "Browser closed successfully"

@app.tool()
async def screenshot_base64(full_page: bool = False, timeout: int = 10000) -> str:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    data = await page.screenshot(full_page=full_page, type="png")
    await push_dashboard_update(
        page=page,
        action="screenshot_base64",
        status="running",
        log_message="Live frame pushed to dashboard",
        include_screenshot=False,
        command_status="Live frame captured"
    )
    return base64.b64encode(data).decode("utf-8")

@app.tool()
async def render_site(
    url: str,
    full_page: bool = False,
    timeout: int = 30000,
    wait_until: str = "networkidle",
    settle_ms: int = 800,
    fmt: str = "jpeg",
    quality: int = 60
) -> dict:
    async with _browser_lock:
        await _ensure_browser_internal()
        page = _browser_context["page"]
    await page.goto(url, timeout=timeout, wait_until=wait_until)
    if settle_ms > 0:
        await page.wait_for_timeout(settle_ms)
    title = ""
    try: title = await page.title()
    except: pass
    final_url = page.url
    if fmt.lower() in ("jpg", "jpeg"):
        img = await page.screenshot(type="jpeg", quality=int(quality), full_page=full_page)
        mime = "image/jpeg"
    else:
        img = await page.screenshot(type="png", full_page=full_page)
        mime = "image/png"
    return {
        "url": final_url, "title": title, "mime": mime,
        "base64": base64.b64encode(img).decode("utf-8"),
        "viewport": {"width": 1280, "height": 720}
    }

@app.tool()
def html_preview(url: str, timeout: int = 15) -> dict:
    try:
        r = httpx.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        html = r.text or ""
    except Exception as e:
        return {"url": url, "error": str(e)}
    m_title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = m_title.group(1).strip() if m_title else ""
    m_og = re.search(r"<meta[^>]+property=['\"]og:image['\"][^>]+content=['\"]([^'\"]+)['\"]", html, re.I)
    og_image = m_og.group(1).strip() if m_og else ""
    return {"url": url, "title": title, "og_image": og_image}

# ==================== RUN ====================
if __name__ == "__main__":
    logger.info(f"MCP Server on {app.settings.host}:{app.settings.port}")
    logger.info(f"Screenshots: {PUBLIC_URL_BASE}/screenshots/")
    logger.info(f"REST API Base: {REST_API_BASE}")
    logger.info("Auto-retry: 2 attempts per operation")
    logger.info("Keep-alive: 60s HTTP, browser pool persistent")

    # Note: Browser pool will be initialized on first use
    # This avoids blocking startup and event loop issues
    logger.info("Server starting... (browser pool will init on demand)")
    if is_port_listening(app.settings.host, app.settings.port):
        logger.warning(
            f"Port {app.settings.port} is already in use. "
            "Skipping MCP startup to avoid duplicate bind; free the port or set MCP_PORT/FASTMCP_PORT if needed."
        )
        raise SystemExit(0)
    app.run(transport="sse")
