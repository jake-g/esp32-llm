"""Table-driven tests for verify_board serial parsing (no hardware needed)."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_board  # pylint: disable=wrong-import-position

_PASS = 'LLM_SELFTEST {"ok":true,"golden":true,"tok_s":23.75}'
_FAIL = 'LLM_SELFTEST {"ok":false,"golden":false,"tok_s":23.75}'


class ParseTaggedLineTest(unittest.TestCase):
  """parse_tagged_line edge cases."""

  def test_cases(self) -> None:
    cases = [
        ("pass line", _PASS, True),
        ("log noise before tag", "I (123) MAIN: x " + _PASS, True),
        ("no tag", "I (123) MAIN: Loading Model", None),
        ("truncated json", 'LLM_SELFTEST {"ok":tr', None),
        ("json array not object", "LLM_SELFTEST [1,2]", None),
        ("empty payload", "LLM_SELFTEST ", None),
    ]
    for name, line, want_ok in cases:
      with self.subTest(name):
        got = verify_board.parse_tagged_line(line,
                                             verify_board.SELFTEST_PREFIX)
        if want_ok is None:
          self.assertIsNone(got)
        else:
          self.assertIsNotNone(got)
          self.assertEqual(got["ok"], want_ok)


class EvaluateTest(unittest.TestCase):
  """evaluate() verdicts over whole boot logs."""

  def test_cases(self) -> None:
    result = 'LLM_RESULT {"gen":1,"tok_s":18.33}'
    assert_line = ("assert failed: xQueueGenericSend queue.c:937 "
                   "(!( ( pvItemToQueue == ((void *)0) ) ...")
    cases = [
        ("pass with demo", ["boot", _PASS, "story", result], True, 1),
        ("fail golden", ["boot", _FAIL], False, 0),
        ("no verdict", ["boot", "I (1) MAIN: Loading Model"], False, 0),
        ("empty log", [], False, 0),
        ("results before verdict are still counted",
         [result, _PASS], True, 1),
        ("any failed verdict wins over a later pass", [_FAIL, _PASS], False,
         0),
        # Observed 2026-10-17: self-test passes, then the demo asserts and
        # the board reboot-loops; the old verifier reported PASS here.
        ("crash after pass", [_PASS, "Once upon a time,", assert_line,
                              "Rebooting...", _PASS], False, 0),
        ("crash marker before verdict is ignored",
         ["Rebooting...", _PASS, result], True, 1),
    ]
    for name, lines, want_ok, want_results in cases:
      with self.subTest(name):
        summary = verify_board.evaluate(lines)
        self.assertEqual(summary["ok"], want_ok)
        self.assertEqual(len(summary["results"]), want_results)

  def test_fail_detail_is_reported(self) -> None:
    summary = verify_board.evaluate([_FAIL])
    self.assertFalse(summary["selftest"]["golden"])


if __name__ == "__main__":
  unittest.main()
