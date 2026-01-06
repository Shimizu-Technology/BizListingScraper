"""
Stealth browsing utilities to avoid rate limiting.
All free techniques - no paid services required.
"""
import asyncio
import random
from typing import Optional

# Realistic user agents (rotate through these)
USER_AGENTS = [
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Viewport sizes (common screen resolutions)
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

# Timezones
TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Detroit",
]


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> dict:
    """Get a random viewport size."""
    return random.choice(VIEWPORTS)


def get_random_timezone() -> str:
    """Get a random timezone."""
    return random.choice(TIMEZONES)


async def human_delay(min_seconds: float = 2, max_seconds: float = 5):
    """Random delay to simulate human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def simulate_human_behavior(page):
    """
    Simulate human-like behavior on a page.
    - Random mouse movements
    - Scrolling
    - Random pauses
    """
    # Random mouse movement
    x = random.randint(100, 800)
    y = random.randint(100, 600)
    await page.mouse.move(x, y)
    await asyncio.sleep(random.uniform(0.3, 0.8))
    
    # Scroll down slowly
    for _ in range(random.randint(2, 4)):
        scroll_amount = random.randint(200, 400)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # Move mouse again
    x = random.randint(200, 900)
    y = random.randint(200, 500)
    await page.mouse.move(x, y)


def get_stealth_scripts() -> str:
    """
    JavaScript to inject for stealth mode.
    Hides automation indicators.
    """
    return """
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Add chrome runtime
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Add realistic screen properties
        Object.defineProperty(screen, 'availWidth', { get: () => window.innerWidth });
        Object.defineProperty(screen, 'availHeight', { get: () => window.innerHeight });
    """


async def create_stealth_context(playwright, data_dir: Optional[str] = None):
    """
    Create a browser context with stealth settings.
    
    Args:
        playwright: Playwright instance
        data_dir: Optional persistent data directory
    
    Returns:
        Browser context configured for stealth
    """
    user_agent = get_random_user_agent()
    viewport = get_random_viewport()
    timezone = get_random_timezone()
    
    args = [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-first-run',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-breakpad',
        '--disable-component-extensions-with-background-pages',
        '--disable-component-update',
        '--disable-default-apps',
        '--disable-extensions',
        '--disable-features=TranslateUI',
        '--disable-hang-monitor',
        '--disable-ipc-flooding-protection',
        '--disable-popup-blocking',
        '--disable-prompt-on-repost',
        '--disable-renderer-backgrounding',
        '--disable-sync',
        '--force-color-profile=srgb',
        '--metrics-recording-only',
        '--no-default-browser-check',
    ]
    
    if data_dir:
        context = await playwright.chromium.launch_persistent_context(
            data_dir,
            headless=False,
            viewport=viewport,
            user_agent=user_agent,
            timezone_id=timezone,
            locale='en-US',
            args=args,
        )
    else:
        browser = await playwright.chromium.launch(
            headless=False,
            args=args,
        )
        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            timezone_id=timezone,
            locale='en-US',
        )
    
    return context

