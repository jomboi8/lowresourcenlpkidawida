import random
from patchright.sync_api import sync_playwright

TARGET = "https://bounty-nodejs.datashield.co/scraping"


def human_drag(page, start_x, start_y, end_x, end_y):
    page.mouse.move(start_x, start_y, steps=3)
    page.wait_for_timeout(random.randint(120, 280))
    page.mouse.down()
    page.wait_for_timeout(random.randint(50, 140))

    overshoot = random.uniform(6, 16)
    total_dx = (end_x + overshoot) - start_x

    t = 0.0
    x, y = start_x, start_y
    while t < 1.0:
        step = random.uniform(0.008, 0.03)
        t = min(1.0, t + step)
        eased = t * t * t * (t * (t * 6 - 15) + 10)
        x = start_x + total_dx * eased
        y = start_y + random.uniform(-3, 3)
        page.mouse.move(x, y)
        if random.random() < 0.08:
            page.wait_for_timeout(random.randint(35, 90))
        else:
            page.wait_for_timeout(random.randint(5, 16))

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


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="chrome")
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto(TARGET, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    print("webdriver:", page.evaluate("navigator.webdriver"))
    print("platform:", page.evaluate("navigator.platform"), "| UA:", page.evaluate("navigator.userAgent"))

    solved = False
    for attempt in range(5):
        frame = None
        for f in page.frames:
            if "captcha-delivery.com" in f.url:
                frame = f
                break

        if frame is None:
            print(f"[attempt {attempt}] No captcha frame -- likely passed straight through")
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
            print(f"[attempt {attempt}] slider-success -- waiting + reloading to confirm...")
            page.wait_for_timeout(3000)
            page.goto(TARGET, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            still_captcha_after = any("captcha-delivery.com" in f.url for f in page.frames)
            if not still_captcha_after:
                print(f"[attempt {attempt}] CONFIRMED: no captcha after reload -- real pass")
                solved = True
                break
            else:
                print(f"[attempt {attempt}] still captcha after reload -- server rejected, retrying")
                continue

        page.wait_for_timeout(1000)
        if page.is_closed() or not browser.is_connected():
            print(f"[attempt {attempt}] page/browser closed")
            break

        print(f"[attempt {attempt}] not success, reloading and retrying...")
        page.goto(TARGET, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

    print("solved:", solved)
    if not page.is_closed():
        print("page.url:", page.url)
        try:
            body = page.inner_text("body")
            print("=== body (first 400) ===")
            print(repr(body[:400]))
        except Exception as e:
            print("inner_text failed:", e)
        try:
            print("=== cookies ===")
            for c in context.cookies(TARGET):
                print(c["name"], "=", c["value"][:60])
        except Exception as e:
            print("cookies failed:", e)

    if browser.is_connected():
        browser.close()
