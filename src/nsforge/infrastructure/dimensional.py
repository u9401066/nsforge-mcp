"""
Dimensional analysis via ``sympy.physics.units`` — an infrastructure adapter.

Consolidates the SI dimensional logic that previously lived only in the MCP tool
layer, so the domain ``Verifier`` and the L3 orchestrator share one
implementation (single source of truth). Pure: no I/O.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from nsforge.infrastructure.parsing import parse_expression_safe


def _unit_map() -> dict[str, Any]:
    """Map common unit symbols to ``sympy.physics.units`` quantities."""
    from sympy.physics import units as u

    return {
        "m": u.meter,
        "kg": u.kilogram,
        "g": u.gram,
        "s": u.second,
        "A": u.ampere,
        "K": u.kelvin,
        "mol": u.mole,
        "cd": u.candela,
        "N": u.newton,
        "J": u.joule,
        "W": u.watt,
        "Pa": u.pascal,
        "C": u.coulomb,
        "V": u.volt,
        "Hz": u.hertz,
        "rad": u.radian,
        "L": u.liter,
        "min": u.minute,
        "h": u.hour,
    }


def dimension_of(expression: str, units_map: dict[str, str]) -> tuple[str | None, str | None]:
    """Return ``(SI dimensional expression string, error)``.

    Substitutes each symbol's unit into ``expression`` and asks SymPy for the SI
    dimensional expression. Exactly one of the two return values is ``None``.
    """
    from sympy.physics.units.systems import SI

    try:
        units = _unit_map()
        expr, expression_error = parse_expression_safe(expression)
        if expression_error is not None or expr is None:
            raise ValueError(expression_error or "expression parser returned no value")
        subs: dict[Any, Any] = {}
        for name, unit_str in units_map.items():
            unit_value, unit_error = parse_expression_safe(unit_str, local_dict=units)
            if unit_error is not None or unit_value is None:
                raise ValueError(unit_error or f"invalid unit for {name}")
            subs[sp.Symbol(name)] = unit_value
        dim = SI.get_dimensional_expr(expr.subs(subs))
        return str(dim), None
    except Exception as exc:
        return None, str(exc)


def _dimensional_deps(
    expression: str, units_map: dict[str, str]
) -> tuple[dict[str, int] | None, str | None]:
    """Return ``(base-dimension exponent map, error)`` fully reduced to SI base dims.

    Reduces derived dimensions (e.g. ``force``) to base dimensions so that
    equivalent expressions compare equal (``N/kg`` == ``m/s**2`` == length/time**2).
    """
    from sympy.physics.units import Dimension
    from sympy.physics.units.systems import SI

    try:
        units = _unit_map()
        expr, expression_error = parse_expression_safe(expression)
        if expression_error is not None or expr is None:
            raise ValueError(expression_error or "expression parser returned no value")
        subs: dict[Any, Any] = {}
        for name, unit_str in units_map.items():
            unit_value, unit_error = parse_expression_safe(unit_str, local_dict=units)
            if unit_error is not None or unit_value is None:
                raise ValueError(unit_error or f"invalid unit for {name}")
            subs[sp.Symbol(name)] = unit_value
        dim_expr = SI.get_dimensional_expr(expr.subs(subs))
        deps = SI.get_dimension_system().get_dimensional_dependencies(Dimension(dim_expr))
        return {str(getattr(k, "name", k)): int(v) for k, v in deps.items()}, None
    except Exception as exc:
        return None, str(exc)


def dimensions_match(
    expression: str, units_map: dict[str, str], expected_units: str
) -> tuple[bool | None, str]:
    """Whether ``expression`` shares the SI base dimension of ``expected_units``.

    Returns ``(match, detail)``; ``match`` is ``None`` when analysis failed.
    """
    got, err = _dimensional_deps(expression, units_map)
    if err or got is None:
        return None, f"analysis failed: {err}"
    want, werr = _dimensional_deps("nsforge_quantity", {"nsforge_quantity": expected_units})
    if werr or want is None:
        return None, f"bad expected_units: {werr}"
    return got == want, f"got {got}, expected {want}"
