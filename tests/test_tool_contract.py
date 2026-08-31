"""Invariant checks for centralized MCP tool discovery hints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nsforge_mcp.tool_contract import (
    KNOWN_TOOL_NAMES,
    TOOL_PROFILES,
    TOOL_SPECS,
    contract_for,
    profile_manifest,
    profile_tool_names,
    spec_for,
)

MANIFEST = Path(__file__).resolve().parents[1] / "docs" / "agent" / "capabilities.json"


def _tools() -> list[dict[str, object]]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["tools"]


def test_all_catalog_tools_have_consistent_safe_annotations() -> None:
    tools = _tools()
    assert len(tools) == 91
    assert {str(tool["name"]) for tool in tools} == KNOWN_TOOL_NAMES
    for tool in tools:
        contract = contract_for(str(tool["name"]), str(tool["module"]))
        assert tool["annotations"] == contract.annotations_dict()
        assert not (contract.read_only_hint and contract.destructive_hint)
        if contract.destructive_hint:
            assert not contract.read_only_hint


def test_external_and_file_side_effect_hints_are_precise() -> None:
    assert contract_for("formula_search", "formula").open_world_hint is True
    assert contract_for("formula_get", "formula").open_world_hint is True
    assert contract_for("formula_constants", "formula").open_world_hint is False
    assert contract_for("formula_categories", "formula").open_world_hint is False

    for name in ("music_generate_wav", "music_plot_spectrum", "music_plot_waveform"):
        contract = contract_for(name, "music")
        assert contract.read_only_hint is False
        assert contract.destructive_hint is True


def test_negative_verification_remains_a_valid_read_only_result() -> None:
    contract = contract_for("verify_equality", "verify")
    assert contract.read_only_hint is True
    assert contract.idempotent_hint is True
    assert contract.destructive_hint is False


def test_unknown_future_tool_hints_fail_closed() -> None:
    contract = contract_for("future_stateful_tool", "future")
    assert contract.read_only_hint is False
    assert contract.idempotent_hint is False


def test_completion_discloses_that_auto_save_can_overwrite() -> None:
    contract = contract_for("derivation_complete", "derivation")
    assert contract.read_only_hint is False
    assert contract.destructive_hint is True


def test_toolspec_is_the_exact_profile_source_of_truth() -> None:
    assert set(TOOL_SPECS) == KNOWN_TOOL_NAMES
    assert {profile: len(profile_tool_names(profile)) for profile in TOOL_PROFILES} == {
        "legacy": 82,
        "workflow": 17,
        "scientific": 35,
        "interactive": 35,
        "full": 91,
    }
    assert profile_manifest()["workflow"]["strict_inputs"] is True
    assert spec_for("symbolic_equal").deprecated is True
    assert spec_for("symbolic_equal").replacement == "verify_equality"
    assert spec_for("generate_python_function").provenance_mode == "caller-attested"


def test_unknown_or_misfiled_toolspec_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown MCP tool"):
        spec_for("future_stateful_tool")
    with pytest.raises(ValueError, match="belongs to module"):
        spec_for("verify_equality", "calculate")
