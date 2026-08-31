from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGET = "https://bounty-nodejs.datashield.co/scraping"

with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(TARGET, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print("main frame content:")
    print(page.content()[:3000])
    for f in page.frames:
        if f == page.main_frame:
            continue
        print("\n--- sub frame:", f.url)
        try:
            print(f.content()[:3000])
        except Exception as e:
            print("err:", e)
    browser.close()
