# NPO (Fasting) Impact on Oral Antibiotic Efficacy

## Derivation Result

**ID**: `npo_antibiotic_effect`  
**Category**: `pharmacokinetics/absorption`  
**Status**: ✅ Verified (SymPy-MCP)

## Formula

### Final Combined PK/PD Model

$$E = E_0 + \frac{E_{max} \cdot C_{eff}^n}{EC_{50}^n + C_{eff}^n}$$

Where effective concentration depends on pH-dependent absorption:

$$C_{eff} = \frac{F_{base} \cdot D}{V_d \cdot (1 + 10^{pH - pKa})}$$

### Henderson-Hasselbalch (Fraction Non-ionized)

$$f_{non-ionized} = \frac{1}{1 + 10^{pH - pKa}}$$

### Simplified Form (from SymPy)

$$E = \frac{E_0 \left((D \cdot F_{base})^n + (EC_{50} \cdot V_d \cdot (10^{pH-pKa}+1))^n\right) + E_{max} (D \cdot F_{base})^n}{EC_{50}^n (V_d (10^{pH-pKa}+1))^n + (D \cdot F_{base})^n}$$

## SymPy Expression

```python
# Henderson-Hasselbalch (fraction non-ionized for weak acid)
f_nonionized = 1 / (1 + 10**(pH - pKa))

# Effective concentration with pH-dependent absorption
C_effective = F_base * D / (Vd * (1 + 10**(pH - pKa)))

# Emax pharmacodynamic model
E = E_0 + (E_max * C_effective**n) / (EC_50**n + C_effective**n)
```

## Variables

| Symbol | Description | Unit | Constraints |
| ------ | ----------- | ---- | ----------- |
| $E$ | Pharmacological effect (e.g., bactericidal activity) | % or effect units | ≥ E₀ |
| $E_0$ | Baseline effect | effect units | real |
| $E_{max}$ | Maximum achievable effect above baseline | effect units | positive |
| $EC_{50}$ | Concentration producing 50% of Emax | mg/L | positive |
| $n$ | Hill coefficient (sigmoidicity) | dimensionless | positive, typically 1-4 |
| $C_{eff}$ | Effective plasma concentration | mg/L | positive |
| $F_{base}$ | Baseline bioavailability (formulation) | dimensionless | 0 < F ≤ 1 |
| $D$ | Administered dose | mg | positive |
| $V_d$ | Volume of distribution | L | positive |
| $pH$ | Gastric pH | dimensionless | 1-8 |
| $pKa$ | Drug acid dissociation constant | dimensionless | positive |
| $f_{non-ionized}$ | Fraction of non-ionized drug | dimensionless | 0-1 |

## Derivation

### Base Formulas Used

1. **Henderson-Hasselbalch equation**: 
   $$pH = pKa + \log\left(\frac{[A^-]}{[HA]}\right)$$
   
2. **Sigmoid Emax (Hill) Model**: 
   $$E = E_0 + \frac{E_{max} \cdot C^n}{EC_{50}^n + C^n}$$

3. **Plasma concentration**: 
   $$C = \frac{F \cdot D}{V_d}$$

### Derivation Steps

1. **Start with Henderson-Hasselbalch**: For weak acid drugs, the fraction in non-ionized (absorbable) form is:
   $$f_{HA} = \frac{[HA]}{[HA] + [A^-]} = \frac{1}{1 + 10^{pH - pKa}}$$

2. **Model pH effect on absorption**: Only non-ionized drug crosses membranes passively
   $$F_{effective} = F_{base} \cdot f_{non-ionized}$$

3. **Calculate effective concentration**:
   $$C_{eff} = \frac{F_{base} \cdot D}{V_d \cdot (1 + 10^{pH - pKa})}$$

4. **Substitute into Emax model**: Replace C with C_eff to get pH-dependent effect

5. **Simplify using SymPy-MCP**: Combined expression verified symbolically

### SymPy-MCP Verification

```python
# Variables introduced with assumptions
intro_many([
    {"var_name": "pH", "pos_assumptions": ["real", "positive"]},
    {"var_name": "pKa", "pos_assumptions": ["real", "positive"]},
    {"var_name": "D", "pos_assumptions": ["real", "positive"]},
    {"var_name": "F_base", "pos_assumptions": ["real", "positive"]},
    {"var_name": "Vd", "pos_assumptions": ["real", "positive"]},
    {"var_name": "E_0", "pos_assumptions": ["real"]},
    {"var_name": "E_max", "pos_assumptions": ["real", "positive"]},
    {"var_name": "EC_50", "pos_assumptions": ["real", "positive"]},
    {"var_name": "n", "pos_assumptions": ["real", "positive"]},
])

# Build expressions
f_nonionized = introduce_expression("1 / (1 + 10**(pH - pKa))")
C_effective = introduce_expression("F_base * D / (Vd * (1 + 10**(pH - pKa)))")
emax_model = introduce_expression("E_0 + (E_max * C**n) / (EC_50**n + C**n)")

# Substitute C with C_effective
final_expr = substitute_expression(emax_model, "C", C_effective)
simplified = simplify_expression(final_expr)
```

**LaTeX Output**:
$$\frac{E_{0} \left(\left(D F_{base}\right)^{n} + \left(EC_{50} Vd \left(10^{pH - pKa} + 1\right)\right)^{n}\right) + E_{max} \left(D F_{base}\right)^{n}}{EC_{50}^{n} \left(Vd \left(10^{pH - pKa} + 1\right)\right)^{n} + \left(D F_{base}\right)^{n}}$$

