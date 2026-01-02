# 🔥 Neurosymbolic Forge (NSForge)

> **"Forge" = CREATE new formulas through verified derivation**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

🌐 **English** | [繁體中文](README.zh-TW.md)

## 🔨 Core Concept: The "Forge"

**NSForge is NOT a formula database** — it's a **derivation factory** that CREATES new formulas.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🔨 FORGE = Create new formulas through derivation                         │
│                                                                             │
│   Input: Base formulas          Output: NEW derived formulas                │
│   ┌─────────────────────┐       ┌─────────────────────────────────────┐    │
│   │ • One-compartment   │       │ Temperature-corrected elimination   │    │
│   │ • Arrhenius         │  ──→  │ Body fat-adjusted distribution      │    │
│   │ • Fick's law        │       │ Renal function dose adjustment      │    │
│   │ • ...               │       │ Custom PK/PD models                 │    │
│   └─────────────────────┘       └─────────────────────────────────────┘    │
│         (from sympy-mcp)                    (stored in NSForge)            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ Three Core Capabilities

| Capability | Description | Tools |
| ---------- | ----------- | ----- |
| **DERIVE** | Create new formulas by composing base formulas | `substitute`, `simplify`, `differentiate`, `integrate` |
| **VERIFY** | Ensure correctness through multiple methods | `check_dimensions`, `verify_derivative`, `symbolic_equal` |
| **STORE**  | Save derived formulas with full provenance | `formulas/derivations/` repository |

---

## � Ecosystem: Don't Reinvent the Wheel

NSForge works WITH other MCP servers, not against them:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP Formula Ecosystem                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  sympy-mcp                                                                  │
│  └── Base formulas: F=ma, PV=nRT, Arrhenius...                             │
│  └── Physical constants: c, G, h, R... (SciPy CODATA)                      │
│  └── Symbolic computation engine                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  medical-calc-mcp (75+ tools)                                               │
│  └── Clinical scores: APACHE, SOFA, GCS, MELD, qSOFA...                    │
│  └── Medical calculations: eGFR, IBW, BSA, MEWS...                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  nsforge-mcp ← YOU ARE HERE                                                 │
│  └── 🔨 Derivation framework: compose, verify, generate code               │
│  └── 📁 Derivation repository: store CREATED formulas with provenance      │
│  └── ✅ Verification layer: dimensional analysis, reverse verification     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**What NSForge stores:**

| ✅ BELONGS in NSForge | ❌ Does NOT belong (use other tools) |
| --------------------- | ------------------------------------ |
| Temperature-corrected drug elimination | Basic physics formulas (sympy-mcp) |
| Body fat-adjusted volume of distribution | Physical constants (sympy-mcp) |
| Renal function dose adjustments | Clinical scores (medical-calc-mcp) |
| Custom composite PK/PD models | Textbook formulas (references) |

---

## �🎬 Workflow

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   User Question                   NSForge Processing Pipeline              │
│   ═════════════                   ═══════════════════════════              │
│                                                                            │
│   "Drug concentration in         1️⃣ Query Formula Knowledge Base           │
│    a 38°C fever patient?"   ──→     ├─ One-compartment PK: C(t) = C₀·e^(-kₑt)
│                                     └─ Arrhenius equation: k(T) = A·e^(-Ea/RT)
│                                                                            │
│                                  2️⃣ Compose Derivation                      │
│                                     ├─ Substitute k(T) into PK model       │
│                                     └─ Obtain temperature-corrected formula│
│                                                                            │
│                                  3️⃣ Symbolic Computation (SymPy)            │
│                                     └─ C(t,T) = C₀·exp(-kₑ,ref·t·exp(...)) │
│                                                                            │
│                                  4️⃣ Verify Results                          │
│                                     ├─ T=37°C reduces to standard model ✓  │
│                                     └─ Dimensional analysis passed ✓       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Why NSForge?

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Problem: LLMs doing math directly                                         │
│   ═════════════════════════════════                                         │
│                                                                             │
│   ❌ May calculate wrong        ❌ Different results      ❌ Unverifiable   │
│      (hallucinations)              each time                                │
│                                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│   Solution: LLM + NSForge                                                   │
│   ═══════════════════════                                                   │
│                                                                             │
│   LLM handles:                      NSForge handles:                        │
│   ┌─────────────────────┐          ┌─────────────────────┐                 │
│   │ • Understand query  │          │ • Store verified    │                 │
│   │ • Plan derivation   │    ──→   │   formulas          │                 │
│   │ • Explain results   │          │ • Precise symbolic  │                 │
│   └─────────────────────┘          │   computation       │                 │
│      "Understanding                │ • Track derivation  │                 │
│       & Planning"                  │   sources           │                 │
│                                    │ • Verify results    │                 │
│                                    └─────────────────────┘                 │
│                                       "Computation                         │
│                                        & Verification"                     │
│                                                                             │
│   ✅ Guaranteed correct    ✅ Reproducible    ✅ Fully traceable            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 Derivation Repository Architecture

