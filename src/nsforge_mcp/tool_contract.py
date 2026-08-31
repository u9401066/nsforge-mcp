"""Central MCP tool catalog, profile membership, and discovery metadata.

The registry in this module is intentionally dependency-free.  Runtime tool
registration, the capability-manifest generator, profile selection, and contract
tests all consume the same :class:`ToolSpec` objects.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Literal

MCP_PROTOCOL_REVISION = "2026-07-28"
MCP_SDK_REQUIREMENT = "==2.1.1"
MCP_TRANSPORTS = ("stdio", "streamable-http")

NSFORGE_ICON_URL = (
    "https://raw.githubusercontent.com/u9401066/nsforge-mcp/master/docs/images/nsforge-hero.svg"
)

RESOURCE_URIS = (
    "nsforge://manifest",
    "nsforge://health",
    "nsforge://north-star",
    "nsforge://derivations/{result_id}",
    "nsforge://sessions/{session_id}",
    "nsforge://runs/{run_id}",
    "nsforge://runs/{run_id}/events",
    "nsforge://artifacts/{sha256}",
)
PROMPT_NAMES = ("forge_verified_derivation",)

type ToolProfile = Literal["legacy", "workflow", "scientific", "interactive", "full"]
TOOL_PROFILES: tuple[ToolProfile, ...] = (
    "legacy",
    "workflow",
    "scientific",
    "interactive",
    "full",
)
STRICT_TOOL_PROFILES: frozenset[ToolProfile] = frozenset({"workflow", "scientific", "interactive"})

_MODULE_TOOL_NAMES: dict[str, tuple[str, ...]] = {
    "calculate": (
        "calculate_limit",
        "calculate_series",
        "calculate_summation",
        "define_distribution",
        "distribution_probability",
        "distribution_stats",
        "evaluate_numeric",
        "query_assumptions",
        "refine_expression",
        "solve_inequality",
        "solve_inequality_system",
        "symbolic_equal",
    ),
    "codegen": (
        "generate_derivation_report",
        "generate_latex_derivation",
        "generate_python_function",
        "generate_sympy_script",
    ),
    "derivation": (
        "derivation_abort",
        "derivation_add_note",
        "derivation_complete",
        "derivation_delete_saved",
        "derivation_delete_step",
        "derivation_differentiate",
        "derivation_export_for_sympy",
        "derivation_get_saved",
        "derivation_get_step",
        "derivation_get_steps",
        "derivation_handoff_status",
        "derivation_import_from_sympy",
        "derivation_insert_note",
        "derivation_integrate",
        "derivation_list_saved",
        "derivation_list_sessions",
        "derivation_load_formula",
        "derivation_prepare_for_optimization",
        "derivation_record_step",
        "derivation_repository_stats",
        "derivation_resume",
        "derivation_rollback",
        "derivation_search_saved",
        "derivation_show",
        "derivation_simplify",
        "derivation_solve_for",
        "derivation_start",
        "derivation_status",
        "derivation_substitute",
        "derivation_update_saved",
        "derivation_update_step",
    ),
    "expression": ("extract_symbols", "parse_expression", "validate_expression"),
    "formula": (
        "formula_categories",
        "formula_constants",
        "formula_get",
        "formula_kinetic_laws",
        "formula_pk_models",
        "formula_search",
    ),
    "meta": ("nsforge_health", "nsforge_manifest"),
    "music": (
        "music_compose_chord",
        "music_compose_sequence",
        "music_compose_tone",
        "music_function_info",
        "music_function_to_waveform",
        "music_generate_wav",
        "music_note_to_frequency",
        "music_plot_spectrum",
        "music_plot_waveform",
    ),
    "simplify": (
        "apart_expression",
        "cancel_expression",
        "collect_expression",
        "combsimp_expression",
        "expand_expression",
        "factor_expression",
        "fourier_transform_expression",
        "inverse_fourier_transform_expression",
        "inverse_laplace_transform_expression",
        "laplace_transform_expression",
        "powsimp_expression",
        "radsimp_expression",
        "together_expression",
        "trigsimp_expression",
    ),
    "suggest": ("derivation_suggest_next",),
    "task": ("task_explore", "task_plan", "task_run"),
    "verify": (
        "check_dimensions",
        "reverse_verify",
        "verify_derivative",
        "verify_equality",
        "verify_integral",
        "verify_solution",
    ),
}

_MUSIC_TOOLS = frozenset(_MODULE_TOOL_NAMES["music"])
_ALL_TOOL_NAMES = frozenset(name for names in _MODULE_TOOL_NAMES.values() for name in names)
_LEGACY_TOOL_NAMES = _ALL_TOOL_NAMES - _MUSIC_TOOLS

# The recommended compact workflow keeps deterministic actions granular while
# moving health, manifest, saved-result reads, and snapshots to MCP resources.
_WORKFLOW_TOOL_NAMES = frozenset(
    {
        "task_plan",
        "task_run",
        "task_explore",
        "parse_expression",
        "calculate_limit",
        "verify_equality",
        "check_dimensions",
        "derivation_start",
        "derivation_load_formula",
        "derivation_substitute",
        "derivation_simplify",
        "derivation_solve_for",
        "derivation_differentiate",
        "derivation_integrate",
        "derivation_record_step",
        "derivation_complete",
        "derivation_abort",
    }
)
_SCIENTIFIC_TOOL_NAMES = frozenset(
    name
    for module in ("calculate", "simplify", "verify", "expression")
    for name in _MODULE_TOOL_NAMES[module]
)

# Interactive adds state-changing edit/handoff operations, but intentionally
# omits pure read aliases that have a resource counterpart in the compact API.
_INTERACTIVE_EXTRA_NAMES = frozenset(
    {
        "derivation_add_note",
        "derivation_delete_saved",
        "derivation_delete_step",
        "derivation_export_for_sympy",
        "derivation_import_from_sympy",
        "derivation_insert_note",
        "derivation_prepare_for_optimization",
        "derivation_resume",
        "derivation_rollback",
        "derivation_update_saved",
        "derivation_update_step",
        "extract_symbols",
        "validate_expression",
        "verify_derivative",
        "verify_integral",
        "verify_solution",
        "reverse_verify",
        "derivation_suggest_next",
    }
)
_INTERACTIVE_TOOL_NAMES = _WORKFLOW_TOOL_NAMES | _INTERACTIVE_EXTRA_NAMES

_PROFILE_BASE_NAMES: dict[ToolProfile, frozenset[str]] = {
    "legacy": _LEGACY_TOOL_NAMES,
    "workflow": _WORKFLOW_TOOL_NAMES,
    "scientific": _SCIENTIFIC_TOOL_NAMES,
    "interactive": _INTERACTIVE_TOOL_NAMES,
    "full": _ALL_TOOL_NAMES,
}

# Calls that change an in-memory session, the saved-derivation repository, or
# an explicitly requested output file.  All other known calls are observational.
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
_IDEMPOTENT_WRITES = frozenset(
    {
        "derivation_delete_saved",
        "music_generate_wav",
        "music_plot_spectrum",
        "music_plot_waveform",
    }
)
_OPEN_WORLD_TOOLS = frozenset(
    {"formula_get", "formula_kinetic_laws", "formula_pk_models", "formula_search"}
)

_DEPRECATED_REPLACEMENTS: dict[str, str] = {"symbolic_equal": "verify_equality"}

_STRICT_ENUMS: dict[str, dict[str, tuple[str, ...]]] = {
    "calculate_limit": {"direction": ("+-", "", "+", "-")},
    "calculate_series": {"series_type": ("taylor", "laurent", "fourier")},
    "derivation_add_note": {
        "note_type": (
            "assumption",
            "limitation",
            "observation",
            "correction",
            "clinical",
            "physical",
        )
    },
    "derivation_record_step": {
        "source": ("sympy_mcp", "manual", "literature"),
        "operation_type": (
            "substitute",
            "simplify",
            "solve",
            "differentiate",
            "integrate",
            "custom",
        ),
    },
    "derivation_simplify": {"method": ("auto", "trig", "radical", "expand_then_simplify")},
    "powsimp_expression": {"combine": ("all", "base", "exp")},
    "query_assumptions": {
        "query": (
            "positive",
            "negative",
            "nonnegative",
            "nonpositive",
            "real",
            "imaginary",
            "complex",
            "integer",
            "rational",
            "irrational",
            "even",
            "odd",
            "prime",
            "finite",
            "infinite",
            "zero",
            "nonzero",
        )
    },
    "reverse_verify": {"operation": ("differentiate", "integrate", "solve")},
    "solve_inequality": {"domain": ("real", "positive", "integer")},
    "trigsimp_expression": {"method": ("matching", "groebner", "combined")},
}


@dataclass(frozen=True, slots=True)
class NumericConstraint:
    """A compact-profile numeric range enforced before SDK coercion."""

    field: str
    minimum: float | None = None
    maximum: float | None = None
    exclusive_minimum: bool = False

    def manifest_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"field": self.field}
        if self.minimum is not None:
            key = "exclusiveMinimum" if self.exclusive_minimum else "minimum"
            result[key] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        return result


_STRICT_NUMERIC: dict[str, tuple[NumericConstraint, ...]] = {
    "calculate_series": (NumericConstraint("order", minimum=1, maximum=100),),
    "derivation_add_note": (NumericConstraint("related_step", minimum=1),),
    "derivation_delete_step": (NumericConstraint("step_number", minimum=1),),
    "derivation_differentiate": (NumericConstraint("order", minimum=1, maximum=100),),
    "derivation_get_step": (NumericConstraint("step_number", minimum=1),),
    "derivation_insert_note": (NumericConstraint("after_step", minimum=0),),
    "derivation_rollback": (NumericConstraint("to_step", minimum=0),),
    "derivation_update_step": (NumericConstraint("step_number", minimum=1),),
    "distribution_stats": (),
    "evaluate_numeric": (NumericConstraint("precision", minimum=1, maximum=100),),
    "formula_pk_models": (NumericConstraint("limit", minimum=1, maximum=100),),
    "formula_search": (NumericConstraint("limit", minimum=1, maximum=100),),
    "music_compose_sequence": (
        NumericConstraint("default_duration", minimum=0, maximum=3600, exclusive_minimum=True),
    ),
    "music_compose_tone": (
        NumericConstraint("frequency", minimum=0, maximum=200_000, exclusive_minimum=True),
        NumericConstraint("amplitude", minimum=0, maximum=1),
        NumericConstraint("duration", minimum=0, maximum=3600, exclusive_minimum=True),
    ),
    "music_function_to_waveform": (
        NumericConstraint("duration", minimum=0, maximum=3600, exclusive_minimum=True),
        NumericConstraint("sample_rate", minimum=1_000, maximum=384_000),
    ),
    "music_generate_wav": (
        NumericConstraint("duration", minimum=0, maximum=3600, exclusive_minimum=True),
        NumericConstraint("sample_rate", minimum=1_000, maximum=384_000),
        NumericConstraint("amplitude_scale", minimum=0, maximum=1),
    ),
    "music_note_to_frequency": (
        NumericConstraint("a4_freq", minimum=0, maximum=200_000, exclusive_minimum=True),
    ),
    "music_plot_spectrum": (
        NumericConstraint("duration", minimum=0, maximum=3600, exclusive_minimum=True),
        NumericConstraint("sample_rate", minimum=1_000, maximum=384_000),
        NumericConstraint("max_freq", minimum=0, maximum=200_000, exclusive_minimum=True),
    ),
    "music_plot_waveform": (
        NumericConstraint("duration", minimum=0, maximum=3600, exclusive_minimum=True),
        NumericConstraint("sample_rate", minimum=1_000, maximum=384_000),
    ),
    "radsimp_expression": (NumericConstraint("max_terms", minimum=1, maximum=100),),
    "task_explore": (
        NumericConstraint("timeout_s", minimum=0, maximum=86_400, exclusive_minimum=True),
    ),
    "task_run": (
        NumericConstraint("timeout_s", minimum=0, maximum=86_400, exclusive_minimum=True),
    ),
}

_DISPLAY_WORDS = {
    "nsforge": "NSForge",
    "pk": "PK",
    "wav": "WAV",
    "sympy": "SymPy",
    "latex": "LaTeX",
}

_INPUT_DESCRIPTIONS_BY_FIELD: dict[str, str] = {
    "acceptance": "Acceptance-oracle definitions that the completed derivation must satisfy.",
    "assumptions": "Explicit symbolic or domain assumptions used by this operation.",
    "author": "Human-readable author or agent attribution for the derivation session.",
    "auto_save": "Whether to persist the completed derivation automatically.",
    "clinical_context": "Optional clinical context recorded with the derivation result.",
    "description": "Human-readable rationale or context for this operation.",
    "direction": "One-sided or two-sided direction used to approach the limit point.",
    "expression": "Symbolic expression to parse, transform, calculate, or record.",
    "expression1": "First symbolic expression in the equality comparison.",
    "expression2": "Second symbolic expression in the equality comparison.",
    "formula": "Formula expression to load into the active derivation.",
    "formula_id": "Stable formula identifier when loading a catalog formula.",
    "in_formula": "Optional formula expression on which to perform the substitution.",
    "latex": "Optional LaTeX rendering supplied for the recorded expression.",
    "limitations": "Known limitations that qualify this derivation operation.",
    "lower": "Optional lower integration bound as a symbolic expression.",
    "method": "Named deterministic method used for this transformation.",
    "name": "Stable human-readable name for the new derivation session.",
    "notes": "Additional provenance notes recorded with this operation.",
    "operation_type": "Declared operation category for a manually recorded step.",
    "order": "Positive integer order of the requested derivative or series.",
    "point": "Symbolic point at which the limit is evaluated.",
    "references": "Source references recorded with the completed derivation.",
    "replacement": "Symbolic expression that replaces the selected variable.",
    "session_id": "Target derivation-session identifier; omit only when using local active state.",
    "set_as_current": "Whether the recorded expression becomes the session's current expression.",
    "source": "Declared provenance source category for the formula or step.",
    "source_detail": "Human-readable details that identify the formula source.",
    "spec": "Strict Derivation Task Spec defining inputs, transformations, and acceptance checks.",
    "symbol_hints": "Optional symbol metadata used to disambiguate expression parsing.",
    "tags": "Searchable labels attached to the completed derivation.",
    "timeout_s": "Positive wall-clock timeout in seconds, capped at 86400.",
    "units_map": "Mapping from symbol names to declared physical units.",
    "upper": "Optional upper integration bound as a symbolic expression.",
    "variable": "Symbolic variable targeted by this operation.",
}


def strict_input_description(tool_name: str, field: str) -> str:
    """Return a non-empty compact-profile description for one input field."""
    known = _INPUT_DESCRIPTIONS_BY_FIELD.get(field)
    if known is not None:
        return known
    readable = field.replace("_", " ")
    return f"{readable.capitalize()} input for {_title(tool_name)}."


def strict_task_spec_schema() -> dict[str, Any]:
    """Return the closed, resource-safe DTS schema advertised by compact profiles."""
    modification = {
        "type": "object",
        "description": "One named symbolic modification or alternative branch.",
        "additionalProperties": False,
        "required": ["id"],
        "properties": {
            "id": {
                "type": "string",
                "minLength": 1,
                "description": "Stable identifier for this modification.",
            },
            "description": {
                "type": "string",
                "description": "Human-readable purpose of the modification.",
            },
            "expression": {
                "type": "string",
                "description": "Symbolic term introduced by the modification.",
            },
            "target": {
                "type": "string",
                "description": "Symbol replaced by the modification, when applicable.",
            },
        },
    }
    acceptance = {
        "type": "object",
        "description": "One deterministic acceptance oracle.",
        "additionalProperties": False,
        "required": ["kind"],
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["dimensional", "boundary", "limit", "equivalence"],
                "description": "Deterministic acceptance-oracle category.",
            },
            "description": {
                "type": "string",
                "description": "Human-readable expectation checked by this oracle.",
            },
            "params": {
                "type": "object",
                "description": "Oracle-specific parameters; keys depend on the selected kind.",
                "additionalProperties": True,
            },
        },
    }

    def string_array(description: str) -> dict[str, object]:
        return {
            "type": "array",
            "description": description,
            "items": {"type": "string"},
        }

    return {
        "type": "object",
        "title": "Derivation Task Spec",
        "description": "Closed declarative specification for one provenance-tracked derivation.",
        "additionalProperties": False,
        "required": ["name", "goal", "unknowns", "base_formulas"],
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "description": "Stable name for this derivation task.",
            },
            "goal": {
                "type": "string",
                "minLength": 1,
                "description": "Human-readable result the derivation must produce.",
            },
            "given": {
                "type": "object",
                "description": "Mapping from known symbols to units or semantic descriptions.",
                "additionalProperties": {"type": "string"},
            },
            "unknowns": {
                **string_array("Symbols the derivation must solve for."),
                "minItems": 1,
            },
            "assumptions": string_array("Explicit symbolic or domain assumptions."),
            "base_formulas": {
                **string_array("Formula identifiers or expressions used as starting evidence."),
                "minItems": 1,
            },
            "modifications": {
                "type": "array",
                "description": "Ordered symbolic modifications applied to the base formulas.",
                "items": modification,
            },
            "alternatives": {
                "type": "array",
                "description": "Alternative modification branches explored after a failed check.",
                "items": modification,
            },
            "acceptance": {
                "type": "array",
                "description": "Deterministic checks required before accepting the result.",
                "items": acceptance,
            },
            "metadata": {
                "type": "object",
                "description": "Caller metadata retained as untrusted contextual information.",
                "additionalProperties": True,
            },
        },
    }


def common_outcome_schema() -> dict[str, Any]:
    """Return additive common result fields for compact-profile discovery."""
    return {
        "type": "object",
        "description": "NSForge outcome envelope; tool-specific legacy fields may also appear.",
        "additionalProperties": True,
        "properties": {
            "success": {
                "type": "boolean",
                "description": "Whether the tool executed successfully.",
            },
            "execution_status": {
                "type": "string",
                "description": "Lifecycle status of the execution or persisted run.",
            },
            "verification_status": {
                "type": "string",
                "description": "Deterministic verification state for the result.",
            },
            "run_id": {
                "type": "string",
                "description": "Identifier of the immutable run that produced this result.",
            },
            "correlation_id": {
                "type": "string",
                "description": "Identifier used to correlate the run and its phase events.",
            },
            "resources": {
                "type": "array",
                "description": "Canonical MCP resources created or updated by the operation.",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "name": {"type": "string"},
                        "uri": {"type": "string"},
                        "description": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer", "minimum": 0},
                    },
                },
            },
            "error": {
                "description": "Structured or human-readable execution failure.",
                "anyOf": [
                    {"type": "string"},
                    {"type": "object", "additionalProperties": True},
                ],
            },
        },
    }


def validate_strict_task_spec(value: Any) -> list[dict[str, str]]:
    """Validate a compact-profile DTS before SDK coercion or domain construction."""
    issues: list[dict[str, str]] = []

    def issue(path: str, message: str) -> None:
        issues.append({"path": path, "message": message})

    if not isinstance(value, dict):
        issue("spec", "must be an object")
        return issues

    allowed = {
        "name",
        "goal",
        "given",
        "unknowns",
        "assumptions",
        "base_formulas",
        "modifications",
        "alternatives",
        "acceptance",
        "metadata",
    }
    for field in sorted(set(value) - allowed):
        issue(f"spec.{field}", "unknown field")
    for field in ("name", "goal"):
        field_value = value.get(field)
        if not isinstance(field_value, str) or not field_value.strip():
            issue(f"spec.{field}", "must be a non-empty string")
    for field in ("unknowns", "base_formulas"):
        field_value = value.get(field)
        if not isinstance(field_value, list) or not field_value:
            issue(f"spec.{field}", "must be a non-empty array of strings")
        elif any(not isinstance(item, str) for item in field_value):
            issue(f"spec.{field}", "must contain only strings")
    for field in ("assumptions",):
        field_value = value.get(field, [])
        if not isinstance(field_value, list) or any(
            not isinstance(item, str) for item in field_value
        ):
            issue(f"spec.{field}", "must be an array of strings")
    given = value.get("given", {})
    if not isinstance(given, dict) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in given.items()
    ):
        issue("spec.given", "must be an object with string values")

    modification_fields = {"id", "description", "expression", "target"}
    for collection in ("modifications", "alternatives"):
        entries = value.get(collection, [])
        if not isinstance(entries, list):
            issue(f"spec.{collection}", "must be an array")
            continue
        for index, entry in enumerate(entries):
            path = f"spec.{collection}[{index}]"
            if not isinstance(entry, dict):
                issue(path, "must be an object")
                continue
            for field in sorted(set(entry) - modification_fields):
                issue(f"{path}.{field}", "unknown field")
            if not isinstance(entry.get("id"), str) or not entry["id"].strip():
                issue(f"{path}.id", "must be a non-empty string")
            for field in modification_fields - {"id"}:
                if field in entry and not isinstance(entry[field], str):
                    issue(f"{path}.{field}", "must be a string")

    acceptance = value.get("acceptance", [])
    if not isinstance(acceptance, list):
        issue("spec.acceptance", "must be an array")
    else:
        acceptance_fields = {"kind", "description", "params"}
        acceptance_kinds = {"dimensional", "boundary", "limit", "equivalence"}
        for index, entry in enumerate(acceptance):
            path = f"spec.acceptance[{index}]"
            if not isinstance(entry, dict):
                issue(path, "must be an object")
                continue
            for field in sorted(set(entry) - acceptance_fields):
                issue(f"{path}.{field}", "unknown field")
            if entry.get("kind") not in acceptance_kinds:
                issue(f"{path}.kind", "must be a supported acceptance kind")
            if "description" in entry and not isinstance(entry["description"], str):
                issue(f"{path}.description", "must be a string")
            if "params" in entry and not isinstance(entry["params"], dict):
                issue(f"{path}.params", "must be an object")

    metadata = value.get("metadata", {})
    if not isinstance(metadata, dict):
        issue("spec.metadata", "must be an object")
    return issues


def _title(name: str) -> str:
    return " ".join(_DISPLAY_WORDS.get(word, word.capitalize()) for word in name.split("_"))


def _concise_description(name: str, module: str) -> str:
    title = _title(name)
    if module == "task":
        return f"{title} through the provenance-tracked reification workflow."
    if module == "derivation":
        return f"{title} on a stateful derivation; pass session_id for multi-client use."
    if module == "verify":
        return (
            f"{title} deterministically; a negative mathematical result is not an execution error."
        )
    if module in {"calculate", "simplify", "expression"}:
        return f"{title} deterministically without mutating derivation-session state."
    if module == "suggest":
        return (
            "Rank caller-supplied next-step candidates without promoting them to trusted evidence."
        )
    if module == "formula":
        return f"{title} from declared scientific sources; retrieved formulas still require verification."
    if module == "codegen":
        return f"Legacy caller-attested {title}; prefer verified artifact-based code generation."
    if module == "music":
        return f"{title} using the optional symbolic-audio tool set."
    return f"{title} runtime compatibility alias; compact profiles prefer MCP resources."


def _provenance_mode(name: str, module: str) -> str:
    if module == "codegen":
        return "caller-attested"
    if name in {"task_run", "task_explore"}:
        return "deterministic-ledger"
    if module == "derivation":
        return "session-ledger"
    if module == "formula":
        return "external-source"
    if module == "meta":
        return "runtime"
    return "deterministic"


@dataclass(frozen=True, slots=True)
class ToolContract:
    """Stable standard MCP discovery metadata for one tool."""

    title: str
    module: str
    read_only_hint: bool
    destructive_hint: bool
    idempotent_hint: bool
    open_world_hint: bool

    def annotations_dict(self) -> dict[str, bool | str]:
        return {
            "title": self.title,
            "readOnlyHint": self.read_only_hint,
            "destructiveHint": self.destructive_hint,
            "idempotentHint": self.idempotent_hint,
            "openWorldHint": self.open_world_hint,
        }


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Single source of truth for one catalog tool."""

    name: str
    module: str
    description: str
    contract: ToolContract
    profiles: frozenset[ToolProfile]
    provenance_mode: str
    deprecated: bool = False
    replacement: str | None = None
    strict_enums: tuple[tuple[str, tuple[str, ...]], ...] = ()
    strict_numeric: tuple[NumericConstraint, ...] = ()

    def manifest_dict(self) -> dict[str, object]:
        return {
            **asdict(self.contract),
            "annotations": self.contract.annotations_dict(),
            "profiles": sorted(self.profiles),
            "deprecated": self.deprecated,
            "replacement": self.replacement,
            "provenance_mode": self.provenance_mode,
            "strict_unknown_fields": bool(self.profiles & STRICT_TOOL_PROFILES),
            "strict_enums": {name: list(values) for name, values in self.strict_enums},
            "strict_numeric": [rule.manifest_dict() for rule in self.strict_numeric],
            "structured_output": True,
            "meta": tool_meta(self.module),
        }

    def runtime_meta(self, profile: ToolProfile) -> dict[str, object]:
        """Return additive compact-profile metadata; compatibility profiles stay byte-stable."""
        meta = tool_meta(self.module)
        if profile not in STRICT_TOOL_PROFILES:
            return meta
        meta.update(
            {
                "org.nsforge/profile": profile,
                "org.nsforge/provenanceMode": self.provenance_mode,
                "org.nsforge/deprecated": self.deprecated,
            }
        )
        if self.replacement is not None:
            meta["org.nsforge/replacedBy"] = self.replacement
        return meta


