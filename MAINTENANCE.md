# ForgeCard Maintenance

Deployment and upkeep guide for the ForgeCard kiosk (Pi-side Python + frontend). For product behavior see [README.md](README.md); for visual design rules see the root `DESIGN.md` (EchoForgeStyle).

---

## Architecture

```
Raspberry Pi                                    Kiosk Display (Next.js)
├── PN532 reader ──I2C──> your Python script
│                              │
│                              ├── card_store.py   (local UID -> stake address)
│                              │
│                              └── subprocess: hand the URL to the
│                                  already-running Chromium
│                                  http://<frontend>/?address=<stake_address>
│                                                       │
└── Chromium (v0: started by hand, F11) ───────────────┘
                                                         │
                                          frontend reads ?address=, calls the
                                          EchoID API itself, renders the card
```

The Pi-side Python and the kiosk browser run on the **same Raspberry Pi**. There is no persistent backend service and no WebSocket — each card tap is a fresh page load. The Python script's entire job is: read a UID off the PN532, resolve it to a stake address with `lookup_uid()` from `card_store.py`, and point the kiosk browser at the right URL. It never calls the EchoID API and never decides `accountType` — that's the frontend's job, done client-side in `frontend/src/lib/echoid.js`.

The URL is the entire interface between the two halves, and it has exactly two forms:

| Situation | URL the Pi navigates to | What the screen shows |
|---|---|---|
| Card has a local binding | `/?address=<stake_address>` | Verifying → EchoID profile card |
| Card read, but no binding | `/?status=unbound` | "Card Not Registered" |

Note that `?status=unbound` carries no UID and reveals nothing about the local binding table — the decoupling the contract exists to protect is intact. Navigation is always one-way: Python pushes a URL and never resets the screen, because the frontend returns itself to idle on a timer.

### Settled decisions

| Decision | Choice | Consequence to keep in mind |
|---|---|---|
| Browser control | v0: hand the URL to the already-running Chromium | **Verified on the Pi:** `chromium <url>` does not start a second process — it passes the URL to the running instance, which opens it in a **new tab** and brings that tab to the front. The screen updates, so v0 needs no process tracking and no kill logic. The cost is one accumulated tab and one cold page load per tap. |
| Kiosk process management | Deferred to v1 | Autostart, `--kiosk` flags, tab/window cleanup, and crash recovery are v1 scope. In v0 Chromium is started by hand and fullscreened with F11. |
| Unbound card | Navigate to `?status=unbound` | A tap on an unregistered card must never look like broken hardware. |
| Frontend hosting | Vercel | The Pi runs zero Node processes. Network is already a hard dependency via the EchoID API. |

The browser binary is **`chromium`**, not `chromium-browser`. Debian renamed both the package and the executable in Bookworm; Raspberry Pi OS inherited the change. Confirm with `ls /usr/bin | grep -i chrom` before hardcoding it anywhere.

An earlier prototype ran a FastAPI WebSocket service on the Pi that resolved the EchoID profile itself and pushed it to the frontend. That coupled Python to the `accountType` decision, which is why the URL contract above replaced it. Those files have been moved out of this repo — there is no backend directory, no server process, and no WebSocket anywhere in the kiosk.

---

## Raspberry Pi Setup

### 1. Hardware

Wire the PN532 to the Pi over **I2C**:

| PN532 | Raspberry Pi |
|---|---|
| VCC | 3.3V or 5V (per module) |
| GND | GND |
| SDA | SDA (GPIO2) |
| SCL | SCL (GPIO3) |

Enable I2C: `sudo raspi-config` -> Interface Options -> I2C -> Enable. Confirm the reader shows up with `i2cdetect -y 1` (default PN532 address `0x24`).

### 2. Pi-side Python

`forgecard_kiosk.py` is the Pi-side entry point. It must fulfill this contract:

