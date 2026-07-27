# ForgeCard V0

A local-first NFC identity kiosk for the EchoForge ecosystem — part of the Echo Family.

**Live kiosk display:** `forgecard.echoforgellc.tech`

---

## Overview

ForgeCard V0 splits into two independent halves that only agree on one contract: a URL.

```
PN532 Reader (Raspberry Pi, Python)         Kiosk Display (Next.js)
    ↓                                            ↑
Card UID                                    reads ?address=... on load
    ↓                                            ↑
lookup_uid(uid)  →  Cardano Stake Address   opens/replaces the kiosk browser at
    ↓                                       http://<frontend>/?address=<stake_address>
subprocess opens/reloads kiosk Chromium ────┘
                                                  ↓
                                        frontend calls the EchoID API itself
                                        (data.profile / data.tierMeta) and renders
```

Python's job stops at resolving a UID to a stake address and pointing the kiosk browser at it — it never calls the EchoID API and never decides `accountType`. The frontend's job starts at the URL — it doesn't know a UID or a local binding table exist. Each side reasons about its own layer only; the URL is the entire interface between them, and it has exactly two forms:

| Situation | URL | Screen |
|---|---|---|
| Card has a local binding | `/?address=<stake_address>` | Verifying → EchoID profile card |
| Card read, no binding | `/?status=unbound` | "Card Not Registered" |

`?status=unbound` carries no UID and says nothing about the binding table, so the decoupling holds — the frontend still has no concept of local bindings, only of "the Pi couldn't give me an address."

Card-to-stake-address bindings are stored locally in a JSON file (`card_store.json`). No blockchain interaction is required — the stake address is only ever used as a lookup key.

For deployment/setup on the Raspberry Pi, see [MAINTENANCE.md](MAINTENANCE.md). For the visual design system, see the root [DESIGN.md](../DESIGN.md) (EchoForgeStyle) — ForgeCard follows it exactly (IBM Plex Mono, monochrome, glass morphism, corner markers).

---

# Project Structure

```
forgecard-v0/

├── frontend/             # Kiosk display (Next.js), styled per DESIGN.md
│   └── src/
│       ├── app/             # page.js — reads ?address= / ?status=, drives idle/scanning/result/error
│       ├── components/      # IdleView, ScanningView, ResultView, ErrorView, etc.
│       └── lib/             # echoid.js (client-side EchoID fetch), format.js, constants.js
├── forgecard_kiosk.py    # Pi entry point: PN532 -> UID -> lookup -> navigate kiosk browser
├── card_store.py         # Local data layer: read/write/normalize UID bindings
├── bind_card.py          # CLI: bind a card UID to a Cardano stake address
├── test_lookup.py        # CLI: look up a card's local binding by UID
├── echoid_client.py      # HTTPS client for the EchoID profile API (used by the CLI tools, not the kiosk)
├── forgecard_demo.py     # CLI: full flow — UID -> binding -> EchoID profile display (manual input, no hardware)
├── card_store.json       # Local binding database (generated automatically, gitignored)
├── requirements.txt      # Core deps (requests) — install everywhere
├── requirements-pi.txt   # PN532 hardware drivers — Raspberry Pi only
├── README.md
├── MAINTENANCE.md        # Pi deployment, kiosk mode, env vars, troubleshooting
└── .venv/
```

There is no backend directory and no server process. The kiosk is two halves — a Python script on the Pi and a static frontend — joined only by the URL contract above.

---

# Requirements

