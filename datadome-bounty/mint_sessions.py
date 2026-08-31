"""
Mints validated DataDome sessions against the bounty target using a real
headless Chromium (Playwright), which passes the JS device-check challenge
the way a real browser would. Each session's `datadome` cookie is saved to
sessions.json so the bulk scraper (scrape.py) can reuse them over many
fingerprint-impersonated HTTP requests without re-solving the challenge
every time.

Usage:
    python3 mint_sessions.py --target https://bounty-nodejs.datashield.co --count 5
"""
import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SESSIONS_FILE = Path(__file__).parent / "sessions.json"


def mint_one(playwright, target: str, timeout_s: float = 20.0) -> dict | None:
    browser = playwright.chromium.launch(headless=True)
    try:
        # Fresh context per session => fresh device fingerprint / cookie jar,
        # so sessions in the pool are independent of one another.
        context = browser.new_context()
        page = context.new_page()
        page.goto(target, wait_until="domcontentloaded")

        deadline = time.time() + timeout_s
        validated = False
        while time.time() < deadline:
            body_text = page.inner_text("body") if page.query_selector("body") else ""
            if "pagehash_" in body_text or "scraping" in body_text:
                validated = True
                break
            if "Verifying the device" not in body_text:
                # Not the interstitial and not yet our content; give it a moment.
                pass
            page.wait_for_timeout(500)

        cookies = context.cookies(target)
        dd_cookie = next((c["value"] for c in cookies if c["name"] == "datadome"), None)
        user_agent = page.evaluate("navigator.userAgent")

        context.close()

        if not validated or not dd_cookie:
            return None

        return {
            "cookie": dd_cookie,
            "user_agent": user_agent,
            "minted_at": time.time(),
            "requests_sent": 0,
        }
    finally:
        browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="https://bounty-nodejs.datashield.co/scraping")
    ap.add_argument("--count", type=int, default=5, help="number of sessions to mint")
    ap.add_argument("--append", action="store_true", help="append to existing sessions.json instead of overwriting")
    args = ap.parse_args()

    existing = []
    if args.append and SESSIONS_FILE.exists():
        existing = json.loads(SESSIONS_FILE.read_text())

    minted = []
    with sync_playwright() as p:
        for i in range(args.count):
            print(f"[{i+1}/{args.count}] minting session...", flush=True)
            sess = mint_one(p, args.target)
            if sess:
                print(f"  ok: datadome cookie len={len(sess['cookie'])}")
                minted.append(sess)
            else:
                print("  FAILED to validate device check within timeout")

    all_sessions = existing + minted
    SESSIONS_FILE.write_text(json.dumps(all_sessions, indent=2))
    print(f"\nSaved {len(all_sessions)} total sessions to {SESSIONS_FILE} ({len(minted)} new)")


if __name__ == "__main__":
    main()
