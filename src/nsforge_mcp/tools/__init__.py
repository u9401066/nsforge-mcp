"""
NSForge MCP Tools

Tool modules for the MCP server.

Architecture:
- derivation.py: 🔥 Derivation engine (stateful sessions, provenance tracking)
- formula.py: 🌐 Formula search (Wikidata, BioModels, SciPy) - Agent's knowledge base
- expression.py: Parse and validate mathematical expressions
- calculate.py: Symbolic computation (simplify, solve, diff, integrate)
- verify.py: Verification (equality, reverse, dimensions)
- codegen.py: Generate Python code and reports from derivations
- music.py: 🎵 Music function composition, visualization, and audio generation

Design Principles:
1. Forge = CREATE new formulas through derivation (core mission!)
2. Every derivation step is recorded with full provenance
3. Sessions persist to prevent mid-derivation data loss
4. Leverage existing packages (SymPy, SciPy) - don't reinvent the wheel
5. Use SymPy for all symbolic computation
6. Generated code uses SymPy (not Agent-generated)
7. Formula search = Agent's scientific knowledge base (Wikidata, BioModels)
"""

from typing import Any

from nsforge_mcp.config import module_enabled
from nsforge_mcp.envelope import EnvelopeMCP
from nsforge_mcp.tools.calculate import register_calculate_tools
from nsforge_mcp.tools.codegen import register_codegen_tools
from nsforge_mcp.tools.derivation import register_derivation_tools
from nsforge_mcp.tools.expression import register_expression_tools
from nsforge_mcp.tools.formula import register_formula_tools
from nsforge_mcp.tools.meta import register_meta_tools
from nsforge_mcp.tools.music import register_music_tools
from nsforge_mcp.tools.simplify import register_simplify_tools
from nsforge_mcp.tools.suggest import register_suggest_tools
from nsforge_mcp.tools.task import register_task_tools
from nsforge_mcp.tools.verify import register_verify_tools


def register_all_tools(mcp: Any) -> None:
    """Register all NSForge tools with the MCP server."""
    # Wrap once so every tool gets a uniform error envelope (an unhandled exception
    # becomes a structured, logged error dict) without touching any tool body.
    mcp = EnvelopeMCP(mcp)

    # 🔥 Core: Derivation engine (the "Forge" in NSForge)
    register_derivation_tools(mcp)

    # 🌐 Formula search: Agent's scientific knowledge base
    register_formula_tools(mcp)

    # Supporting tools
    register_expression_tools(mcp)
    register_calculate_tools(mcp)
    register_simplify_tools(mcp)  # 🆕 Phase 1: Advanced simplification
    register_verify_tools(mcp)
    register_codegen_tools(mcp)

    # 🧭 L2/L3: Declarative task spec + reification-ladder orchestrator
    register_task_tools(mcp)

    # 🧭 Phase 3: Retrieval-augmented next-step suggester (ranks open-source candidates)
    register_suggest_tools(mcp)

    # 🧩 Agent harness: runtime self-description (health, manifest)
    register_meta_tools(mcp)

    # 🎵 Music: mission-tangential; opt-in via NSFORGE_ENABLE_MUSIC=1 so the default
    # surface stays lean (fewer tools => better tool selection by the model).
    if module_enabled("music"):
        register_music_tools(mcp)
