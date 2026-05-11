# GRBL Python G-code Sender

A minimal but practical Python CLI script to send G-code files to a GRBL-based CNC controller over a serial connection.

This repository provides:
- `gcode_sender.py`: the sender script
- `requirements.txt`: minimal dependency list (`pyserial`)

---

## Features

- Connects to a GRBL controller via serial port
- Optional GRBL soft reset (`Ctrl+X`) before streaming
- GRBL wake-up initialization (`\r\n\r\n` + startup wait)
- Streams G-code line-by-line (not whole-file burst)
- Waits for controller acknowledgment after each line
  - success: `ok`
  - failure: `error:*` / `ALARM:*`
- Reports the exact file line and command on failure
- Supports serial and per-line response timeouts
- Skips blank lines and strips common G-code comments (`;` and `( ... )`)

---

## Requirements

- Python 3.8+
- A GRBL-compatible device connected through USB/serial
- Access to the correct serial port:
  - Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.
  - macOS: `/dev/tty.usbserial-*`, `/dev/tty.usbmodem*`
  - Windows: `COM3`, `COM4`, etc.

---

## Installation

```bash
python -m pip install -r requirements.txt
```

Dependency used:
- `pyserial>=3.5,<4`

---

## Quick Start

```bash
python gcode_sender.py --port /dev/ttyUSB0 --file /absolute/path/to/job.gcode
```

Example with explicit settings:

```bash
python gcode_sender.py \
  --port /dev/ttyUSB0 \
  --file /home/user/jobs/part.gcode \
  --baud-rate 115200 \
  --line-timeout 10 \
  --read-timeout 1 \
  --write-timeout 2 \
  --soft-reset
```

---

## CLI Options

| Option | Description | Default |
|---|---|---|
| `--port` | Serial port of the GRBL controller (required) | — |
| `--file` | Path to G-code file to stream (required) | — |
| `--baud`, `--baud-rate` | Serial baud rate | `115200` |
| `--line-timeout` | Max seconds to wait for `ok/error` after each sent line | `10` |
| `--read-timeout` | Serial read timeout in seconds | `1` |
| `--write-timeout` | Serial write timeout in seconds | `2` |
| `--soft-reset` | Send GRBL soft reset (`Ctrl+X`) before wake-up sequence | disabled |

---

## How Streaming Works

1. Open serial connection with the configured baud and timeouts.
2. (Optional) Send GRBL soft reset (`Ctrl+X`).
3. Send wake-up sequence (`\r\n\r\n`) and wait for startup.
4. Read the G-code file line-by-line.
5. For each useful command line:
   - send line to GRBL
   - wait for response
   - continue on `ok`
   - stop and report on `error:*` or `ALARM:*`
6. Exit with success code when all lines are acknowledged.

---

## Exit Codes

- `0`: completed successfully
- `1`: serial/streaming error
- `2`: G-code file not found

---

## Troubleshooting

### 1) Permission denied on serial port (Linux)

If you get permission errors, add your user to `dialout` (or equivalent group):

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in.

### 2) Wrong serial port

Check available ports and retry with the correct one.

### 3) Device not responding / timeout

- Verify baud rate (GRBL commonly uses `115200`)
- Check USB cable and power
- Close other software using the same serial port
- Increase `--line-timeout` for slower controllers

### 4) Immediate `ALARM` responses

This usually indicates machine state/limits/homing issues. Resolve machine alarms before re-running the sender.

---

## Safety Notes

- Always test with air-cuts or safe Z height first.
- Keep an emergency stop accessible.
- Validate your G-code in a simulator when possible.

---

## Script File

- `gcode_sender.py` — main sender CLI script

Run help at any time:

```bash
python gcode_sender.py --help
```
