"""
Bulk scraper for the DataDome bounty target. Uses curl_cffi to replicate a
real Chrome TLS/JA3 + HTTP/2 fingerprint on every request (plain `curl`/
`requests`/`httpx` get re-challenged even with a valid `datadome` cookie --
confirmed during recon), reusing validated cookies minted by mint_sessions.py
so we don't have to solve the JS challenge per request.

Usage:
    python3 scrape.py --base https://bounty-nodejs.datashield.co/scraping \
        --count 30000 --workers-per-session 4 --out results.csv

Writes results.csv incrementally: url,pagehash
Prints running req/s so you can watch progress toward a reward tier.
"""
import argparse
import asyncio
import csv
import json
import re
import time
from pathlib import Path

from curl_cffi.requests import AsyncSession

SESSIONS_FILE = Path(__file__).parent / "sessions.json"
HASH_RE = re.compile(r"pagehash_[0-9a-f]{32}")


def load_sessions():
    if not SESSIONS_FILE.exists():
        raise SystemExit("sessions.json not found -- run mint_sessions.py first")
    sessions = json.loads(SESSIONS_FILE.read_text())
    if not sessions:
        raise SystemExit("sessions.json is empty -- run mint_sessions.py first")
    return sessions


def gen_paths(base: str, count: int, start: int, digits: int):
    for i in range(start, start + count):
        yield f"{base.rstrip('/')}/{str(i).zfill(digits)}"


class Stats:
    def __init__(self):
        self.success = 0
        self.failed = 0
        self.status_counts = {}
        self.start = time.time()
        self.lock = asyncio.Lock()

    async def record(self, ok: bool, status):
        async with self.lock:
            if ok:
                self.success += 1
            else:
                self.failed += 1
            self.status_counts[status] = self.status_counts.get(status, 0) + 1

    def rps(self):
        elapsed = max(time.time() - self.start, 1e-9)
        return (self.success + self.failed) / elapsed


async def worker(name, session_info, queue, csv_writer, csv_lock, stats, impersonate, retries):
    cookies = {"datadome": session_info["cookie"]}
    headers = {
        "User-Agent": session_info["user_agent"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with AsyncSession(impersonate=impersonate) as s:
        while True:
            try:
                url = queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            ok = False
            status = None
            for attempt in range(retries + 1):
                try:
                    resp = await s.get(url, cookies=cookies, headers=headers, timeout=15)
                    status = resp.status_code
                    if status == 200:
                        m = HASH_RE.search(resp.text)
                        if m:
                            async with csv_lock:
                                csv_writer.writerow([url, m.group(0)])
                            ok = True
                            break
                    # non-200 or no hash found -> retry
                except Exception as e:
                    status = f"error:{type(e).__name__}"
                await asyncio.sleep(0.2 * (attempt + 1))

            await stats.record(ok, status)
            queue.task_done()


async def progress_reporter(stats: Stats, total: int):
    while True:
        await asyncio.sleep(5)
        done = stats.success + stats.failed
        print(
            f"  progress: {done}/{total} done | ok={stats.success} fail={stats.failed} "
            f"| {stats.rps():.1f} req/s | statuses={stats.status_counts}",
            flush=True,
        )
        if done >= total:
            return


async def main_async(args):
    sessions = load_sessions()
    digits = max(len(str(args.start + args.count - 1)), args.min_digits)

    queue = asyncio.Queue()
    for path in gen_paths(args.base, args.count, args.start, digits):
        queue.put_nowait(path)

    out_path = Path(args.out)
    is_new = not out_path.exists()
    csv_file = open(out_path, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if is_new:
        csv_writer.writerow(["url", "pagehash"])
    csv_lock = asyncio.Lock()

    stats = Stats()
    reporter = asyncio.create_task(progress_reporter(stats, args.count))

    tasks = []
    for i, sess in enumerate(sessions):
        for w in range(args.workers_per_session):
            tasks.append(
                asyncio.create_task(
                    worker(f"s{i}w{w}", sess, queue, csv_writer, csv_lock, stats, args.impersonate, args.retries)
                )
            )

    await queue.join()
    for t in tasks:
        t.cancel()
    reporter.cancel()
    csv_file.close()

    elapsed = time.time() - stats.start
    print("\n=== DONE ===")
    print(f"Total attempted: {stats.success + stats.failed}")
    print(f"Success (200 + pagehash): {stats.success}")
    print(f"Failed: {stats.failed}  -- breakdown: {stats.status_counts}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Avg throughput: {stats.rps():.2f} req/s")
    print(f"CSV written to: {out_path.resolve()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://bounty-nodejs.datashield.co/scraping")
    ap.add_argument("--count", type=int, default=30000)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--min-digits", type=int, default=5)
    ap.add_argument("--workers-per-session", type=int, default=4)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--impersonate", default="chrome124")
    ap.add_argument("--out", default="results.csv")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
