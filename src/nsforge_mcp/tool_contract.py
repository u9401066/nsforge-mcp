"""MCP-facing metadata shared by every NSForge tool.

The tool bodies remain the source of truth for names, descriptions, inputs, and
legacy response envelopes.  This module adds protocol-level intent without
duplicating those contracts: clients can tell which calls are read-only,
destructive, idempotent, or capable of reaching outside the server.

Keep this module dependency-free.  The capability-manifest generator imports it
without booting the MCP server.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

MCP_PROTOCOL_REVISION = "2026-07-28"
MCP_SDK_REQUIREMENT = ">=2.1.1,<3"
MCP_TRANSPORTS = ("stdio", "streamable-http")

NSFORGE_ICON_URL = (
    "https://raw.githubusercontent.com/u9401066/nsforge-mcp/master/docs/images/nsforge-hero.svg"
)

RESOURCE_URIS = (
    "nsforge://manifest",
    "nsforge://health",
    "nsforge://north-star",
    "nsforge://derivations/{result_id}",
)
PROMPT_NAMES = ("forge_verified_derivation",)


@dataclass(frozen=True, slots=True)
class ToolContract:
    """Stable MCP discovery metadata for one tool."""

    title: str
    module: str
    read_only_hint: bool
    destructive_hint: bool
    idempotent_hint: bool
    open_world_hint: bool

    def annotations_dict(self) -> dict[str, bool | str]:
        """Return protocol field names used by ``ToolAnnotations`` JSON."""
        return {
            "title": self.title,
            "readOnlyHint": self.read_only_hint,
            "destructiveHint": self.destructive_hint,
            "idempotentHint": self.idempotent_hint,
            "openWorldHint": self.open_world_hint,
        }

    def manifest_dict(self) -> dict[str, object]:
        """Return deterministic metadata for the capability manifest."""
        return {
            **asdict(self),
            "annotations": self.annotations_dict(),
            "structured_output": True,
            "meta": tool_meta(self.module),
        }


# These calls change an in-memory session, the saved-derivation repository, or
# an explicitly requested output file.  Everything else is observational.
_MUTATING_TOOLS = frozenset(
    {
        "derivation_abort",
        "derivation_add_note",
        "derivation_complete",
        "derivation_delete_saved",
        "derivation_delete_step",
        "derivation_differentiate",
        "derivation_import_from_sympy",
        "derivation_insert_note",
        "derivation_integrate",
        "derivation_load_formula",
        "derivation_record_step",
        "derivation_resume",
        "derivation_rollback",
        "derivation_simplify",
        "derivation_solve_for",
        "derivation_start",
        "derivation_substitute",
        "derivation_update_saved",
        "derivation_update_step",
        "music_generate_wav",
        "music_plot_spectrum",
        "music_plot_waveform",
    }
)

# Explicit allowlist: an unfamiliar future tool fails closed as mutating and
# non-idempotent until its semantics are reviewed here.  This prevents a newly
# added write tool from silently inheriting reassuring read-only metadata.
_READ_ONLY_TOOLS = frozenset(
    {
        "apart_expression",
        "calculate_limit",
        "calculate_series",
        "calculate_summation",
        "cancel_expression",
        "check_dimensions",
        "collect_expression",
        "combsimp_expression",
        "define_distribution",
        "derivation_export_for_sympy",
        "derivation_get_saved",
        "derivation_get_step",
        "derivation_get_steps",
        "derivation_handoff_status",
        "derivation_list_saved",
        "derivation_list_sessions",
        "derivation_prepare_for_optimization",
        "derivation_repository_stats",
        "derivation_search_saved",
        "derivation_show",
        "derivation_status",
        "derivation_suggest_next",
        "distribution_probability",
        "distribution_stats",
        "evaluate_numeric",
        "expand_expression",
        "extract_symbols",
        "factor_expression",
        "formula_categories",
        "formula_constants",
        "formula_get",
        "formula_kinetic_laws",
        "formula_pk_models",
        "formula_search",
        "fourier_transform_expression",
        "generate_derivation_report",
        "generate_latex_derivation",
        "generate_python_function",
        "generate_sympy_script",
        "inverse_fourier_transform_expression",
        "inverse_laplace_transform_expression",
        "laplace_transform_expression",
        "music_compose_chord",
        "music_compose_sequence",
        "music_compose_tone",
        "music_function_info",
        "music_function_to_waveform",
        "music_note_to_frequency",
        "nsforge_health",
        "nsforge_manifest",
        "parse_expression",
        "powsimp_expression",
        "query_assumptions",
        "radsimp_expression",
        "refine_expression",
        "reverse_verify",
        "solve_inequality",
        "solve_inequality_system",
        "symbolic_equal",
        "task_explore",
        "task_plan",
        "task_run",
        "together_expression",
        "trigsimp_expression",
        "validate_expression",
        "verify_derivative",
        "verify_equality",
        "verify_integral",
        "verify_solution",
    }
)

KNOWN_TOOL_NAMES = _READ_ONLY_TOOLS | _MUTATING_TOOLS

# A true destructive hint means the call can remove or replace user-visible
# state.  Purely additive session steps are deliberately not classified here.
_DESTRUCTIVE_TOOLS = frozenset(
    {
        "derivation_abort",
        "derivation_complete",
        "derivation_delete_saved",
        "derivation_delete_step",
        "derivation_rollback",
        "derivation_update_saved",
        "derivation_update_step",
        "music_generate_wav",
        "music_plot_spectrum",
        "music_plot_waveform",
    }
)

# Repeating these writes with identical inputs converges on the same visible
# result.  Session creation/step appends intentionally remain non-idempotent.
_IDEMPOTENT_WRITES = frozenset(
    {
        "derivation_delete_saved",
        "music_generate_wav",
        "music_plot_spectrum",
        "music_plot_waveform",
    }
)

# Formula lookup can contact public scientific knowledge services.  Local file
# access and deterministic symbolic computation are not considered open-world.
_OPEN_WORLD_TOOLS = frozenset(
    {
        "formula_get",
        "formula_kinetic_laws",
        "formula_pk_models",
        "formula_search",
    }
)

_DISPLAY_WORDS = {
    "nsforge": "NSForge",
    "pk": "PK",
    "wav": "WAV",
    "sympy": "SymPy",
    "latex": "LaTeX",
}


def _title(name: str) -> str:
    return " ".join(_DISPLAY_WORDS.get(word, word.capitalize()) for word in name.split("_"))


def tool_meta(module: str) -> dict[str, object]:
    """Namespaced, additive metadata safe for clients that ignore it."""
    return {
        "org.nsforge/module": module,
        "org.nsforge/protocolRevision": MCP_PROTOCOL_REVISION,
        "org.nsforge/responseEnvelope": "v1-compatible",
    }


def contract_for(name: str, module: str) -> ToolContract:
    """Build the metadata contract for a registered tool."""
    read_only = name in _READ_ONLY_TOOLS
    return ToolContract(
        title=_title(name),
        module=module,
        read_only_hint=read_only,
        destructive_hint=name in _DESTRUCTIVE_TOOLS,
        idempotent_hint=read_only or name in _IDEMPOTENT_WRITES,
        open_world_hint=name in _OPEN_WORLD_TOOLS,
    )
