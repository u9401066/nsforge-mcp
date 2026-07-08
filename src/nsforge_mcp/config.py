"""Runtime configuration for the NSForge MCP server.

Some tool modules are mission-tangential (a demo of the symbolic core rather than
part of the derivation forge). They are **opt-in**, so the default surface an MCP
client loads stays lean and focused — fewer tools means better tool selection by
the model. Enable one by setting ``NSFORGE_ENABLE_<MODULE>=1``, e.g.
``NSFORGE_ENABLE_MUSIC=1``.
"""

from __future__ import annotations

import os

# Tool modules registered only when explicitly enabled (kept out of the default
# production surface). Kept as a plain tuple so tooling can read it statically.
OPTIONAL_MODULES: tuple[str, ...] = ("music",)

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def module_enabled(module: str) -> bool:
    """Return whether a tool module should be registered in this process.

    Core modules are always enabled; optional ones require ``NSFORGE_ENABLE_<M>``.
    """
    if module not in OPTIONAL_MODULES:
        return True
    return os.environ.get(f"NSFORGE_ENABLE_{module.upper()}", "").strip().lower() in _TRUTHY