1. Read a UID from the PN532, normalize it to the `card_store.json` key format (uppercase hex, zero-padded, no `0x` prefix), and debounce repeat reads of the same card.
2. `card_store.lookup_uid(uid)` -> stake address.
3. Navigate the kiosk browser to `/?address=<stake_address>`, or to `/?status=unbound` when step 2 found no binding.

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # requests -- needed everywhere
pip install -r requirements-pi.txt     # adafruit PN532 drivers -- Pi only
```

`requirements-pi.txt` will not install on macOS. That's expected, and it does not block Mac-side work: URL building and UID normalization are pure functions, and `init_pn532()` imports `board` / `busio` / `adafruit_pn532` inside the function body precisely so the rest of the file still imports on a machine without the drivers. There is no keyboard/mock reader — the PN532 is the only read path, so the read loop itself can only be exercised on the Pi.

Bind real cards before deploying — **`card_store.json` is local and gitignored, so it does not travel with a `git clone`.** A fresh checkout on the Pi has no bindings at all, and every tap will resolve to `?status=unbound`, which is indistinguishable from a UID normalization bug. Bind on the machine that will read the cards:

```bash
python bind_card.py <UID> <stake_address> <display_name>
```

Use `bind_card.py` rather than editing the JSON by hand. It routes through `json.dump()`, which cannot emit invalid syntax, and through `std_uid()`, which normalizes the key. A hand-edited file that is missing a comma between entries fails at `json.load()` — loudly, with a line and column, but not until something calls `read_bindings()`. Validate with `python -m json.tool card_store.json`.

For step 3, see the browser control decision above: on this hardware `chromium <url>` hands the URL to the running instance, which opens a new tab and focuses it, so v0 needs no process management at all. The v1 upgrade is `--remote-debugging-port` + DevTools navigation, a drop-in swap behind `open_kiosk()`: it navigates the current tab instead of opening another one, removing both the tab accumulation and the multi-second cold start, at the cost of needing a "browser is gone, relaunch it" branch.

Suggested bring-up order on the Pi — each step adds exactly one new way to fail:

1. `python test_lookup.py`, one entry per card. Proves the binding table before any hardware is involved.
2. `chromium <url>` by hand with a known-good `?address=`. Proves the frontend and the URL shape.
3. `init_pn532()` plus a single read, from a REPL or a throwaway script. Proves wiring and drivers. Do not run `forgecard_kiosk.py` yet — it will hit the unimplemented read loop.
4. Chain one read through normalization, `lookup_uid()`, and URL building by hand. This is the whole v0 contract minus repetition; if it works here, the read loop only has to add debounce and error tolerance.
5. Write the read loop.

### 3. Frontend

Settled decision: the frontend is deployed to **Vercel** at `https://forgecard.echoforgeef.com`, and the Pi runs no Node process at all. Point the kiosk browser at that URL.

For local frontend development only (not on the Pi):

```bash
cd frontend
npm install
npm run dev
```

### 4. Kiosk mode

**v0: by hand.** Start Chromium pointed at the frontend's base URL (no `?address=` yet — that's what idle looks like) and press F11:

```bash
chromium https://forgecard.echoforgeef.com
```

F11 replaces the `--kiosk` flag's fullscreen behavior, but nothing else it did. A hand-fullscreened window still shows the mouse pointer, session-restore bubbles, and update prompts — acceptable while bringing the reader up, not acceptable in front of an audience. `unclutter` hides the idle pointer; the flags below suppress the rest.

**v1: autostart and hardening.** Deferred deliberately (see Settled decisions). What it owns:

```bash
chromium --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 https://forgecard.echoforgeef.com
```

