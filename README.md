# test

Minimal Python GRBL G-code sender.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Usage

```bash
python gcode_sender.py --port /dev/ttyUSB0 --file /absolute/path/to/file.gcode
```

Common options:

- `--baud 115200` (default)
- `--line-timeout 10`
- `--read-timeout 1` and `--write-timeout 2`
- `--soft-reset` to send GRBL Ctrl-X before wake-up

The script connects over serial, performs GRBL wake-up initialization, streams G-code line-by-line, and waits for `ok`/`error` responses.
