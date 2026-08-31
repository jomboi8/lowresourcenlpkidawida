import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGET = "https://bounty-nodejs.datashield.co/scraping"

with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(TARGET, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    captcha_frame = None
    for f in page.frames:
        if "captcha-delivery.com" in f.url:
            captcha_frame = f
            break

    if captcha_frame is None:
        print("NO CAPTCHA FRAME -- body:", page.inner_text("body")[:300])
    else:
        print("Captcha frame URL:", captcha_frame.url)
        print("=== captcha frame HTML (first 4000 chars) ===")
        print(captcha_frame.content()[:4000])

    browser.close()
