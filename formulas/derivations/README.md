# 🔨 NSForge Derivation Results

> **Formulas created through verified derivation, not copied from textbooks**

🌐 [English](README.md) | [繁體中文](README.zh-TW.md)

## 🎯 What This Is

This directory contains **derived formulas** - new formulas created by combining
base formulas and verifying the results through NSForge's symbolic computation tools.

```
┌─────────────────────────────────────────────────────────────┐
│                    Formula Ecosystem                         │
├─────────────────────────────────────────────────────────────┤
│ sympy-mcp          │ Base formulas (F=ma, Arrhenius...)     │
│ medical-calc-mcp   │ Clinical scores (APACHE, SOFA...)      │
├─────────────────────────────────────────────────────────────┤
│ nsforge-mcp        │ 🔨 Derivation framework + verification │
│  └── formulas/     │ 📚 DERIVED formulas (this directory)   │
│                    │    • Temperature-corrected PK models   │
│                    │    • Obesity-adjusted dosing formulas  │
│                    │    • Custom composite models           │
└─────────────────────────────────────────────────────────────┘
```

## ✅ What Belongs Here

| Category | Example | Description |
| -------- | ------- | ----------- |
| Temperature corrections | `temp_corrected_elimination` | Drug elimination adjusted for hypothermia/fever |
| Obesity adjustments | `fat_adjusted_vd` | Volume of distribution corrected for body fat |
| Renal adjustments | `renal_dose_adjustment` | Dosing for impaired kidney function |
| Drug interactions | `cyp_inhibition_model` | PK changes with enzyme inhibitors |
| Custom PK/PD | `effect_site_targeting` | Target-controlled infusion models |

## ❌ What Does NOT Belong Here

| Type | Where It Belongs | Why |
| ---- | ---------------- | --- |
| Basic physics (F=ma) | sympy-mcp | Already in SymPy |
| Arrhenius equation | sympy-mcp | Already in SymPy |
| Physical constants | sympy-mcp | Already in SciPy |
| Clinical scores | medical-calc-mcp | Scoring ≠ derivation |
| Textbook formulas | sympy-mcp | Not derived, just copied |

## 📁 Directory Structure

```
formulas/
└── derivations/           ← All derived formulas go here
    ├── README.md          ← You are here
    ├── pharmacokinetics/  ← PK model derivations
    │   ├── temp_corrected_elimination.md
    │   ├── fat_adjusted_vd.md
    │   └── renal_clearance_adjustment.md
    ├── pharmacodynamics/  ← PD model derivations
    │   └── effect_site_equilibration.md
    └── combined/          ← Complex multi-domain derivations
        └── tkpi_model.md
```

## 📄 File Format

Each derivation result is a Markdown file with YAML metadata:

```markdown
# Formula Name

## Derivation Result

**ID**: `unique_id`
**Category**: `pharmacokinetics/temperature`
**Status**: ✅ Verified

## Formula

$$\text{LaTeX formula here}$$

## SymPy Expression

\`\`\`python
sympy_expression_string
\`\`\`

## Variables

| Symbol | Description | Unit | Constraints |
...

## Derivation

### Base Formulas Used
### Derivation Steps
### Verification

## Clinical Context

### When to Use
### Clinical Example

## Metadata

\`\`\`yaml
id: unique_id
expression: sympy_expression
derived_from: [base_formula_1, base_formula_2]
verified: true
...
\`\`\`
```

## 🔧 How to Create New Derivations

### 1. Use NSForge MCP Tools

```
User: "Derive a temperature-corrected elimination rate model"

Agent:
1. get_formula("one_compartment") from sympy-mcp
2. get_formula("arrhenius") from sympy-mcp  
3. substitute and simplify
4. verify_derivative / check_dimensions
5. generate_derivation_report
6. save to formulas/derivations/
```

### 2. Manual Creation

1. Create a new `.md` file in the appropriate category
2. Follow the file format above
3. Include derivation steps and verification
4. Add YAML metadata at the end

## 📊 Current Derivations

| ID | Name | Category | Verified |
| -- | ---- | -------- | -------- |
| `temp_corrected_elimination` | Temperature-Corrected Elimination | PK/temperature | ✅ |
| `fat_adjusted_vd` | Fat-Adjusted Volume of Distribution | PK/obesity | ✅ |

## 🔗 Related Tools

- **sympy-mcp**: Base formulas and symbolic computation
- **medical-calc-mcp**: Clinical scoring tools (75+ calculators)
- **NSForge verify tools**: `verify_derivative`, `verify_integral`, `check_dimensions`
- **NSForge codegen**: `generate_python_function`, `generate_derivation_report`
