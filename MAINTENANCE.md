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
│                              └── subprocess: open/replace the kiosk
│                                  browser at
│                                  http://<frontend>/?address=<stake_address>
│                                                       │
└── Chromium --kiosk ──────────────────────────────────┘
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
| Browser control | Reopen a new process per tap | Old Chromium must be killed or the Pi runs out of memory; kill timing matters. First verify whether `chromium-browser <url>` reuses an already-running instance — if it does on this hardware, the kill logic becomes unnecessary. |
| Unbound card | Navigate to `?status=unbound` | A tap on an unregistered card must never look like broken hardware. |
| Frontend hosting | Vercel | The Pi runs zero Node processes. Network is already a hard dependency via the EchoID API. |

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

`requirements-pi.txt` will not install on macOS. That's expected: develop with `--keyboard` mode, which needs neither the drivers nor the hardware.

Bind real cards before deploying (`card_store.json` is local and gitignored):

```bash
python bind_card.py <UID> <stake_address> <display_name>
```

Develop without hardware — the keyboard mode substitutes `input()` for the PN532 and exercises every other block:

```bash
python forgecard_kiosk.py --keyboard
```

For step 3, the settled decision is **reopen a new Chromium process per tap**. Before writing any process-management code, check whether `chromium-browser <url>` on this Pi hands the URL to an already-running instance rather than starting a second one — if it does, there is nothing to kill and the whole problem disappears. If it doesn't, the previous process must be terminated (track its `Popen` object rather than searching with `pgrep`) and allowed to exit before the replacement starts. Upgrading later to `--remote-debugging-port` + DevTools navigation is a drop-in swap behind `open_kiosk()`; it removes the window flash and the multi-second cold start, at the cost of needing a "browser is gone, relaunch it" branch.

### 3. Frontend

Settled decision: the frontend is deployed to **Vercel** at `https://forgecard.echoforgellc.tech`, and the Pi runs no Node process at all. Point the kiosk browser at that URL.

For local frontend development only (not on the Pi):

```bash
cd frontend
npm install
npm run dev
```

### 4. Kiosk mode (autostart)

Launch Chromium in kiosk mode pointed at the frontend's base URL (no `?address=` yet — that's what idle looks like):

```bash
chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 https://forgecard.echoforgellc.tech
```

To start on boot, either add a systemd service for your Pi-side Python script (pattern below — adjust `ExecStart` to whatever you end up calling it) or point `~/.config/lxsession/LXDE-pi/autostart` at it if using the Pi's default desktop:

```ini
# /etc/systemd/system/forgecard-reader.service
[Unit]
Description=ForgeCard PN532 reader -> kiosk browser
After=network.target

[Service]
WorkingDirectory=/home/pi/forgecard-v0
ExecStart=/home/pi/forgecard-v0/.venv/bin/python <your_script>.py
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

---

## Environment Variables

**Frontend** (`frontend/.env.local`, copy from `.env.local.example`):

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_ECHOID_API_URL` | `https://api-id.echoforgellc.tech` | EchoID profile API the browser calls directly once it has `?address=` |

No backend environment variables — there's no server-side component to the kiosk anymore beyond your Pi-side script, which reads `card_store.json` directly.

---

## Troubleshooting

**Kiosk shows "TAP CARD TO BEGIN" and never changes.** The Pi script isn't reaching the browser with a new URL. Confirm it's actually running, and that whatever mechanism it uses to update the kiosk window (new process vs. remote-debugging navigation) is working — test manually by opening `http://<frontend>/?address=<a known-good stake address>` yourself.

**Card taps produce "NO ECHOID PROFILE."** Either the bound stake address genuinely has no EchoID profile yet, or the address is malformed. Confirm with `python test_lookup.py`.

**A card you know is bound produces "CARD NOT REGISTERED."** Almost always UID normalization, not a missing binding — `lookup_uid` fails silently by returning `None`, so a mis-formatted UID is indistinguishable from an unbound card. Print the normalized UID next to the `card_store.json` key and compare character by character; the usual culprits are a surviving `0x` prefix, a byte that lost its leading zero (`"7"` instead of `"07"`, which shifts everything after it), or lowercase hex.

**A real user's name shows "UNNAMED" on the kiosk.** The EchoID API's `display_name` field is `null` for their profile — this is expected now that the frontend only ever sees what the EchoID API returns, not the friendly name recorded locally in `card_store.json` at bind time. See the README's v0.3 dev log entry.

**Browser console shows a CORS error calling `api-id.echoforgellc.tech`.** Unlikely — the API reflects `Access-Control-Allow-Origin` for whatever origin makes the request, verified against both `localhost:3000` and `forgecard.echoforgellc.tech`. If it does happen, it means the API's CORS policy changed; check with whoever owns the EchoID API before working around it client-side.

**Same card scanned twice in a row does something weird.** Debouncing repeat reads of the same UID is `forgecard_kiosk.py`'s responsibility — a card resting on the reader fires continuously. The earlier prototype used a 5-second window; treat that as a starting point, not a rule, and tune it against a real card.

---

## Deploying Frontend Updates

The frontend is a standard Next.js app — deploy it to Vercel like other EchoForge products (see root `DESIGN.md` -> Technical Architecture) and point `forgecard.echoforgellc.tech` at it. Rebuilding the frontend does not require touching the Pi at all, since it talks to the EchoID API directly and has no backend dependency.

**Vercel Root Directory must be `frontend`.** This repo's root holds the Pi-side Python, not the Next.js app — there is no `package.json` at the top level. If Root Directory is left at the repo root, Vercel's framework detection finds nothing, falls back to the "Other" preset, and the build fails with:

```text
Error: No Output Directory named "public" found after the Build completed.
```

Fix it in Vercel -> Project -> Settings -> Build and Deployment: set **Root Directory** to `frontend`, confirm **Framework Preset** is `Next.js`, then redeploy. Leave Build Command / Output Directory on their defaults — with the preset correct, Vercel handles `.next` itself. Do not add a root `vercel.json` to work around this; the Root Directory setting is the supported path and keeps the Python and frontend halves cleanly separated.