NSForge stores **derived formulas** with full provenance tracking:

```text
formulas/
└── derivations/                    ← All derived formulas go here
    ├── README.md                   ← Documentation
    └── pharmacokinetics/           ← PK model derivations
        ├── temp_corrected_elimination.md   ← Temperature-corrected k
        └── fat_adjusted_vd.md              ← Obesity-adjusted Vd
```

**Each derivation result contains:**

- LaTeX mathematical expression
- SymPy computable form  
- **Derived from**: which base formulas were combined
- **Derivation steps**: the actual derivation process
- **Verification status**: dimensional analysis, limiting cases
- Clinical context and usage guidance
- YAML metadata for programmatic access

**Example: Temperature-Corrected Drug Elimination**

```yaml
id: temp_corrected_elimination
name: Temperature-Corrected Drug Elimination Rate
expression: k_ref * exp((E_a / R) * (1/T_ref - 1/T))
derived_from:
  - one_compartment_model      # from sympy-mcp
  - arrhenius_equation         # from sympy-mcp
verified: true
verification_method: dimensional_analysis
```

---

## ✨ Features

| Category | Capabilities |
| ---- | ---- |
| 🔢 **Symbolic Computation** | Calculus, Algebra, Linear Algebra, ODE/PDE |
| 📖 **Formula Management** | Storage, Query, Version Control, Source Tracking |
| 🔄 **Derivation Composition** | Multi-formula composition, Variable substitution, Condition modification |
| ✅ **Result Verification** | Dimensional analysis, Boundary conditions, Reverse verification |
| 🐍 **Code Generation** | Generate Python functions from symbolic formulas |

## 📦 Installation

### Requirements

- **Python 3.12+**
- **uv** (recommended package manager)

```bash
# Using uv (recommended)
uv add nsforge-mcp

# Or using pip
pip install nsforge-mcp
```

### From Source

```bash
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# Create environment and install dependencies
uv sync --all-extras

# Verify installation
uv run python -c "import nsforge; print(nsforge.__version__)"
```

## 🚀 Quick Start

### As MCP Server

```json
// Claude Desktop config (claude_desktop_config.json)
{
  "mcpServers": {
    "nsforge": {
      "command": "uvx",
      "args": ["nsforge-mcp"]
    }
  }
}
```

### Usage Examples

**Calculus computation**:

```text
User: Calculate ∫(x² + 3x)dx and verify the result

Agent calls NSForge:
→ Result: x³/3 + 3x²/2 + C
→ Verify: d/dx(x³/3 + 3x²/2) = x² + 3x ✓
→ Steps: Split integral → Power rule → Combine
```

**Physics derivation**:

```text
User: Work done by ideal gas in isothermal expansion?

Agent calls NSForge:
→ W = nRT ln(V₂/V₁)
→ Derivation: PV=nRT → P=nRT/V → W=∫PdV → Integrate
```

