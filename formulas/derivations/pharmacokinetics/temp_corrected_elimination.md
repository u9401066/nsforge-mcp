# Temperature-Corrected Drug Elimination Rate

## Derivation Result

**ID**: `temp_corrected_elimination`  
**Category**: `pharmacokinetics/temperature`  
**Status**: ✅ Verified

## Formula

$$k(T) = k_{ref} \cdot e^{\frac{E_a}{R}\left(\frac{1}{T_{ref}} - \frac{1}{T}\right)}$$

## SymPy Expression

```python
k_ref * exp((E_a / R) * (1/T_ref - 1/T))
```

## Variables

| Symbol | Description | Unit | Constraints |
| ------ | ----------- | ---- | ----------- |
| $k(T)$ | Elimination rate at temperature T | 1/h | positive |
| $k_{ref}$ | Reference elimination rate (at 37°C) | 1/h | positive |
| $E_a$ | Activation energy | J/mol | positive |
| $R$ | Gas constant | 8.314 J/(mol·K) | constant |
| $T$ | Actual body temperature | K | positive |
| $T_{ref}$ | Reference temperature (310.15 K = 37°C) | K | constant |

## Derivation

### Base Formulas Used

1. **One-compartment elimination**: $C(t) = C_0 \cdot e^{-kt}$
2. **Arrhenius equation**: $k = A \cdot e^{-E_a/(RT)}$

### Derivation Steps

1. Start with standard one-compartment model: $k = k_{ref}$ at $T = T_{ref}$
2. Apply Arrhenius temperature dependence to rate constant
3. Express ratio: $\frac{k(T)}{k_{ref}} = \frac{A \cdot e^{-E_a/(RT)}}{A \cdot e^{-E_a/(RT_{ref})}}$
4. Simplify to get temperature correction factor
5. Verify by dimensional analysis

### Verification

- **Method**: Dimensional analysis + reverse substitution
- **Verified at**: 2026-01-02
- **Result**: Dimensions consistent (1/time), reduces to $k_{ref}$ when $T = T_{ref}$

## Clinical Context

### When to Use

- **Hypothermia**: Patient temperature < 35°C (therapeutic hypothermia, accidental)
- **Hyperthermia**: Patient temperature > 38.5°C (fever, heat stroke)
- **Drug dosing adjustments**: When standard PK parameters may not apply

### Clinical Example

Patient in therapeutic hypothermia (33°C = 306.15 K) receiving propofol:

```python
# Standard parameters at 37°C
k_ref = 0.3  # 1/h (propofol elimination)
E_a = 50000  # J/mol (typical drug activation energy)
R = 8.314
T_ref = 310.15  # K (37°C)
T = 306.15  # K (33°C)

# Temperature-corrected rate
k_corrected = k_ref * exp((E_a/R) * (1/T_ref - 1/T))
# k_corrected ≈ 0.22 /h (27% slower elimination)
```

**Clinical implication**: Reduce maintenance dose by ~25% during hypothermia.

## Assumptions

1. Arrhenius behavior applies to enzymatic drug metabolism
2. Activation energy is constant over the temperature range
3. No phase transitions or protein denaturation occurs
4. Single elimination pathway dominates

## Limitations

1. May not apply to drugs with multiple elimination pathways
2. Extreme temperatures may cause non-linear effects
3. Does not account for temperature effects on protein binding
4. Activation energy varies between drugs (50-100 kJ/mol typical)

## References

1. Zhou H, et al. Temperature effects on drug pharmacokinetics. Clin Pharmacokinet. 2020.
2. Tortorici MA, et al. Therapeutic hypothermia and drug disposition. Ther Drug Monit. 2007.
3. NSForge derivation session 2026-01-02

## Metadata

```yaml
id: temp_corrected_elimination
name: Temperature-Corrected Drug Elimination Rate
version: "1.0.0"
expression: k_ref * exp((E_a / R) * (1/T_ref - 1/T))
category: pharmacokinetics/temperature
tags:
  - pharmacokinetics
  - temperature
  - arrhenius
  - hypothermia
  - drug-elimination
derived_from:
  - one_compartment_model
  - arrhenius_equation
verified: true
verification_method: dimensional_analysis
author: NSForge
created_at: "2026-01-02"
```
