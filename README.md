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
Identity Information
```

At this stage, all data is stored locally in a JSON file. No network connection or blockchain interaction is required.

---

# Project Structure

```
forgecard-v0/

├── card_store.py      # Local data layer
├── bind_card.py       # Bind a card UID to a Cardano stake address
├── test_lookup.py     # Query a card by UID
├── card_store.json    # Local binding database (generated automatically)
├── README.md
└── .venv/
```

---

# Requirements

* Python 3.13+
* macOS / Linux / Raspberry Pi OS

Python standard libraries used:

* json
* pathlib
* argparse

No third-party packages are required for Week 3.

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
UID: 04A1B2C3
质押地址: stake1test
显示名称: Charles
```

---

# Lookup a Card

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
显示名称：Charles
质押地址：stake1test
```

If the UID is not registered:

```
未注册
```

---

# Local Database Format

The local database is stored as JSON.

Example:

```json
{
  "04A1B2C3": {
    "stake_address": "stake1test",
    "display_name": "Charles"
  }
}
```

---

# Week 3 Features

* UID normalization
* Local JSON storage
* Bind NFC UID to Cardano stake address
* Lookup by UID
* Handle unregistered cards
* Command-line interface (CLI)

---

# Next Milestone (Week 4)

Replace manual UID input with a real NFC reader.

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
EchoID
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

### Week 4
- Connect PN532 NFC reader
- Read real NFC UID
- Replace manual input with hardware reader

---

# License


Apache-2.0 license

ForgeCard V0 — 2026