**Algorithm analysis**:

```text
User: Analyze T(n) = 2T(n/2) + n

Agent calls NSForge:
→ T(n) = Θ(n log n)
→ Method: Master Theorem Case 2
→ Example: Merge Sort
```

## 📖 Documentation

### Design Documents

- [Design Evolution: Derivation Framework](docs/design-evolution-derivation-framework.md) - Architecture evolution from templates to composable derivation framework
- [Domain Planning: Audio Circuits](docs/domain-audio-circuits.md) - Audio circuits principles and modifications
- [Original Design](docs/symbolic-reasoning-mcp-design.md) - Complete architecture and API design (reference)

### Example Derivations

- [Power Amp Coupling Capacitor Design](docs/examples/power-amp-coupling-capacitor.md) - Complete RC high-pass filter derivation
  - From ideal formulas to practical considerations (output impedance, ESR, speaker impedance curve)
  - Demonstrates NSForge "Principles + Modifications" framework in practice

### API Reference

- [API Reference](docs/api.md) - MCP tool documentation (TBD)

## 🛠️ MCP Tools

| Tool | Purpose |
| ---- | ---- |
| `symbolic_calculate` | Symbolic math computation |
| `physics_formula` | Physics formula derivation |
| `chemistry_calculate` | Chemistry calculations |
| `algorithm_analyze` | Algorithm analysis |
| `verify_derivation` | Derivation verification |
| `unit_convert` | Unit conversion |

## 🏗️ Project Structure

This project uses **DDD (Domain-Driven Design)** architecture with Core and MCP separation:

```text
nsforge-mcp/
├── src/
│   ├── nsforge/               # 🔷 Core Domain (pure logic, no MCP dependency)
│   │   ├── domain/            # Domain Layer
│   │   │   ├── entities.py    #   - Entities (Expression, Derivation)
│   │   │   ├── value_objects.py #   - Value Objects (MathContext, Result)
│   │   │   └── services.py    #   - Domain service interfaces
│   │   ├── application/       # Application Layer
│   │   │   └── use_cases.py   #   - Use Cases (Calculate, Derive, Verify)
│   │   └── infrastructure/    # Infrastructure Layer
│   │       ├── sympy_engine.py #   - SymPy engine implementation
│   │       └── verifier.py    #   - Verifier implementation
│   │
│   └── nsforge_mcp/           # 🔶 MCP Layer (Presentation)
│       ├── server.py          #   - FastMCP Server
│       └── tools/             #   - MCP tool definitions
│           ├── calculate.py   #     - Calculation tools
│           ├── calculus.py    #     - Calculus tools
│           └── verify.py      #     - Verification tools
│
├── tests/                     # Tests
├── docs/                      # Documentation
└── pyproject.toml             # Project config (uv/hatch)
```

### Architecture Benefits

- **Core independently testable**: No MCP dependency, can use `nsforge` package standalone
- **MCP replaceable**: Can support other protocols (REST, gRPC) in the future
- **Dependency Inversion**: Domain defines interfaces, Infrastructure implements

## 🧪 Development

```bash
# Clone
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# Create environment (uv will automatically use Python 3.12+)
uv sync --all-extras

# Run tests
uv run pytest

# Code checks
uv run ruff check src/
uv run mypy src/

# Start dev server
uv run nsforge-mcp
```

## 📋 Roadmap

- [x] Design documents
- [ ] MVP Implementation
  - [ ] DSL Parser
  - [ ] Step Executor (SymPy)
  - [ ] Basic Verifier
  - [ ] MCP Wrapper
- [ ] Domain Expansion
  - [ ] Physics formula library
  - [ ] Chemistry calculations
  - [ ] Algorithm analysis
- [ ] Advanced Features
  - [ ] Lean4 formal verification
  - [ ] Automatic derivation planning

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[Apache License 2.0](LICENSE)

---

**NSForge** — Forge new formulas through verified derivation | *Where Neural Meets Symbolic*
