"""
Base scraper utilities with robust error handling and browser management.

KEY LEARNINGS:
1. Firefox bypasses BizBuySell's anti-bot better than Chromium
2. Chromium with stealth works for homepage but gets blocked on search pages
3. Rate limiting happens after ~50 pages in quick succession
4. Connection pool needs reset between large batch operations
5. Always save scraped data to file BEFORE database insert
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class ScrapeMetrics:
    """Track scrape performance metrics."""
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_scraped: int = 0
    listings_found: int = 0
    errors: int = 0
    browser_used: str = ""
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def pages_per_minute(self) -> float:
        if self.duration_seconds > 0:
            return (self.pages_scraped / self.duration_seconds) * 60
        return 0
    
    def __str__(self) -> str:
        duration = self.duration_seconds
        mins, secs = divmod(int(duration), 60)
        return (
            f"Scraped {self.pages_scraped} pages, found {self.listings_found} listings "
            f"in {mins}m {secs}s ({self.pages_per_minute:.1f} pages/min) "
            f"using {self.browser_used}, {self.errors} errors"
        )


class BrowserManager:
    """
    Manages browser lifecycle with automatic fallback.
    
    Priority: Firefox (best for BizBuySell) → Chromium with stealth
    """
    
    STEALTH_ARGS = [
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-dev-shm-usage',
        '--no-first-run',
    ]
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.browser_type: str = ""
        self.playwright = None
    
    async def launch(self, preferred_browser: str = "firefox") -> Page:
        """
        Launch browser with automatic fallback.
        
        Args:
            preferred_browser: "firefox" or "chromium"
        
        Returns:
            Page object ready for navigation
        """
        self.playwright = await async_playwright().start()
        
        # Try preferred browser first
        browsers_to_try = [preferred_browser]
        if preferred_browser == "firefox":
            browsers_to_try.append("chromium")
        else:
            browsers_to_try.append("firefox")
        
        last_error = None
        for browser_name in browsers_to_try:
            try:
                logger.info(f"Launching {browser_name}...")
                
                if browser_name == "firefox":
                    self.browser = await self.playwright.firefox.launch(headless=False)
                    self.context = await self.browser.new_context(
                        viewport=self._random_viewport(),
                        locale='en-US',
                    )
                else:
                    # Chromium with stealth
                    self.browser = await self.playwright.chromium.launch(
                        headless=False,
                        args=self.STEALTH_ARGS,
                    )
                    self.context = await self.browser.new_context(
                        viewport=self._random_viewport(),
                        user_agent=self._random_user_agent(),
                        locale='en-US',
                    )
                    # Add stealth script
                    await self.context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.chrome = { runtime: {} };
                    """)
                
                self.page = await self.context.new_page()
                self.browser_type = browser_name
                
                # Quick test - can we reach any page?
                response = await self.page.goto('https://www.google.com', timeout=10000)
                if response and response.status == 200:
                    logger.info(f"{browser_name} launched successfully")
                    return self.page
                    
            except Exception as e:
                last_error = e
                logger.warning(f"{browser_name} failed: {e}")
                await self._cleanup()
        
        raise RuntimeError(f"All browsers failed. Last error: {last_error}")
    
    async def close(self):
        """Close browser and cleanup."""
        await self._cleanup()
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def _cleanup(self):
        """Internal cleanup."""
        if self.context:
            try:
                await self.context.close()
            except:
                pass
            self.context = None
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
            self.browser = None
        self.page = None
    
    def _random_viewport(self) -> dict:
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1366, 'height': 768},
        ]
        return random.choice(viewports)
    
    def _random_user_agent(self) -> str:
        agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        ]
        return random.choice(agents)


async def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Random human-like delay."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def safe_navigate(page: Page, url: str, retries: int = 3) -> bool:
    """
    Navigate to URL with retry logic.
    
    Returns:
        True if navigation successful, False otherwise
    """
    for attempt in range(retries):
        try:
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response is None:
                logger.warning(f"No response from {url}")
                continue
            
            if response.status == 403:
                logger.error(f"Access denied (403) for {url}")
                return False
            
            if response.status == 200:
                content = await page.content()
                if 'Access Denied' in content:
                    logger.error(f"Access Denied in page content for {url}")
                    return False
                return True
            
            logger.warning(f"Unexpected status {response.status} for {url}")
            
        except Exception as e:
            logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await human_delay(2, 5)
    
    return False


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    mins, secs = divmod(int(seconds), 60)
    if mins < 60:
        return f"{mins}m {secs}s"
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m"

