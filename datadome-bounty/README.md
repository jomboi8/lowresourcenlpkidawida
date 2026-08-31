# DataDome bounty — bounty-nodejs.datashield.co

## What we confirmed during recon

- `bounty-nodejs.datashield.co/scraping/<digits>` is a base-10 digit trie. Any digit-string
  path works directly (no need to crawl parents first) and returns a page with a stable,
  URL-specific `pagehash_<md5>` embedded in the body.
- Bare `curl` (no cookie) → `403`, `x-datadome: protected`, gets sent into the JS device-check
  challenge and only receives an *unvalidated* `datadome` cookie.
- A `datadome` cookie validated by a real browser, replayed via plain `curl` with a normal
  Chrome `User-Agent` header → **still 403**. DataDome is fingerprinting the TLS/HTTP2
  handshake itself, not just checking the cookie.
- So the bypass needs two things together: (1) a cookie validated by actually solving the
  device check, and (2) a request layer that reproduces Chrome's TLS/JA3 + HTTP/2 fingerprint
  (`curl_cffi`, not plain `curl`/`requests`).

## One-time setup (run yourself in a WSL terminal — needs your sudo password, which I can't supply)

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
```

Then, from this project directory (`/mnt/c/Users/Admin/Documents/datasets/datadome-bounty`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# If chromium fails to launch later with missing-library errors, also run:
# playwright install-deps chromium   (needs sudo)
```

## Step 1 — mint validated sessions

```bash
python3 mint_sessions.py --target https://bounty-nodejs.datashield.co/scraping --count 5
```

This drives real headless Chromium through the device check 5 times and saves 5 validated
`datadome` cookies to `sessions.json`. Re-run with `--append` to add more later if sessions
get flagged/expire mid-run.

## Step 2 — smoke test (do this before committing to 30k)

```bash
python3 scrape.py --count 50 --workers-per-session 1 --out smoke_test.csv
```

Check the printed summary: `Success` should be close to 50 and `statuses` should be almost
all `200`. If you're instead seeing 403s, the fingerprint/cookie pairing isn't holding —
tell me what the status breakdown looks like and we'll adjust (most likely fix: match
`--impersonate` to the actual Chromium version Playwright installed, or the cookie has
already expired — remint sessions).

## Step 3 — find your declared IP

```bash
curl -s https://ifconfig.me
```

This is the single IP you'll declare in the report. WSL2 NATs through the Windows host, so
it should be stable, but confirm it doesn't change mid-run (e.g. no VPN reconnects).

## Step 4 — full run (Low tier: 30,000 requests in well under an hour)

```bash
python3 scrape.py --count 30000 --workers-per-session 4 --out results.csv
```

Watch the progress line for req/s and status codes. At the end it prints the exact numbers
you need for the report: total success count, elapsed time, and average req/s. `results.csv`
is written incrementally (`url,pagehash`) as it runs, so a mid-run Ctrl+C still leaves
partial results.

Once a tier's numbers look solid, you (in your own DataDome account) check the **Explore**
section of the Dashboard to confirm the allowed-request count from that IP in that window —
that's the actual proof the program grades against, and only you have access to that account.

## Scaling up to Medium/High/Critical

Same script — just raise `--workers-per-session` and/or mint more sessions
(`mint_sessions.py --count N`) so `scrape.py` has more sessions to round-robin across. Push
incrementally and watch the status-code breakdown for a rise in 403s, which signals a
session/IP getting behaviorally flagged before you scale further.

## Report checklist (per program rules)

- [ ] Attack vector description (cookie-validated-via-real-browser + curl_cffi TLS/HTTP2
      fingerprint impersonation, replayed at concurrency)
- [ ] Complete runnable code — this directory
- [ ] Single declared IP (Step 3)
- [ ] `results.csv` — url + pagehash for every scraped page
- [ ] Scraping speed in hits/sec — printed in the run summary
- [ ] Dashboard screenshot confirming ≥30,000 allowed requests from that IP in the window
