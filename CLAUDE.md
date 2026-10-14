# CLAUDE.md

Working rules for AI agents (Claude Code included) operating in this repo.

## Why this file exists

The hardware layer of ForgeCard is the one part of this project where the code must be written by Charles, by hand — that discipline is written into the V0 manual. The documented failure mode has already happened once in this repo: an AI produced a complete, working `pn532_reader.py`. The code was correct, so nothing signaled that a loss had occurred; the loss was the practice that never happened. The file was reverted. This file makes the boundary mechanical instead of memory-dependent.

## Red line: hardware-layer Python is human-written

Do NOT write, generate, complete, or refactor code that:

- talks to the PN532 / NFC reader or any GPIO / I2C / SPI / UART interface (`adafruit_pn532`, `busio`, `board`, `digitalio`, and similar)
- belongs to the Pi-side kiosk script: the card read loop, UID debounce, UID formatting, `subprocess` control of the kiosk browser
- launches any of the above (systemd units, autostart entries — a template lives in MAINTENANCE.md; adapting it is Charles's job)

"Do not write" includes example code, reference implementations, runnable "pseudocode", filling in TODOs, and autocomplete-style completions. If a file mixes hardware and software concerns, treat the whole file as hardware.

Allowed in the hardware layer:

- reviewing code Charles wrote: point out problems precisely ("the read loop doesn't handle a timeout") — but do not output the corrected code
- explaining concepts, naming functions / APIs, linking documentation
- changing a configuration value in these files, such as a hostname or URL. That is not writing code: the red line protects the practice of writing the logic, not the constants it reads (Charles, 2026-10-14)

## Explicit exceptions

If Charles states in his own words that he has decided to have AI write a specific hardware-layer piece, comply — and add a line to the README dev log recording the exception. This file guards against silent drift, not conscious trade-offs.

## Software layer: normal rules

`frontend/`, documentation, and anything that never touches the reader or the kiosk process are normal AI-assisted territory.

## Repo contracts — do not re-architect

- The entire interface between Python and the frontend is one URL: `http://<frontend>/?address=<stake_address>`. Do not reintroduce a backend service, WebSocket, or push channel — that was v0.2 and it was removed deliberately (see the README dev log).
- Python never calls the EchoID API and never decides `accountType`. The frontend does both.

## Docs follow reality

If files are added, deleted, or renamed, update README.md and MAINTENANCE.md in the same change. Stale references to deleted files have already happened in this repo.