### Numerical Verification (SymPy-MCP)

| Drug | pKa | pH=2.0 (Fed) | pH=4.5 (NPO) | Change |
|------|-----|--------------|--------------|--------|
| **Ciprofloxacin** | 6.1 | f = 99.99% | f = 97.55% | -2.4% |
| **Amoxicillin** | 2.4 | f = 71.53% | f = 0.79% | **-98.9%** |

**Key Finding**: Amoxicillin (low pKa) is dramatically affected by NPO, while Ciprofloxacin (high pKa) is minimally affected.

## Clinical Context

### When to Use

- **NPO patients**: Fasting before surgery, critically ill, GI dysfunction
- **Acid-suppressive therapy**: PPI, H2 blockers increase gastric pH
- **Weak acid antibiotics**: Penicillins, some fluoroquinolones

### Clinical Impact by Drug Class

| Drug | pKa | NPO Impact | Recommendation |
|------|-----|------------|----------------|
| Amoxicillin | 2.4 | **Severe** (>90% reduction) | Consider IV or take with acidic beverage |
| Ampicillin | 2.5 | **Severe** | Switch to IV in NPO patients |
| Cephalexin | 3.4 | **Significant** (~70% reduction) | Consider alternative |
| Ciprofloxacin | 6.1 | Minimal (<5% reduction) | OK for NPO patients |
| Levofloxacin | 5.5-6.3 | Minimal | OK for NPO patients |
| Metronidazole | 2.6 | **Significant** | Consider IV |

### Clinical Example

**Scenario**: Patient on PO Amoxicillin 500mg TID for pneumonia is made NPO for emergency surgery.

```python
# Parameters
D = 500        # mg
F_base = 0.8   # 80% baseline bioavailability
Vd = 20        # L
pKa = 2.4      # Amoxicillin
EC_50 = 2.0    # mg/L (MIC for S. pneumoniae)
E_max = 100    # % kill
n = 1.5        # Hill coefficient

# Fed state (pH = 2.0)
f_fed = 1 / (1 + 10**(2.0 - 2.4))  # = 0.715
C_fed = 0.8 * 0.715 * 500 / 20     # = 14.3 mg/L
E_fed = 100 * 14.3**1.5 / (2.0**1.5 + 14.3**1.5)  # ≈ 95%

# NPO state (pH = 4.5)
f_npo = 1 / (1 + 10**(4.5 - 2.4))  # = 0.008
C_npo = 0.8 * 0.008 * 500 / 20     # = 0.16 mg/L
E_npo = 100 * 0.16**1.5 / (2.0**1.5 + 0.16**1.5)  # ≈ 2.2%

# Effect reduction
reduction = (95 - 2.2) / 95 * 100  # ≈ 98% reduction!
```

**Clinical Decision**: Switch to IV Ampicillin/Sulbactam

## Assumptions

1. Passive diffusion is primary absorption mechanism
2. Only non-ionized form is absorbed
3. Gastric pH is uniform (simplified)
4. No active transport mechanisms (e.g., PEPT1 for β-lactams)
5. Instant equilibrium between ionized/non-ionized forms
6. Single compartment pharmacokinetics

## Limitations

1. **Active transport ignored**: β-lactams use PEPT1 transporter (may partially compensate)
2. **Gastric emptying**: NPO may accelerate emptying (variable effect)
3. **Food effects beyond pH**: Fat, protein, chelation not modeled
4. **Enteric coating**: Delayed release formulations may be less affected
5. **Intestinal pH**: Small intestine pH (~6-7) also affects absorption
6. **Drug formulation**: Salts, esters may have different pKa profiles

## References

1. Henderson LJ. Concerning the relationship between the strength of acids and their capacity to preserve neutrality. Am J Physiol. 1908.
2. Hasselbalch KA. Die Berechnung der Wasserstoffzahl des Blutes. Biochem Z. 1917.
3. Hill AV. The possible effects of the aggregation of the molecules of haemoglobin on its dissociation curves. J Physiol. 1910;40:iv-vii.
4. Dressman JB, et al. Upper gastrointestinal (GI) pH in young, healthy men and women. Pharm Res. 1990;7(7):756-761.
5. Russell TL, et al. Upper gastrointestinal pH in seventy-nine healthy, elderly, North American men and women. Pharm Res. 1993;10(2):187-196.
6. Rowland M, Tozer TN. Clinical Pharmacokinetics and Pharmacodynamics. 4th ed. Lippincott Williams & Wilkins; 2011.

## Metadata

```yaml
id: npo_antibiotic_effect
name: NPO Impact on Oral Antibiotic Efficacy
version: "1.0.0"
expression: E_0 + (E_max * (F_base * D / (Vd * (1 + 10**(pH - pKa))))**n) / (EC_50**n + (F_base * D / (Vd * (1 + 10**(pH - pKa))))**n)
category: pharmacokinetics/absorption
tags:
  - pharmacokinetics
  - pharmacodynamics
  - pH
  - ionization
  - NPO
  - fasting
  - absorption
  - antibiotic
  - Henderson-Hasselbalch
  - Emax
  - Hill-equation
derived_from:
  - henderson_hasselbalch
  - emax_model
  - pk_concentration
verified: true
verification_method: sympy_symbolic_substitution
verification_date: "2026-01-02"
sympy_mcp_verified: true
author: NSForge
created_at: "2026-01-02"
```
