"""
Untrusted-input safety guard for the symbolic parse boundary.

As a shared multi-agent service, NSForge accepts arbitrary expression strings
from many callers. ``sympify`` / ``parse_expr`` can be turned into a
denial-of-service (power towers like ``9**9**9``, huge literals, pathological
nesting) that exhausts CPU/memory and starves every other agent. This module is
a cheap first line of defence applied *before* parsing. Pure: no I/O.

The robust defence is still a hard timeout / resource cap on the symbolic
evaluation itself (process pool) — see the multi-agent refactor plan.
"""

from __future__ import annotations

import re

MAX_LENGTH = 4000  # characters
MAX_DEPTH = 100  # bracket nesting depth
MAX_DIGITS = 15  # length of a single integer literal (physical constants are < 15)
MAX_POWERS = 50  # number of ** operators

# a**b**c — chained exponentiation grows hyper-exponentially (e.g. 9**9**9).
_POWER_TOWER = re.compile(r"\*\*\s*[\w.]+\s*\*\*")
_BIG_INT = re.compile(rf"\d{{{MAX_DIGITS + 1},}}")
_BIG_FACTORIAL = re.compile(r"\d{4,}\s*!")
_OPEN = "([{"
_CLOSE = ")]}"


def check_expression_safety(text: str) -> str | None:
    """Return an error message if ``text`` is unsafe to parse, else ``None``.

    Cheap string-level heuristics that block the classic symbolic-DoS vectors
    while leaving ordinary formulas untouched.
    """
    if len(text) > MAX_LENGTH:
        return f"expression too long ({len(text)} > {MAX_LENGTH} chars)"

    depth = 0
    max_depth = 0
    for ch in text:
        if ch in _OPEN:
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch in _CLOSE:
            depth -= 1
    if max_depth > MAX_DEPTH:
        return f"expression nesting too deep ({max_depth} > {MAX_DEPTH})"

    if _POWER_TOWER.search(text):
        return "chained exponentiation (power tower) is not allowed"
    if text.count("**") > MAX_POWERS:
        return f"too many exponentiations ({text.count('**')} > {MAX_POWERS})"
    if _BIG_INT.search(text):
        return f"integer literal too large (> {MAX_DIGITS} digits)"
    if _BIG_FACTORIAL.search(text):
        return "factorial of a large literal is not allowed"

    return None