def _profiles_for(name: str) -> frozenset[ToolProfile]:
    return frozenset(profile for profile, names in _PROFILE_BASE_NAMES.items() if name in names)


def _build_specs() -> dict[str, ToolSpec]:
    specs: dict[str, ToolSpec] = {}
    for module, names in _MODULE_TOOL_NAMES.items():
        for name in names:
            read_only = name not in _MUTATING_TOOLS
            contract = ToolContract(
                title=_title(name),
                module=module,
                read_only_hint=read_only,
                destructive_hint=name in _DESTRUCTIVE_TOOLS,
                idempotent_hint=read_only or name in _IDEMPOTENT_WRITES,
                open_world_hint=name in _OPEN_WORLD_TOOLS,
            )
            replacement = _DEPRECATED_REPLACEMENTS.get(name)
            specs[name] = ToolSpec(
                name=name,
                module=module,
                description=_concise_description(name, module),
                contract=contract,
                profiles=_profiles_for(name),
                provenance_mode=_provenance_mode(name, module),
                deprecated=replacement is not None,
                replacement=replacement,
                strict_enums=tuple(
                    (field, values) for field, values in _STRICT_ENUMS.get(name, {}).items()
                ),
                strict_numeric=_STRICT_NUMERIC.get(name, ()),
            )
    return specs


