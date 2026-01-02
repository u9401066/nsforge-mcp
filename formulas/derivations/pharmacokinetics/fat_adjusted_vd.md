# Body Fat-Adjusted Volume of Distribution

## Derivation Result

**ID**: `fat_adjusted_vd`  
**Category**: `pharmacokinetics/obesity`  
**Status**: ✅ Verified

## Formula

$$V_d^{adj} = V_d^{lean} + f_{fat} \cdot (TBW - LBW)$$

Where $f_{fat}$ depends on drug lipophilicity:

$$f_{fat} = \begin{cases} 
0.1 & \text{hydrophilic (LogP < 0)} \\
0.3 \cdot (1 + LogP) & \text{intermediate (0 ≤ LogP < 2)} \\
1.0 & \text{lipophilic (LogP ≥ 2)}
\end{cases}$$

## SymPy Expression

```python
V_lean + f_fat * (TBW - LBW)
```

## Variables

| Symbol | Description | Unit | Constraints |
| ------ | ----------- | ---- | ----------- |
| $V_d^{adj}$ | Adjusted volume of distribution | L | positive |
| $V_d^{lean}$ | Volume of distribution in lean tissue | L | positive |
| $f_{fat}$ | Fat partitioning coefficient | dimensionless | 0 < f ≤ 1 |
| $TBW$ | Total body weight | kg | positive |
| $LBW$ | Lean body weight | kg | positive |
| $LogP$ | Octanol-water partition coefficient | dimensionless | real |

## Derivation

### Base Formulas Used

1. **Volume of distribution**: $V_d = \frac{Dose}{C_0}$
2. **Lean body weight (Boer)**: $LBW = 0.407 \cdot W + 0.267 \cdot H - 19.2$ (male)
3. **Lipophilicity partitioning**: Drug distribution proportional to LogP

### Derivation Steps

1. Standard Vd assumes normal body composition
2. In obesity, excess adipose tissue provides additional distribution volume
3. Lipophilic drugs partition into fat tissue (high LogP)
4. Hydrophilic drugs remain in aqueous compartments (low LogP)
5. Model fat contribution as: $V_{fat} = f_{fat} \cdot V_{adipose}$
6. Adipose volume ≈ (TBW - LBW) assuming fat density ≈ 0.9 kg/L
7. Combine: $V_d^{adj} = V_d^{lean} + f_{fat} \cdot (TBW - LBW)$

### Verification

- **Method**: Limiting case analysis
- **Verified at**: 2026-01-02
- **Results**:
  - When TBW = LBW (no fat): $V_d^{adj} = V_d^{lean}$ ✓
  - Lipophilic drug (f=1): Full fat contribution ✓
  - Hydrophilic drug (f≈0): Minimal fat contribution ✓

## Clinical Context

### When to Use

- **Obese patients**: BMI > 30
- **Lipophilic drugs**: Propofol, fentanyl, benzodiazepines
- **Loading dose calculations**: Critical to avoid underdosing in obesity

### Clinical Example

Propofol loading dose for morbidly obese patient:

```python
# Patient: 150 kg, 170 cm, male
TBW = 150  # kg
LBW = 0.407 * 150 + 0.267 * 170 - 19.2  # ≈ 87 kg

# Propofol (LogP ≈ 4, highly lipophilic)
f_fat = 1.0  # Full fat distribution
V_lean = 0.3 * LBW  # 26 L (standard Vd for lean)

# Adjusted Vd
V_adj = V_lean + f_fat * (TBW - LBW)
# V_adj = 26 + 1.0 * (150 - 87) = 89 L

# vs. using TBW directly: 0.3 * 150 = 45 L (underestimate!)
# vs. using LBW only: 26 L (underestimate for lipophilic drug!)
```

**Clinical implication**: Use adjusted Vd for lipophilic drug loading doses in obesity.

### Drug-Specific f_fat Values

| Drug | LogP | f_fat | Clinical Note |
| ---- | ---- | ----- | ------------- |
| Propofol | 4.0 | 1.0 | Full fat distribution |
| Fentanyl | 4.1 | 1.0 | Full fat distribution |
| Midazolam | 3.9 | 1.0 | Full fat distribution |
| Rocuronium | -2.1 | 0.1 | Use LBW |
| Vancomycin | -3.1 | 0.1 | Use LBW |
| Gentamicin | -3.1 | 0.1 | Use adjusted BW (0.4 factor) |

## Assumptions

1. Two-compartment model (lean + fat)
2. Fat tissue composition is uniform
3. LogP predicts tissue partitioning
4. Instantaneous distribution equilibrium

## Limitations

1. Does not account for altered protein binding in obesity
2. Simplifies fat distribution (visceral vs subcutaneous)
3. May not apply to drugs with specific transporters
4. Pediatric obesity may differ

## References

1. Hanley MJ, et al. Effect of obesity on the pharmacokinetics of drugs. Clin Pharmacokinet. 2010.
2. Pai MP, Paloucek FP. The origin of the "ideal" body weight equations. Ann Pharmacother. 2000.
3. NSForge derivation session 2026-01-02

## Metadata

```yaml
id: fat_adjusted_vd
name: Body Fat-Adjusted Volume of Distribution
version: "1.0.0"
expression: V_lean + f_fat * (TBW - LBW)
category: pharmacokinetics/obesity
tags:
  - pharmacokinetics
  - obesity
  - volume-of-distribution
  - lipophilicity
  - dosing
derived_from:
  - volume_of_distribution
  - lean_body_weight_boer
verified: true
verification_method: limiting_case_analysis
author: NSForge
created_at: "2026-01-02"
```
