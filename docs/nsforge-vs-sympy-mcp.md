# NSForge vs SymPy-MCP: Feature Comparison

> **Last Updated:** 2026-01-03  
> **SymPy-MCP Version Analyzed:** Vendor snapshot (37 tools)  
> **NSForge Version:** v0.1.0+ (49 tools)

## 🎯 Core Positioning

**NSForge is NOT just a SymPy wrapper** — it's a **Derivation Assistant** that provides:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   SymPy / SymPy-MCP                    NSForge                              │
│   ════════════════                     ═══════                              │
│                                                                             │
│   「Calculation Engine」               「Knowledge Forge + Assistant」       │
│                                                                             │
│   Input: sin(x)² + cos(x)²             Input: Conversation + Thinking       │
│   Output: 1                            Output: Verified derivation          │
│                                               with semantics                │
│                                                                             │
│   ❌ Doesn't remember WHY              ✅ Records reasoning & context       │
│   ❌ No provenance                     ✅ Full derivation chain             │
│   ❌ One-time calculation              ✅ Accumulating knowledge base       │
│   ❌ Pure math symbols                 ✅ Domain semantics attached         │
│   ❌ No quality assurance              ✅ Auto-validation each step         │
│   ❌ No suggestions                    ✅ Smart recommendations             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 💡 Why NSForge? (The Real Value)

**Question:** Can't an Agent just write SymPy scripts itself?

**Answer:** Yes, but it can't do these:

| Capability | Agent + Raw SymPy | Agent + NSForge |
| ---------- | ----------------- | --------------- |
| Calculate | ✅ | ✅ |
| Add comments | ✅ | ✅ |
| Save to file | ✅ | ✅ |
| **Auto-validate each step** | ❌ | ✅ |
| **Suggest related formulas** | ❌ | ✅ |
| **Track symbol semantics** | ❌ | ✅ |
| **Detect common errors** | ❌ | ✅ |
| **Accumulate reusable knowledge** | ❌ | ✅ |

## Overview

> 📊 **完整涵蓋分析**：參見 [sympy-coverage-analysis.md](sympy-coverage-analysis.md)  
> - SymPy-MCP: 37 工具  
> - NSForge: 55 工具  
> - 整體涵蓋率: **85%**（高頻功能 100%）

NSForge builds ON TOP of SymPy-MCP, but also provides **unique capabilities** by directly leveraging SymPy modules that SymPy-MCP hasn't exposed.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Feature Layer Diagram                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                     NSForge Unique Features                       │    │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │    │
│   │  │ Statistics  │ │   Limits    │ │ Inequalities│ │ Assumptions │ │    │
│   │  │ sympy.stats │ │ sympy.limit │ │ inequalities│ │   ask/Q     │ │    │
│   │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                    NSForge Core Features                          │    │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │    │
│   │  │ Derivation  │ │ Verification│ │  Provenance │ │    Code     │ │    │
│   │  │   Engine    │ │    Suite    │ │   Tracking  │ │ Generation  │ │    │
│   │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                   SymPy-MCP (37 tools)                            │    │
│   │  Variables | Expressions | Calculus | Matrices | ODE/PDE | Units │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                      SymPy Core Library                           │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SymPy-MCP Current Tools (37 total)

### Verified List (as of 2026-01-03)

| Category | Tools |
|----------|-------|
| **Basic** | `intro`, `intro_many`, `introduce_expression`, `introduce_function`, `reset_state` |
| **Output** | `print_latex_expression`, `print_latex_tensor` |
| **Solving** | `solve_algebraically`, `solve_linear_system`, `solve_nonlinear_system` |
| **ODE/PDE** | `dsolve_ode`, `pdsolve_pde` |
| **Calculus** | `simplify_expression`, `differentiate_expression`, `integrate_expression`, `substitute_expression` |
| **Matrix** | `create_matrix`, `matrix_determinant`, `matrix_inverse`, `matrix_eigenvalues`, `matrix_eigenvectors` |
| **Vector** | `create_coordinate_system`, `create_vector_field`, `calculate_curl`, `calculate_divergence`, `calculate_gradient` |
| **Units** | `convert_to_units`, `quantity_simplify_units` |
| **Tensor/GR** | `create_predefined_metric`, `search_predefined_metrics`, `calculate_tensor`, `create_custom_metric` |

---

## ❌ Features NOT in SymPy-MCP (Verified)

These SymPy capabilities are **NOT exposed** by SymPy-MCP:

### 1. 🎲 Statistics & Probability (`sympy.stats`)

```python
from sympy.stats import Normal, Exponential, P, E, variance

X = Normal('X', mu, sigma)  # Define distribution
E(X)                         # Expected value → mu
variance(X)                  # Variance → sigma²
P(X > 0)                     # Probability calculation
```

**Applications:**
- Population pharmacokinetics (PopPK) variability analysis
- Parameter uncertainty quantification
- Confidence interval derivation

**Status in SymPy-MCP:** ❌ **Not implemented**

---

### 2. ∞ Limits & Series (`sympy.limit`, `sympy.series`, `sympy.summation`)

```python
from sympy import limit, series, summation, oo, Symbol

x = Symbol('x')
n = Symbol('n', integer=True)

limit(sin(x)/x, x, 0)           # → 1
series(exp(x), x, 0, 5)         # Taylor expansion
summation(1/n**2, (n, 1, oo))   # → π²/6
```

**Applications:**
- Steady-state approximation in PK models
- Long-term drug accumulation analysis
- Asymptotic behavior of systems

