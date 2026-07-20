# ForgeCard V0

A local-first NFC identity binding prototype for the EchoForge ecosystem.

---

## Overview

ForgeCard V0 is the first working prototype of the ForgeCard project.

Its purpose is to demonstrate the complete identity flow:

```
NFC Card
    ↓
Card UID
    ↓
Local Mapping (JSON)
    ↓
Cardano Stake Address
    ↓
EchoID Profile (via HTTPS)
    ↓
Identity Information
```

Card-to-stake-address bindings are stored locally in a JSON file. Identity data (tier, role, tagline, etc.) is fetched live from the EchoID API over HTTPS. No blockchain interaction is required — the Cardano stake address is only used as a lookup key.

---

# Project Structure

```
forgecard-v0/

├── card_store.py       # Local data layer: read/write/normalize UID bindings
├── bind_card.py         # CLI: bind a card UID to a Cardano stake address
├── test_lookup.py       # CLI: look up a card's local binding by UID
├── echoid_client.py     # HTTPS client for the EchoID profile API
├── forgecard_demo.py    # CLI: full flow — UID -> binding -> EchoID profile display
├── card_store.json      # Local binding database (generated automatically, gitignored)
├── README.md
└── .venv/
```

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

# Current Features

* UID normalization
* Local JSON storage for card ↔ stake address bindings
* Bind an NFC UID to a Cardano stake address (`bind_card.py`)
* Look up a binding by UID (`test_lookup.py`)
* Fetch a live EchoID profile by stake address over HTTPS (`echoid_client.py`)
* Combined binding + profile demo with formatted terminal output (`forgecard_demo.py`)
* Graceful handling of unregistered cards and missing EchoID profiles
* Command-line interfaces (CLI) throughout

---

# Next Milestone

Replace manual UID input with a real NFC reader (PN532) on Raspberry Pi.

Future workflow:

```
NFC Reader
      ↓
Read UID
      ↓
lookup_uid(uid)
      ↓
Cardano Stake Address
      ↓
EchoID Profile
      ↓
Profile Display
```

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

### Up Next
- Connect PN532 NFC reader
- Read real NFC UID
- Replace manual input with hardware reader

---

# License


Apache-2.0 license

ForgeCard V0 — 2026
