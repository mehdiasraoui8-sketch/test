#!/usr/bin/env python3
import argparse
import re
import sys
import time
from pathlib import Path

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream a G-code file to a GRBL device over serial."
    )
    parser.add_argument("--port", required=True, help="Serial port (for example COM3 or /dev/ttyUSB0)")
    parser.add_argument("--file", required=True, help="Path to .gcode file")
    parser.add_argument(
        "--baud",
        "--baud-rate",
        dest="baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--line-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for ok/error after sending each line (default: 10)",
    )
    parser.add_argument(
        "--read-timeout",
        type=float,
        default=1.0,
        help="Serial read timeout in seconds (default: 1)",
    )
    parser.add_argument(
        "--write-timeout",
        type=float,
        default=2.0,
        help="Serial write timeout in seconds (default: 2)",
    )
    parser.add_argument(
        "--soft-reset",
        action="store_true",
        help="Send GRBL soft reset (Ctrl-X) before wake-up",
    )
    return parser.parse_args()


def read_line(ser: serial.Serial) -> str:
    return ser.readline().decode("utf-8", errors="replace").strip()


def initialize_grbl(ser: serial.Serial, soft_reset: bool) -> None:
    if soft_reset:
        ser.write(b"\x18")
        ser.flush()
        time.sleep(0.2)

    ser.write(b"\r\n\r\n")
    ser.flush()
    time.sleep(2.0)

    while ser.in_waiting:
        startup = read_line(ser)
        if startup:
            print(f"[GRBL] {startup}")


def clean_gcode_line(raw_line: str) -> str:
    """Strip whitespace and common GRBL comment styles from a G-code line."""
    line = raw_line.strip()
    if not line:
        return ""

    line = line.split(";", 1)[0]
    line = re.sub(r"\([^)]*\)", "", line)

    return line.strip()


def wait_for_grbl_response(ser: serial.Serial, timeout: float) -> None:
    started = time.time()
    while time.time() - started < timeout:
        response = read_line(ser)
        if not response:
            time.sleep(0.01)
            continue

        response_lower = response.lower()
        if response_lower == "ok":
            return
        if response_lower.startswith("error") or response_lower.startswith("alarm"):
            raise RuntimeError(response)

        print(f"[GRBL] {response}")

    raise TimeoutError("Timed out waiting for GRBL response")


def stream_gcode(ser: serial.Serial, gcode_path: Path, line_timeout: float) -> None:
    with gcode_path.open("r", encoding="utf-8") as gcode_file:
        for line_number, raw_line in enumerate(gcode_file, start=1):
            line = clean_gcode_line(raw_line)
            if not line:
                continue

            print(f"-> {line}")
            ser.write((line + "\n").encode("utf-8"))
            ser.flush()

            try:
                wait_for_grbl_response(ser, timeout=line_timeout)
            except (RuntimeError, TimeoutError) as exc:
                raise RuntimeError(f"Line {line_number}: {line} | {exc}") from exc


def main() -> int:
    args = parse_args()
    gcode_path = Path(args.file)

    if not gcode_path.is_file():
        print(f"G-code file not found: {gcode_path}", file=sys.stderr)
        return 2

    try:
        with serial.Serial(
            args.port,
            args.baud,
            timeout=args.read_timeout,
            write_timeout=args.write_timeout,
        ) as ser:
            initialize_grbl(ser, soft_reset=args.soft_reset)
            stream_gcode(ser, gcode_path, line_timeout=args.line_timeout)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Streaming failed: {exc}", file=sys.stderr)
        return 1

    print("Done: G-code stream completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
