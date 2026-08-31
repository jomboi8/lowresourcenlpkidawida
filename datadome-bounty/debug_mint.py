import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGET = "https://bounty-nodejs.datashield.co/scraping"

with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(TARGET, wait_until="domcontentloaded")
    for i in range(10):
        time.sleep(1)
        body = page.inner_text("body")
        print(f"--- t={i+1}s ---")
        print(repr(body[:300]))
    print("=== frames ===")
    for f in page.frames:
        print(f.url)
    print("=== full html (first 2000 chars) ===")
    print(page.content()[:2000])
    print("=== cookies ===")
    for c in context.cookies(TARGET):
        print(c["name"], "=", c["value"][:40], "...")
    print("=== navigator.webdriver ===")
    print(page.evaluate("navigator.webdriver"))
    print("=== user agent ===")
    print(page.evaluate("navigator.userAgent"))
    page.screenshot(path="debug_screenshot.png")
    browser.close()