**Status in SymPy-MCP:** ❌ **Not implemented**

---

### 3. 📐 Inequality Solving (`sympy.solvers.inequalities`)

```python
from sympy.solvers.inequalities import solve_univariate_inequality
from sympy import Symbol, Interval

x = Symbol('x', real=True)
solve_univariate_inequality(x**2 - 4 < 0, x)  # → (-2, 2)
```

**Applications:**
- Therapeutic window calculation
- Safety range determination
- Dose range constraints

**Status in SymPy-MCP:** ❌ **Not implemented**

---

### 4. ✓ Assumption Queries (`sympy.assumptions.ask`, `Q`)

```python
from sympy.assumptions import ask, Q
from sympy import Symbol

x = Symbol('x', positive=True)
ask(Q.positive(x**2 + 1))      # → True
ask(Q.real(x), Q.positive(x))  # Query with assumptions
```

**Applications:**
- Automatic validation of mathematical constraints
- Physical meaning verification
- Derivation sanity checks

**Status in SymPy-MCP:** ❌ **Not implemented**

---

### 5. 📊 Uncertainty Propagation (via symbolic differentiation)

```python
from sympy import symbols, sqrt, diff

x, y, sigma_x, sigma_y = symbols('x y sigma_x sigma_y', positive=True)
f = x**2 + y**2

# Error propagation formula
sigma_f = sqrt((diff(f, x) * sigma_x)**2 + (diff(f, y) * sigma_y)**2)
```

**Applications:**
- Parameter uncertainty analysis
- Measurement error propagation
- Sensitivity analysis

**Status in SymPy-MCP:** ⚠️ **Partially possible** (needs manual assembly)

---

## Verification Method

The absence of these features was verified by:

```powershell
# Search for module imports
Select-String -Path "vendor/sympy-mcp/server.py" -Pattern "sympy\.stats|sympy\.assumptions|limit|series|summation|inequality"
# Result: 0 matches

# Verify SymPy has these modules
uv run python -c "from sympy.stats import Normal; from sympy import limit, series; from sympy.solvers.inequalities import solve_univariate_inequality; from sympy.assumptions import ask, Q; print('All exist!')"
# Result: All exist!
```

---

## NSForge Implementation Strategy

### ✅ Recommended: Direct SymPy Integration

NSForge will implement these features by **directly calling SymPy**, NOT by modifying SymPy-MCP:

```text
┌─────────────────────────────────────────────────────────────────┐
│                   NSForge Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   nsforge_mcp/tools/                                            │
│   ├── derivation.py      # Uses SymPy-MCP for basic ops         │
│   ├── verify.py          # Uses SymPy-MCP + direct SymPy        │
│   ├── stats.py           # 🆕 Direct sympy.stats               │
│   ├── limits.py          # 🆕 Direct sympy.limit/series        │
│   └── inequalities.py    # 🆕 Direct sympy.solvers.inequalities│
│                                                                 │
│   nsforge/infrastructure/                                       │
│   └── sympy_engine.py    # Direct SymPy calls (no MCP)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why NOT Fork SymPy-MCP?

| Approach | Pros | Cons |
|----------|------|------|
| **Fork SymPy-MCP** | Full control | Maintenance burden, sync issues, community split |
| **Modify vendor/** | Quick | Upgrade conflicts, violates vendor principles |
| **✅ Direct SymPy** | Independent, no conflicts | Need to implement MCP tools ourselves |

---

## Roadmap

See [ROADMAP.md](../ROADMAP.md) for implementation timeline:

- **v0.2.0**: Statistics, Limits/Series, Inequalities, Assumptions
- **v0.3.0**: Multi-language code generation, NONMEM/Monolix output

---

## Summary Table

| Feature | SymPy Module | SymPy-MCP | NSForge |
|---------|--------------|-----------|---------|
| Variables & Expressions | `sympy.core` | ✅ | Uses SymPy-MCP |
| Calculus | `sympy.diff/integrate` | ✅ | Uses SymPy-MCP |
| ODE/PDE Solving | `sympy.dsolve/pdsolve` | ✅ | Uses SymPy-MCP |
| Matrix Operations | `sympy.Matrix` | ✅ | Uses SymPy-MCP |
| Unit Conversion | `sympy.physics.units` | ✅ | Uses SymPy-MCP |
| **Statistics** | `sympy.stats` | ❌ | ✅ **Implemented** |
| **Limits** | `sympy.limit` | ❌ | ✅ **Implemented** |
| **Series Expansion** | `sympy.series` | ❌ | ✅ **Implemented** |
| **Infinite Sums** | `sympy.summation` | ❌ | ✅ **Implemented** |
| **Inequalities** | `sympy.solvers.inequalities` | ❌ | ✅ **Implemented** |
| **Assumption Queries** | `sympy.assumptions` | ❌ | ✅ **Implemented** |
| Derivation Workflow | - | ❌ | ✅ Core feature |
| Provenance Tracking | - | ❌ | ✅ Core feature |
| Verification Suite | - | ❌ | ✅ Core feature |

---

## 🔍 完整涵蓋分析

詳見 [sympy-coverage-analysis.md](sympy-coverage-analysis.md)，包含：
- ✅ 功能遺漏檢查（發現 6 類，4 類低優先度）
- ✅ 重複功能分析（12 個無衝突）
- ✅ 錯誤描述檢查（0 錯誤）
- ✅ 核心模組覆蓋率（85%，高頻 100%）

---

*NSForge — Extending SymPy-MCP with domain-specific capabilities*
