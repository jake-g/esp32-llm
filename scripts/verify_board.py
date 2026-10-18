"""Verifies a plugged-in ESP32-S3 running esp32-llm.

Resets the board, waits for the firmware's single-line boot verdict
(``LLM_SELFTEST {...}``), and exits 0 only if the self-test passed. The
firmware self-test checks that greedy decoding reproduces the llama2.c run.c
golden output at a minimum tokens/second. A crash after the verdict, or fewer
demo generations than requested, also fails.

Example:
  python scripts/verify_board.py --port /dev/cu.usbmodem2101
  python scripts/verify_board.py --port /dev/cu.usbmodem2101 --flash
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, Iterable, List, Optional

SELFTEST_PREFIX = "LLM_SELFTEST "
RESULT_PREFIX = "LLM_RESULT "
CRASH_MARKERS = ("assert failed", "Guru Meditation", "abort() was called",
                 "Rebooting...", "Stack canary")
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT_S = 45.0
RESET_PULSE_S = 0.1
PANIC_DRAIN_S = 3.0
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT_GLOBS = ("/dev/cu.usbmodem*", "/dev/ttyACM*")

logger = logging.getLogger("verify_board")


def parse_tagged_line(line: str, prefix: str) -> Optional[Dict[str, Any]]:
  """Parses a ``PREFIX {json}`` line emitted by the firmware.

  Args:
    line: One decoded serial line (may contain log noise before the prefix).
    prefix: Tag such as ``SELFTEST_PREFIX``.

  Returns:
    The decoded JSON object, or None if the line has no valid tagged payload.
  """
  idx = line.find(prefix)
  if idx < 0:
    return None
  payload = line[idx + len(prefix):].strip()
  try:
    value = json.loads(payload)
  except json.JSONDecodeError:
    return None
  return value if isinstance(value, dict) else None


def evaluate(lines: Iterable[str]) -> Dict[str, Any]:
  """Scans serial lines for the self-test verdict, demo results, and crashes.

  Args:
    lines: Decoded serial lines in arrival order.

  Returns:
    Summary dict with ``ok``, ``selftest`` (or None), ``results`` and
    ``crash`` (first crash line after the verdict, or None). ``ok`` is True
    only when a self-test line reported ok and nothing crashed afterwards.
  """
  selftest: Optional[Dict[str, Any]] = None
  results: List[Dict[str, Any]] = []
  crash: Optional[str] = None
  for line in lines:
    parsed = parse_tagged_line(line, SELFTEST_PREFIX)
    if parsed is not None:
      if selftest is None:
        selftest = parsed
      elif not parsed.get("ok"):
        selftest = parsed
      continue
    parsed = parse_tagged_line(line, RESULT_PREFIX)
    if parsed is not None:
      results.append(parsed)
      continue
    if (selftest is not None and crash is None and
        any(marker in line for marker in CRASH_MARKERS)):
      crash = line.strip()
  ok = bool(selftest is not None and selftest.get("ok") is True and
            crash is None)
  return {"ok": ok, "selftest": selftest, "results": results, "crash": crash}


def find_port() -> Optional[str]:
  """Returns the single native-USB serial port, or None if 0 or >1 exist."""
  ports = sorted(p for pattern in PORT_GLOBS for p in glob.glob(pattern))
  if len(ports) == 1:
    return ports[0]
  if ports:
    logger.error("Multiple candidate ports %s; pass --port", ports)
  return None


def flash(port: str) -> None:
  """Builds and flashes the firmware with idf.py.

  Args:
    port: Serial port of the target board.

  Raises:
    subprocess.CalledProcessError: If idf.py fails.
  """
  logger.info("Flashing %s from %s", port, PROJECT_DIR)
  subprocess.run(["idf.py", "-C", PROJECT_DIR, "-p", port, "flash"], check=True)


def read_boot_lines(port: str, timeout_s: float, results: int) -> List[str]:
  """Resets the board and collects serial lines until the verdict arrives.

  Args:
    port: Serial port of the target board.
    timeout_s: Maximum seconds to wait for the self-test line.
    results: Extra ``LLM_RESULT`` lines to wait for after the verdict.

  Returns:
    All decoded lines read.
  """
  import serial  # pylint: disable=import-outside-toplevel

  lines: List[str] = []
  with serial.Serial() as ser:
    ser.port = port
    ser.baudrate = DEFAULT_BAUD
    ser.timeout = 0.5
    # Deassert both lines before open so the chip does not enter download
    # mode; then pulse RTS (EN) for a clean app reset.
    ser.dtr = False
    ser.rts = False
    ser.open()
    ser.rts = True
    time.sleep(RESET_PULSE_S)
    ser.rts = False
    deadline = time.monotonic() + timeout_s
    seen_results = 0
    verdict = False
    while time.monotonic() < deadline:
      raw = ser.readline()
      if not raw:
        continue
      line = raw.decode("utf-8", errors="replace").rstrip()
      lines.append(line)
      logger.debug("%s", line)
      if SELFTEST_PREFIX in line:
        verdict = True
        parsed = parse_tagged_line(line, SELFTEST_PREFIX)
        if parsed is None or not parsed.get("ok"):
          break
      elif verdict and RESULT_PREFIX in line:
        seen_results += 1
      elif verdict and any(m in line for m in CRASH_MARKERS):
        # Keep the panic dump (registers, backtrace) for addr2line.
        deadline = min(deadline, time.monotonic() + PANIC_DRAIN_S)
        results = sys.maxsize
      if verdict and seen_results >= results:
        break
  return lines


def main(argv: Optional[List[str]] = None) -> int:
  """Command-line entry point.

  Args:
    argv: Optional argument list (defaults to sys.argv).

  Returns:
    Process exit code: 0 pass, 1 self-test failed, 2 no verdict or no port.
  """
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--port", default=os.environ.get("ESP32_LLM_PORT"))
  parser.add_argument("--flash", action="store_true",
                      help="build and flash before verifying")
  parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
  parser.add_argument("--results", type=int, default=1,
                      help="demo generations to wait for after the verdict")
  parser.add_argument("-v", "--verbose", action="store_true")
  args = parser.parse_args(argv)
  logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                      format="%(levelname)s %(message)s")

  port = args.port or find_port()
  if port is None:
    logger.error("No board found; pass --port or set ESP32_LLM_PORT")
    return 2
  if args.flash:
    flash(port)

  summary = evaluate(read_boot_lines(port, args.timeout, args.results))
  selftest = summary["selftest"]
  if selftest is None:
    logger.error("No %s line within %.0f s on %s", SELFTEST_PREFIX.strip(),
                 args.timeout, port)
    return 2
  for result in summary["results"]:
    logger.info("Demo gen %s: %.2f tok/s", result.get("gen"),
                float(result.get("tok_s", 0.0)))
  if summary["crash"] is not None:
    logger.error("FAIL: crash after self-test: %s", summary["crash"])
    return 1
  if summary["ok"] and len(summary["results"]) < args.results:
    logger.error("FAIL: only %d of %d demo generations completed",
                 len(summary["results"]), args.results)
    return 1
  if summary["ok"]:
    logger.info("PASS: golden output matched at %.2f tok/s",
                float(selftest.get("tok_s", 0.0)))
    return 0
  logger.error("FAIL: self-test %s", json.dumps(selftest))
  return 1


if __name__ == "__main__":
  sys.exit(main())
