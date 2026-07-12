import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser as AsyncBrowser, BrowserContext as AsyncContext, Page as AsyncPage
from playwright.sync_api import sync_playwright, Browser as SyncBrowser, Page as SyncPage

from logger_system import get_logger

logger = get_logger("browser_manager")


class BrowserManager:
    """
    مدير مركزي للـ Playwright (Async + Sync) مع دعم إعادة الاستخدام
    """

    def __init__(self):
        """
        تهيئة المتغيرات الداخلية
        """
        self._async_pw = None
        self._async_browser: Optional[AsyncBrowser] = None
        self._async_contexts = []

        self._sync_pw = None
        self._sync_browser: Optional[SyncBrowser] = None
        self._sync_page: Optional[SyncPage] = None

        self._lock = asyncio.Lock()

    # ==================== ASYNC ====================

    async def start_async_browser(self):
        """
        تشغيل المتصفح async إذا لم يكن يعمل
        """
        async with self._lock:
            if self._async_browser is not None:
                return self._async_browser

            try:
                self._async_pw = await async_playwright().start()
                self._async_browser = await self._async_pw.chromium.launch(headless=True)
                logger.info("Async browser started")
                return self._async_browser

            except Exception as e:
                logger.error("Failed to start async browser", error=e)
                raise

    async def get_context(self) -> AsyncContext:
        """
        الحصول على context جديد أو إعادة استخدام موجود
        """
        try:
            browser = await self.start_async_browser()
            context = await browser.new_context()
            self._async_contexts.append(context)
            logger.debug("New async context created")
            return context

        except Exception as e:
            logger.error("Failed to create async context", error=e)
            raise

    async def new_page(self) -> AsyncPage:
        """
        إنشاء صفحة جديدة داخل context
        """
        try:
            context = await self.get_context()
            page = await context.new_page()
            logger.debug("New async page created")
            return page

        except Exception as e:
            logger.error("Async new_page failed", error=e)
            raise

    async def close(self):
        """
        إغلاق جميع موارد async
        """
        try:
            for ctx in self._async_contexts:
                await ctx.close()

            if self._async_browser:
                await self._async_browser.close()

            if self._async_pw:
                await self._async_pw.stop()

            self._async_browser = None
            self._async_pw = None
            self._async_contexts = []

            logger.info("Async browser closed")

        except Exception as e:
            logger.error("Error closing async browser", error=e)
            raise

    # ==================== SYNC ====================

    def start_sync_browser(self):
        """
        تشغيل المتصفح sync كـ fallback
        """
        if self._sync_browser is not None:
            return self._sync_browser

        try:
            self._sync_pw = sync_playwright().start()
            self._sync_browser = self._sync_pw.chromium.launch(headless=True)
            logger.info("Sync browser started")
            return self._sync_browser

        except Exception as e:
            logger.error("Failed to start sync browser", error=e)
            raise

    def get_sync_page(self) -> SyncPage:
        """
        الحصول على صفحة sync (reuse)
        """
        try:
            if self._sync_page is not None:
                return self._sync_page

            browser = self.start_sync_browser()
            context = browser.new_context()
            self._sync_page = context.new_page()

            logger.debug("Sync page created")
            return self._sync_page

        except Exception as e:
            logger.error("Failed to get sync page", error=e)
            raise


# ==================== SINGLETON ====================

_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """
    إرجاع instance واحد فقط من BrowserManager
    """
    global _browser_manager

    if _browser_manager is None:
        _browser_manager = BrowserManager()
        logger.info("BrowserManager instance created")

    return _browser_manager


# Example usage:
# bm = get_browser_manager()
# page = await bm.new_page()
# await page.goto("https://example.com")
