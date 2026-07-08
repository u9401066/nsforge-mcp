"""
Provenance ledger — the north star as a structured, enforceable record.

Every entity in a derived result (a base formula, a substitution/solve step, the
final expression) must carry a "birth certificate": the tool call that produced
it. A ledger whose every entry names a tool is *complete*; code is emitted only
from a complete ledger, so nothing un-sourced (hand-derived) reaches a result.

Pure domain: no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProvenanceEntry:
    """A birth certificate: which tool call produced ``entity``."""

    entity: str  # what was produced (a formula, a step, the final expression)
    tool: str  # the tool/operation that produced it; empty string = un-sourced
    source: str = ""  # where its inputs came from (provenance of provenance)

    @property
    def is_sourced(self) -> bool:
        return bool(self.tool)


@dataclass(frozen=True)
class ProvenanceLedger:
    """The ordered chain of birth certificates for one derivation."""

    entries: tuple[ProvenanceEntry, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        """True iff there is at least one entry and every entry is tool-sourced."""
        return bool(self.entries) and all(e.is_sourced for e in self.entries)

    def unsourced(self) -> tuple[ProvenanceEntry, ...]:
        """Entries lacking a tool (a hand-derived leak); empty when complete."""
        return tuple(e for e in self.entries if not e.is_sourced)
