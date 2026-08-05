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
lookup_uid(uid)  →  Cardano Stake Address   hands the URL to the running Chromium
    ↓                                       http://<frontend>/?address=<stake_address>
subprocess: chromium <url> ─────────────────┘
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

├── frontend/             # Kiosk display (Next.js), styled per DESIGN.md — Vercel root directory
│   ├── src/
│   │   ├── app/             # page.js — reads ?address= / ?status=, drives idle/scanning/result/error
│   │   │                    #   icon.svg — favicon, auto-detected by the App Router
│   │   ├── components/      # IdleView, ScanningView, ResultView, ErrorView, etc.
│   │   └── lib/             # echoid.js (client-side EchoID fetch), format.js, constants.js
│   └── public/
│       └── tap-card.svg     # Standalone "tap card" key art (EchoForgeStyle, animated) — docs/press use
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

There is no keyboard or mock reader — the PN532 is the only read path, so the read loop can only be run on the Pi. URL building and UID normalization are pure functions and remain testable on a Mac, because the hardware drivers are imported inside `init_pn532()` rather than at module level.

**2. Frontend** (the kiosk display) — already implements its half of the contract:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_ECHOID_API_URL, defaults to production
npm run dev                        # or: npm run build && npm start
```

On load it reads `?address=` (or `?status=`) from the URL, calls the EchoID API directly from the browser (`src/lib/echoid.js` — tries `accountType=individual` then falls back to `institutional`), and renders: idle ("tap card", bare URL) → verifying → EchoID profile card → auto-return to idle (clears the query param client-side). A URL that already carries `?address=` or `?status=` starts at verifying rather than rendering idle first, and verifying is held for at least `MIN_SCANNING_MS` (`src/lib/constants.js`) so a fast answer cannot flash past — turn that one constant if the pacing feels wrong. Append `?preview=ok|idle|scanning|unbound|no_profile|error` to preview a state without Python or a real address. You can also drive the real paths directly: `?address=<any stake address>` or `?status=unbound`.

See [MAINTENANCE.md](MAINTENANCE.md) for Raspberry Pi setup and bring-up order. Kiosk process management — autostart, `--kiosk` flags, tab cleanup — is v1 scope; v0 starts Chromium by hand and fullscreens it with F11.

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

Finish the Pi-side read path: PN532 initialization, then the read loop with debounce. Everything before it — URL building, UID normalization, the binding table — is done and verified on the Pi with real cards. v0 is complete when a tap moves the screen to the right profile; autostart and kiosk hardening are v1.

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

### v0.3.2 — Pi bring-up: scope split and hardware findings
- **Kiosk process management deferred to v1.** v0 stops at "a tap navigates the screen." Autostart, `--kiosk` flags, tab cleanup, and crash recovery are v1 scope; v0 starts Chromium by hand and fullscreens it with F11. F11 substitutes for the `--kiosk` flag's fullscreen only — the mouse pointer, session-restore bubbles, and update prompts that the flags suppress are all still visible, which is fine for bring-up and not fine in front of an audience
- **Keyboard mode removed.** The PN532 is the only read path, so the read loop can only be developed on the Pi. The cost was accepted deliberately: a mock reader exercises the loop's shape but not the thing that actually breaks. Blocks 1-3 stay Mac-testable because `init_pn532()` imports the hardware drivers inside the function body instead of at module level
- **Verified on real hardware: `chromium <url>` does not start a second process.** It hands the URL to the already-running instance, which opens a new tab and brings it to the front. The screen updates, so the kill logic sketched in v0.3.1 turns out to be unnecessary for v0 — the open question recorded there is now closed. The cost is one accumulated tab and one cold page load per tap, both v1's problem
- The Chromium binary is `chromium`, not `chromium-browser`; Debian renamed it in Bookworm and Raspberry Pi OS inherited the change. `BROWSER_CMD` was written against the old name and would have failed as a `subprocess` `FileNotFoundError`
- Blocks 1-3 of `forgecard_kiosk.py` complete (URL building, browser invocation, UID normalization). Blocks 4-5 (PN532 init, read loop + debounce) remain, and are Pi-only
- Three physical cards bound and read on the Pi. Two failure modes found in the process, both now in MAINTENANCE.md troubleshooting: `card_store.json` is gitignored and does not survive a `git clone`, so a fresh Pi checkout reports every card as unbound; and hand-editing that file instead of using `bind_card.py` produced a missing comma and a `JSONDecodeError`
- One of the real card UIDs ends in `0x07`, so the zero-padding trap the normalization comments warn about is live in the actual data rather than hypothetical

### v0.3.3 — Read loop live, kiosk pacing fixed
- **The full chain runs on the Pi.** Tap a bound card and the screen lands on that stake address's EchoID profile; tap an unbound one and it lands on "Card Not Registered". Blocks 4-5 of `forgecard_kiosk.py` are written, so every block of the Pi-side script now exists
- **Three view changes in under a second turned out not to be a bug.** A tap on a bound card visibly changed the screen three times, while unbound cards looked fine. It is the frontend's own state machine — a page loaded with `?address=` rendered idle for one frame, switched to `scanning`, then to `result` as soon as EchoID answered, and `AnimatePresence` never finished a 0.5s transition before the next one started. The unbound path skips both the idle frame and the network request, which is why only bound cards showed it
- Fixed in the frontend, not in Python: `page.js` now initializes `viewState` from the URL, so a page loaded with `?address=` or `?status=unbound` never renders idle first, and `MIN_SCANNING_MS` (`lib/constants.js`) holds "Verifying" on screen for a floor duration even when the answer is already known. Both paths now have the same rhythm — the unbound path gains a visible acknowledgement of the tap instead of snapping straight to the error
- The Python-side deduction that ruled out a debounce fault is worth keeping: a card recognized as *bound* has necessarily matched a `card_store.json` key exactly, so its UID is stable, so `last_uid == uid` holds, so the debounce cannot fire twice inside its window. When a symptom appears on one card and not another, check what differs about the *path*, not the reader

### Deferred to V1 — explicit decision, not drift
Recorded so a later reader sees a decision here rather than an oversight.

- **Power-loss-safe writes.** `card_store.json` is rewritten in place with no atomic-replace or fsync; a power cut mid-write can truncate the binding table.
- **Network failure handling (T4/T5).** The kiosk's behavior when the EchoID API is unreachable or slow is untested beyond the frontend's existing catch-all error state.
- **Kiosk autostart.** V0 drops automatic kiosk launch in favor of starting Chromium by hand and pressing F11.
  * *Rationale:* V0's only deliverable is a YouTube demo video, and the two approaches are indistinguishable on video.
  * *Trigger to restore:* the moment the device has to run unattended — a live on-site demo, recovery after a power cut, or real users tapping it — kiosk mode re-enters scope.
  * *Implementation note:* Wayland compositor autostart is a simpler path than SSH plus a systemd unit. V1 should take that route and replace the debounce at the same time.
- **Debounce semantics.** `last_seen` is refreshed only when a tap fires, so a card left resting on the reader re-triggers every `DEBOUNCE_SECONDS`. Accepted for V0, where the demo is run at home by the person holding the card. V1 should switch to edge triggering — fire on the transition from "no card" to "card present" — so one tap is one trigger regardless of how long the card rests.

### Up Next
- Test the read loop's fault tolerance: pull the reader's wiring or drop the network mid-run and confirm the loop survives instead of exiting
- Measure how many taps the Pi tolerates before tab accumulation degrades it
- Move UID prefix normalization into `std_uid()` so `bind_card()` and `lookup_uid()` cannot disagree
- Decide whether EchoID profiles should get a display-name fallback, and if so where that belongs

---

# License


Apache-2.0 license

ForgeCard V0 — 2026
