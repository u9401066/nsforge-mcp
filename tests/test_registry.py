"""Test script for Formula Registry."""

from nsforge.infrastructure.formula_registry import get_registry

registry = get_registry()
stats = registry.stats()

print("=== Formula Registry Stats ===")
print(f"Total formulas: {stats['total_formulas']}")
print()
for source, info in stats['sources'].items():
    print(f"{source}:")
    print(f"  Count: {info['count']}")
    print(f"  Categories: {info['categories']}")
    print()

# Test search
print('=== Search "energy" ===')
results = registry.search('energy')
for r in results[:5]:
    print(f"  - {r.id}: {r.name}")

# Test get formula
print()
print("=== Get Newton Second Law ===")
f = registry.get('newton_second_law')
if f:
    print(f"  Expression: {f.expression}")
    print(f"  Source: {f.source}")

# Test pharmacokinetics
print()
print("=== Get One-Compartment Model ===")
f = registry.get('one_compartment_iv')
if f:
    print(f"  Expression: {f.expression}")
    print(f"  Source: {f.source}")

# Test constant
print()
print("=== Get Speed of Light ===")
f = registry.get('speed_of_light')
if f:
    var = list(f.variables.values())[0]
    print(f"  Value: {var.get('value')} {var.get('unit')}")

# Test solve
print()
print("=== Solve Newton's Law for 'a' ===")
from sympy import Eq, solve, symbols
f = registry.get('newton_second_law')
if f and isinstance(f.expression, Eq):
    # Need to use the same symbol that's in the expression
    expr = f.expression
    # Get all symbols from expression
    syms = expr.free_symbols
    print(f"  Symbols in expression: {syms}")
    a_sym = [s for s in syms if s.name == 'a'][0]
    solutions = solve(expr, a_sym)
    print(f"  a = {solutions}")