TOOL_SPECS = MappingProxyType(_build_specs())
KNOWN_TOOL_NAMES = frozenset(TOOL_SPECS)


def _validate_registry() -> None:
    if len(TOOL_SPECS) != 91:
        raise RuntimeError(f"ToolSpec registry must contain 91 tools, got {len(TOOL_SPECS)}")
    if len(_PROFILE_BASE_NAMES["legacy"]) != 82 or len(_PROFILE_BASE_NAMES["full"]) != 91:
        raise RuntimeError("legacy/full ToolSpec profiles must remain exactly 82/91 tools")
    if not 15 <= len(_PROFILE_BASE_NAMES["workflow"]) <= 20:
        raise RuntimeError("workflow profile must remain a compact 15-20 tool surface")
    for spec in TOOL_SPECS.values():
        if not spec.profiles or not spec.profiles.issubset(TOOL_PROFILES):
            raise RuntimeError(f"invalid profile membership for {spec.name!r}: {spec.profiles}")
        if spec.replacement is not None and spec.replacement not in TOOL_SPECS:
            raise RuntimeError(
                f"deprecated tool {spec.name!r} has unknown replacement {spec.replacement!r}"
            )
        if spec.contract.read_only_hint and spec.contract.destructive_hint:
            raise RuntimeError(f"read-only tool {spec.name!r} cannot be destructive")


