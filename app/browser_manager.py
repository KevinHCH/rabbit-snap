from playwright.async_api import async_playwright
from user_agent import generate_user_agent
import asyncio


class BrowserManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self.last_used = None
        self.lock = asyncio.Lock()
        self.is_running = False

    async def start(self):
        if self.is_running:
            return
        print("Starting browser")
        user_agent = generate_user_agent(os="win", device_type="desktop")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            args=[
                f"--user-agent='{user_agent}'",
            ]
        )
        self.context = await self.browser.new_context()
        self.last_used = asyncio.get_event_loop().time()
        self.is_running = True
        asyncio.create_task(self._auto_close())

    async def stop(self):
        if not self.is_running:
            return
        async with self.lock:
            try:
                if self.context:
                    await self.context.close()
                if self.browser:
                    print("Closing browser")
                    await self.browser.close()
                if self.playwright:
                    print("Closing playwright")
                    await self.playwright.stop()
            except Exception as e:
                print(f"Error during shutdown: {e}")
            finally:
                self.is_running = False

    async def capture_screenshot(self, url):
        async with self.lock:
            if not self.is_running:
                await self.start()
            self.last_used = asyncio.get_event_loop().time()
            page = await self.context.new_page()
            await page.goto(url)
            screenshot_path = f"cache/{url.replace('://', '_').replace('/', '_')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            await page.close()
            return screenshot_path

    async def _auto_close(self):
        TWO_MINUTES = 120  # 2 minutes idle
        while True:
            # check every 30 seconds
            await asyncio.sleep(30)
            if asyncio.get_event_loop().time() - self.last_used > TWO_MINUTES:
                await self.stop()
                break