For starting on boot, **Wayland compositor autostart is the preferred route** — it is a simpler path than SSH plus a systemd unit, and V1 should take it while replacing the debounce at the same time (see the README's "Deferred to V1"). The systemd pattern below is kept as the fallback for a headless or non-Wayland setup; adjust `ExecStart`, `User`, and `WorkingDirectory` to the real account, as the Pi in use is `charles`, not the `pi` default. On the Pi's older LXDE desktop the equivalent hook is `~/.config/lxsession/LXDE-pi/autostart`.

```ini
# /etc/systemd/system/forgecard-reader.service
[Unit]
Description=ForgeCard PN532 reader -> kiosk browser
After=network.target

[Service]
WorkingDirectory=/home/charles/forgecard-v0
ExecStart=/home/charles/forgecard-v0/.venv/bin/python forgecard_kiosk.py
Restart=on-failure
User=charles

[Install]
WantedBy=multi-user.target
```

Also v1's problem: tab accumulation. Every tap adds a tab to the running Chromium, which is invisible in fullscreen but real in memory. Either cap it via DevTools navigation (reusing the current tab) or measure how many taps the Pi tolerates and decide it is enough.

---

## Environment Variables

**Frontend** (`frontend/.env.local`, copy from `.env.local.example`):

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_ECHOID_API_URL` | `https://api-id.echoforgeef.com` | EchoID profile API the browser calls directly once it has `?address=` |

No backend environment variables — there's no server-side component to the kiosk anymore beyond your Pi-side script, which reads `card_store.json` directly.

---

## Troubleshooting

**`chromium-browser: command not found`.** The binary is `chromium` on Bookworm and later. Check with `ls /usr/bin | grep -i chrom`, and update `BROWSER_CMD` in `forgecard_kiosk.py` to match — a wrong value there surfaces as `FileNotFoundError` from `subprocess`, not as a browser problem.

**Kiosk shows "TAP CARD TO BEGIN" and never changes.** The Pi script isn't reaching the browser with a new URL. Confirm it's actually running, and that whatever mechanism it uses to update the kiosk window is working — test manually by opening `http://<frontend>/?address=<a known-good stake address>` yourself.

**`json.decoder.JSONDecodeError` from `read_bindings()`.** `card_store.json` was hand-edited into invalid syntax; the usual cause is a missing comma between two card entries (JSON requires separators between members and forbids a trailing one — the opposite of a Python dict). The decoder reports the line and column of the first problem only, so re-check the whole file with `python -m json.tool card_store.json`, or delete it and re-run `bind_card.py` once per card. Deleting is safe: `read_bindings()` returns `{}` when the file is absent.

**Card taps produce "NO ECHOID PROFILE."** Either the bound stake address genuinely has no EchoID profile yet, or the address is malformed. Confirm with `python test_lookup.py`.

**A card you know is bound produces "CARD NOT REGISTERED."** Two causes, and they look identical because `lookup_uid` fails silently by returning `None`. First check that the table on *this* machine is not empty — `card_store.json` is gitignored, so a fresh clone on the Pi has no bindings even though the Mac does. If the table is populated, it's UID normalization: print the normalized UID next to the `card_store.json` key and compare character by character. The usual culprits are a surviving `0x` prefix, a byte that lost its leading zero (`"7"` instead of `"07"`, which shifts everything after it), or lowercase hex. Note that `std_uid()` strips separators and uppercases but does **not** zero-pad, so a short byte stays short all the way to the lookup.

**A real user's name shows "UNNAMED" on the kiosk.** The EchoID API's `display_name` field is `null` for their profile — this is expected now that the frontend only ever sees what the EchoID API returns, not the friendly name recorded locally in `card_store.json` at bind time. See the README's v0.3 dev log entry.

**Browser console shows a CORS error calling `api-id.echoforgeef.com`.** Unlikely — the API reflects `Access-Control-Allow-Origin` for whatever origin makes the request, verified against both `localhost:3000` and the kiosk host (then `forgecard.echoforgellc.tech`, now `forgecard.echoforgeef.com`). If it does happen, it means the API's CORS policy changed; check with whoever owns the EchoID API before working around it client-side.

**Same card scanned twice in a row does something weird.** Debouncing repeat reads of the same UID is `forgecard_kiosk.py`'s responsibility — a card resting on the reader fires continuously. The earlier prototype used a 5-second window; treat that as a starting point, not a rule, and tune it against a real card.

---

## Deploying Frontend Updates

The frontend is a standard Next.js app — deploy it to Vercel like other EchoForge products (see root `DESIGN.md` -> Technical Architecture) and point `forgecard.echoforgeef.com` at it. Rebuilding the frontend does not require touching the Pi at all, since it talks to the EchoID API directly and has no backend dependency.

**Vercel Root Directory must be `frontend`.** This repo's root holds the Pi-side Python, not the Next.js app — there is no `package.json` at the top level. If Root Directory is left at the repo root, Vercel's framework detection finds nothing, falls back to the "Other" preset, and the build fails with:

```text
Error: No Output Directory named "public" found after the Build completed.
```

Fix it in Vercel -> Project -> Settings -> Build and Deployment: set **Root Directory** to `frontend`, confirm **Framework Preset** is `Next.js`, then redeploy. Leave Build Command / Output Directory on their defaults — with the preset correct, Vercel handles `.next` itself. Do not add a root `vercel.json` to work around this; the Root Directory setting is the supported path and keeps the Python and frontend halves cleanly separated.