_validate_registry()


def tool_meta(module: str) -> dict[str, object]:
    """Legacy-compatible namespaced metadata safe for clients that ignore it."""
    return {
        "org.nsforge/module": module,
        "org.nsforge/protocolRevision": MCP_PROTOCOL_REVISION,
        "org.nsforge/responseEnvelope": "v1-compatible",
    }


def spec_for(name: str, module: str | None = None) -> ToolSpec:
    """Return a registered spec or fail closed for an unknown/misfiled tool."""
    try:
        spec = TOOL_SPECS[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown MCP tool {name!r}; add it to TOOL_SPECS before registration"
        ) from exc
    if module is not None and spec.module != module:
        raise ValueError(
            f"MCP tool {name!r} belongs to module {spec.module!r}, not declared module {module!r}"
        )
    return spec


def contract_for(name: str, module: str) -> ToolContract:
    """Return known metadata, or conservative hints for pre-registration review."""
    spec = TOOL_SPECS.get(name)
    if spec is not None:
        if spec.module != module:
            raise ValueError(
                f"MCP tool {name!r} belongs to module {spec.module!r}, not declared module {module!r}"
            )
        return spec.contract
    return ToolContract(
        title=_title(name),
        module=module,
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    )


def profile_tool_names(
    profile: ToolProfile,
    *,
    legacy_music: bool = False,
) -> frozenset[str]:
    """Return the immutable startup surface for a validated profile."""
    if profile not in TOOL_PROFILES:
        raise ValueError(f"unknown NSForge tool profile {profile!r}")
    names = _PROFILE_BASE_NAMES[profile]
    if profile == "legacy" and legacy_music:
        return names | _MUSIC_TOOLS
    return names


def profile_manifest() -> dict[str, dict[str, object]]:
    """Return deterministic profile metadata for the capability manifest."""
    return {
        profile: {
            "tool_count": len(names),
            "tools": sorted(names),
            "strict_inputs": profile in STRICT_TOOL_PROFILES,
            "resource_first": profile in STRICT_TOOL_PROFILES,
        }
        for profile, names in _PROFILE_BASE_NAMES.items()
    }


def strict_enum_values(name: str) -> dict[str, tuple[str, ...]]:
    """Return high-risk enum constraints enforced by compact profiles."""
    return dict(spec_for(name).strict_enums)


def strict_numeric_constraints(name: str) -> tuple[NumericConstraint, ...]:
    """Return compact-profile numeric constraints for one tool."""
    return spec_for(name).strict_numeric
