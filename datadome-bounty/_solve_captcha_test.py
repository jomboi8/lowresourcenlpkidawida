import random
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGET = "https://bounty-nodejs.datashield.co/scraping"


def human_drag(page, start_x, start_y, end_x, end_y):
    page.mouse.move(start_x, start_y, steps=3)
    page.wait_for_timeout(random.randint(120, 280))
    page.mouse.down()
    page.wait_for_timeout(random.randint(50, 140))

    overshoot = random.uniform(6, 16)
    total_dx = (end_x + overshoot) - start_x
    n_points = random.randint(45, 70)

    t = 0.0
    x, y = start_x, start_y
    while t < 1.0:
        # bell-shaped velocity: slow-start, fast-middle, slow-end (sum of two sigmoids)
        step = random.uniform(0.008, 0.03)
        t = min(1.0, t + step)
        # smootherstep easing
        eased = t * t * t * (t * (t * 6 - 15) + 10)
        x = start_x + total_dx * eased
        y = start_y + random.uniform(-3, 3) + (2 if 0.3 < t < 0.7 else 0) * random.choice([-1, 1]) * random.random()
        page.mouse.move(x, y)
        # occasional micro pause, like a real hand
        if random.random() < 0.08:
            page.wait_for_timeout(random.randint(35, 90))
        else:
            page.wait_for_timeout(random.randint(5, 16))

    # settle: correct the overshoot back to the true end, slowly
    settle_steps = random.randint(5, 9)
    cur_x = x
    for i in range(1, settle_steps + 1):
        frac = i / settle_steps
        x = cur_x + (end_x - cur_x) * frac
        y = start_y + random.uniform(-1, 1)
        page.mouse.move(x, y)
        page.wait_for_timeout(random.randint(15, 40))

    page.wait_for_timeout(random.randint(150, 350))
    page.mouse.up()


with Stealth(
    navigator_platform_override="Linux x86_64",
).use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(TARGET, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    print("platform check:", page.evaluate("navigator.platform"), "| UA:", page.evaluate("navigator.userAgent"))

    solved = False
    for attempt in range(5):
        frame = None
        for f in page.frames:
            if "captcha-delivery.com" in f.url:
                frame = f
                break

        if frame is None:
            print(f"[attempt {attempt}] No captcha frame -- body:", page.inner_text("body")[:200])
            solved = True
            break

        iframe_loc = page.frame_locator("iframe[title='DataDome CAPTCHA']")
        slider = iframe_loc.locator(".slider")
        container = iframe_loc.locator(".sliderContainer")

        try:
            slider.wait_for(state="visible", timeout=10000)
        except Exception as e:
            print(f"[attempt {attempt}] slider not visible: {e}")
            page.goto(TARGET, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            continue

        sbox = slider.bounding_box()
        cbox = container.bounding_box()
        start_x = sbox["x"] + sbox["width"] / 2
        start_y = sbox["y"] + sbox["height"] / 2
        end_x = cbox["x"] + cbox["width"] - sbox["width"] / 2 - 3
        end_y = start_y

        human_drag(page, start_x, start_y, end_x, end_y)

        # poll for success/error class for up to 4s (validation is likely async)
        final_cls = None
        for _ in range(16):
            page.wait_for_timeout(250)
            try:
                final_cls = container.get_attribute("class", timeout=1000)
            except Exception:
                final_cls = None
            if final_cls and ("slider-success" in final_cls or "slider-error" in final_cls):
                break
        print(f"[attempt {attempt}] final container class: {final_cls}")

        if final_cls and "slider-success" in final_cls:
            print(f"[attempt {attempt}] slider-success -- waiting for natural redirect...")
            page.wait_for_timeout(4000)
            solved = True
            break

        page.wait_for_timeout(1500)

        if page.is_closed() or not browser.is_connected():
            print(f"[attempt {attempt}] page/browser closed")
            break

        still_captcha = any("captcha-delivery.com" in f.url for f in page.frames)
        if not still_captcha:
            print(f"[attempt {attempt}] captcha frame gone -- likely solved")
            solved = True
            break
        else:
            print(f"[attempt {attempt}] still showing captcha, reloading and retrying...")
            page.goto(TARGET, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

    print("solved:", solved)
    if not page.is_closed():
        print("page.url:", page.url)
        print("frames after solve:", [f.url for f in page.frames])
        if solved:
            print("forcing reload to pick up validated cookie...")
            page.goto(TARGET, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            print("frames after reload:", [f.url for f in page.frames])
        try:
            body = page.inner_text("body")
            print("=== body (first 400) ===")
            print(repr(body[:400]))
        except Exception as e:
            print("inner_text failed:", e)
        try:
            print("=== cookies ===")
            for c in context.cookies(TARGET):
                print(c["name"], "=", c["value"][:50])
        except Exception as e:
            print("cookies failed:", e)

    if browser.is_connected():
        browser.close()