* Python 3.13+
* macOS / Linux / Raspberry Pi OS
* [`requests`](https://pypi.org/project/requests/) — used by `echoid_client.py` to call the EchoID API

Python standard libraries used:

* json
* pathlib
* argparse

---

# Virtual Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install requests
```

Verify:

```bash
python --version
```

---

# Bind a Card

Example:

```bash
python bind_card.py 04A1B2C3 stake1test Charles
```

Expected output:

```
绑定成功！
UID:04A1B2C3
质押地址:stake1test
显示名称:Charles
```

---

# Lookup a Card (local binding only)

Run:

```bash
python test_lookup.py
```

Example input:

```
04A1B2C3
```

Example output:

```
已注册
显示名称： Charles
质押地址： stake1test
```

If the UID is not registered:

```
未注册
```

---

# Run the Full Demo (binding + EchoID profile)

`forgecard_demo.py` chains the local UID lookup together with a live EchoID profile fetch, then renders the result as a terminal card.

Run:

```bash
python forgecard_demo.py
```

Example input:

```
请输入 UID: 04A1B2C3
```

Example output:

```
==================================================
                  ForgeCard V0
==================================================
Card UID            : 04A1B2C3
Stake Address       : stake_test1urex...
Display Name        : Charles
Tier                : <tier name> (<tier cn>)
Role                : <role>
Days Since Joined   : <days>
Tagline             : <tagline>
==================================================
```

Tier, role, days-since-joined, and tagline come from the live EchoID response, so values vary per account.

If the UID has no local binding, it prints `未注册` and exits. If the stake address has no EchoID profile yet, it prints `请先注册 EchoID` and exits.

---

# Local Database Format

Card-to-stake-address bindings are stored as JSON in `card_store.json` (not committed to git).

Example:

```json
{
  "04A1B2C3": {
    "stake_address": "stake1test",
    "display_name": "Charles"
  }
}
```

Identity information (tier, role, tagline, etc.) is **not** cached locally — `forgecard_demo.py` fetches it from EchoID on every run.

---

# Kiosk Backend + Frontend

The kiosk display replaces manual UID input with a PN532 reader and a 1024x600 screen. The two halves communicate through the URL contract described in the Overview above — nothing else.

**1. Pi-side Python** (`forgecard_kiosk.py`, in progress): reads a UID off the PN532, normalizes it to the `card_store.json` key format, resolves it with `lookup_uid(uid)`, and navigates the kiosk Chromium window to `/?address=<stake_address>` — or to `/?status=unbound` when the card has no binding. It never calls the EchoID API and never sees an `accountType`; that decision belongs to the frontend.

Develop it without hardware — keyboard mode replaces the PN532 with `input()`:

```bash
python forgecard_kiosk.py --keyboard
```

**2. Frontend** (the kiosk display) — already implements its half of the contract:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_ECHOID_API_URL, defaults to production
npm run dev                        # or: npm run build && npm start
```

On load it reads `?address=` (or `?status=`) from the URL, calls the EchoID API directly from the browser (`src/lib/echoid.js` — tries `accountType=individual` then falls back to `institutional`), and renders: idle ("tap card", bare URL) → verifying → EchoID profile card → auto-return to idle (clears the query param client-side). Append `?preview=ok|idle|scanning|unbound|no_profile|error` to preview a state without Python or a real address. You can also drive the real paths directly: `?address=<any stake address>` or `?status=unbound`.

See [MAINTENANCE.md](MAINTENANCE.md) for Raspberry Pi kiosk setup (autostart, Chromium `--kiosk` flags).

---

# Current Features

* UID normalization
* Local JSON storage for card ↔ stake address bindings
* Bind an NFC UID to a Cardano stake address (`bind_card.py`)
* Look up a binding by UID (`test_lookup.py`)
* Fetch a live EchoID profile by stake address over HTTPS (`echoid_client.py`, used by the CLI tools)
* Combined binding + profile demo with formatted terminal output (`forgecard_demo.py`)
* Kiosk frontend: 1024x600 EchoForgeStyle display driven entirely by `?address=` (`frontend/`) — reads the URL, calls the EchoID API itself, renders idle/scanning/result/error states
* Graceful handling of missing EchoID profiles and lookup failures
* Command-line interfaces (CLI) throughout, plus the kiosk display

---

# Next Milestone

Rewrite the Pi-side Python to match the `?address=` contract: UID → `lookup_uid()` → build the kiosk URL → `subprocess` open/replace the Chromium kiosk window. Then wire a physical PN532 over I2C and deploy to run on boot.

---

# Development Notes

Current implementation is intended for local development on macOS.

After validation, the project will be deployed to Raspberry Pi for hardware integration.

## Development Log

### Week 3
- Implemented local JSON storage
- Added UID normalization
- Implemented card binding CLI
- Implemented UID lookup
- Completed local testing on macOS

### v0.1-alpha
- Implemented `echoid_client.py`: HTTPS client for the EchoID profile API
- Implemented `forgecard_demo.py`: combined UID lookup + EchoID profile fetch + formatted terminal display
- Handled 404 / non-200 responses and missing EchoID profiles
- Fixed `card_store.json` path resolution to be independent of the current working directory
- Tagged local build as ForgeCard v0.1-alpha

### v0.2 — Kiosk backend + frontend (WebSocket prototype)
- Added `backend/server.py`: FastAPI WebSocket backend reusing `card_store.py` / `echoid_client.py` as the single source of truth
- Added `backend/pn532_reader.py`: PN532 I2C driver with mock-reader fallback for hardware-less dev machines
- Built the kiosk frontend (`frontend/`) in Next.js, styled per `DESIGN.md` (EchoForgeStyle): idle / scanning / result / error states, sized for a 1024x600 screen
- Verified the full chain end-to-end: simulated PN532 tap -> WebSocket push -> live EchoID API fetch -> kiosk render
- Domain reserved: `forgecard.echoforgellc.tech`
- Superseded by v0.3 below — Python calling `fetch_profile()` itself coupled it to the frontend's `accountType` decision

### v0.3 — `?address=` contract
- Redefined the Python/frontend boundary: Python resolves UID -> stake address and hands the frontend a URL (`?address=<stake_address>`); it no longer calls the EchoID API or decides `accountType`
- Rewrote the frontend to read `?address=` on load and call the EchoID API directly from the browser (`frontend/src/lib/echoid.js`) — tries `accountType=individual`, falls back to `institutional`
- Removed the WebSocket layer from the frontend (`useForgeCardSocket.js`, dev simulate panel) — no longer needed since each tap is a fresh page load, not a push event
- Confirmed via direct query that `api-id.echoforgellc.tech` reflects CORS for any origin (including `localhost`), so the browser-to-EchoID fetch works with no proxy
- Found that the EchoID API's `display_name` is `null` for the test address on both account types — the "Charles" name shown in the v0.2 prototype came only from the local `card_store.json` binding, which the frontend no longer has access to; real profiles without a display name will render "UNNAMED" on the kiosk
- `backend/server.py` / `backend/pn532_reader.py` demoted to reference-only, then removed from the repo in v0.3.1

### v0.3.1 — Three decisions settled, Pi script scaffolded
- **Browser control: reopen a new Chromium process per tap.** Simpler for a first implementation; the cost is a multi-second cold start and window flash, and old processes must be killed. Reuse-via-DevTools stays available as a drop-in upgrade behind `open_kiosk()`. Worth checking on real hardware first whether `chromium-browser <url>` already reuses a running instance — if so the kill logic is unnecessary.
- **Unbound card: navigate to `/?status=unbound`.** Silence was rejected: at a live demo, a tap with no visible response is indistinguishable from broken hardware. The parameter carries no UID and reveals nothing about the binding table, so the decoupling the contract protects is intact.
- **Frontend hosting: Vercel.** The Pi runs zero Node processes; network is already a hard dependency through the EchoID API, so local hosting would buy very little availability.
- Frontend: added the `unbound` error state (`?status=unbound`, `?preview=unbound`); header now reads FORGECARD only
- Added `forgecard_kiosk.py` as a comment-only scaffold with a `--keyboard` mode, so the Pi-side logic can be written and run before any hardware arrives
- Removed `backend/` entirely: the WebSocket prototype was moved out of the repo, leaving a directory named after a component that no longer exists. Its two requirements files moved to the repo root, dropping `fastapi` / `uvicorn` / `pydantic` — nothing imports them now that there is no server, and `requests` is the only remaining core dependency

### Up Next
- Implement `forgecard_kiosk.py` (UID normalization, debounce, subprocess navigation)
- Wire a physical PN532 to a Raspberry Pi over I2C
- Point `forgecard.echoforgellc.tech` at the deployed frontend
- Decide whether EchoID profiles should get a display-name fallback, and if so where that belongs

---

# License


Apache-2.0 license

ForgeCard V0 — 2026
