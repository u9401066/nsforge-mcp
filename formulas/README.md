# � NSForge Formula Repository

> **Not a formula bank - a derivation results repository**

🌐 [English](README.md) | [繁體中文](README.zh-TW.md)

## 🎯 Purpose

This directory stores **derivation results** - formulas created through
NSForge's verified symbolic derivation process.

### What This Is NOT

| ❌ NOT This | ✅ Use Instead |
|-------------|----------------|
| Basic physics formulas | [sympy-mcp](https://github.com/space-cadet/sympy-mcp) (SymPy physics) |
| Physical constants | [sympy-mcp](https://github.com/space-cadet/sympy-mcp) (SciPy constants) |
| Clinical scoring tools | [medical-calc-mcp](https://github.com/hsieh-cy/medical-calc-mcp) |
| Textbook formulas | Standard references |

### What This IS

- **Derived formulas**: New formulas created by combining base formulas
- **Verified results**: Each formula has verification status
- **Provenance tracking**: Know where each formula came from
- **Clinical context**: Real-world application guidance

## 📁 Structure

```text
formulas/
├── README.md              ← You are here
└── derivations/           ← All derived formulas
    ├── README.md          ← Detailed documentation
    └── pharmacokinetics/  ← PK model derivations
        ├── temp_corrected_elimination.md
        └── fat_adjusted_vd.md
```

## 🔗 Ecosystem

```text
┌─────────────────────────────────────────────────────────────┐
│                   MCP Formula Ecosystem                      │
├─────────────────────────────────────────────────────────────┤
│  sympy-mcp                                                   │
│  └── Base formulas: F=ma, PV=nRT, Arrhenius...              │
│  └── Physical constants: c, G, h, R...                       │
│  └── Symbolic computation engine                             │
├─────────────────────────────────────────────────────────────┤
│  medical-calc-mcp (75+ tools)                                │
│  └── Clinical scores: APACHE, SOFA, GCS, MELD...            │
│  └── Medical calculations: eGFR, IBW, BSA...                │
├─────────────────────────────────────────────────────────────┤
│  nsforge-mcp                                                 │
│  └── Derivation framework: verify, substitute, simplify      │
│  └── Code generation: Python functions from formulas         │
│  └── THIS REPO: Store verified derivation results            │
└─────────────────────────────────────────────────────────────┘
```

## 📖 See Also

- [derivations/README.md](derivations/README.md) - Full documentation
- [Example: Temperature-corrected elimination](derivations/pharmacokinetics/temp_corrected_elimination.md)
- [Example: Fat-adjusted volume of distribution](derivations/pharmacokinetics/fat_adjusted_vd.md)
