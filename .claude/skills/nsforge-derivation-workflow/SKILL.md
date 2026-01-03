---
name: nsforge-derivation-workflow
description: 步進式推導工作流。觸發詞：推導, derive, 組合公式, 建立模型。
---

# 推導工作流 Skill

## 核心原則

> **SymPy-MCP 做計算，NSForge 記錄知識！**
> **每步都要 `print_latex_expression` 顯示給用戶！**

## 工作流程

```
Phase 1: derivation_start(name, description)
    ↓
Phase 2: 循環 {
    SymPy-MCP: intro_many → introduce_expression → 計算 → print_latex_expression
    NSForge:   derivation_record_step(expression, description, notes?)
    NSForge:   derivation_add_note(note, note_type?)  # 可選
}
    ↓
Phase 3: derivation_complete(description, assumptions?, limitations?, references?)
```

## 工具速查

| 階段 | MCP | 工具 | 用途 |
|------|-----|------|------|
| 開始 | NSForge | `derivation_start(name, description)` | 建立會話 |
| 計算 | SymPy | `intro_many`, `introduce_expression`, `substitute_expression`... | 符號計算 |
| 顯示 | SymPy | `print_latex_expression` | ⚠️ 必須！ |
| 記錄 | NSForge | `derivation_record_step(expr, desc, notes?, source?)` | 記錄步驟+知識 |
| 說明 | NSForge | `derivation_add_note(note, note_type?)` | 純文字洞見 |
| 完成 | NSForge | `derivation_complete(...)` | 存檔+元資料 |

**note_type**: `assumption`, `limitation`, `observation`, `correction`, `clinical`, `physical`

## Handoff：NSForge 做不到時

當需要 ODE/PDE、矩陣運算、聯立方程組：

```python
# 1. 導出
result = derivation_export_for_sympy()
# → 返回 intro_many_command, current_expression

# 2. SymPy-MCP 計算
intro_many([...])
dsolve_ode(...) / solve_linear_system(...)
print_latex_expression(...)

# 3. 導入回 NSForge
derivation_import_from_sympy(
    expression="...",
    operation_performed="Solved ODE",
    sympy_tool_used="dsolve_ode",
    notes="...",
    assumptions_used=[...],
    limitations=[...]
)
```

## 調用範例

```python
# Phase 1
derivation_start("temp_mm", "Temperature-corrected Michaelis-Menten")

# Phase 2a: SymPy 計算
intro_many([{"name": "V_max", "assumptions": ["positive"]}, ...])
mm = introduce_expression("V_max * C / (K_m + C)")
print_latex_expression(mm)

# Phase 2b: NSForge 記錄
derivation_record_step(
    expression="V_max * C / (K_m + C)",
    description="Base Michaelis-Menten",
    notes="假設溫度恆定"
)

# Phase 2c: 加入洞見
derivation_add_note("酵素在 >42°C 會變性", note_type="limitation")

# Phase 3
derivation_complete(
    description="...",
    assumptions=["Michaelis-Menten kinetics"],
    limitations=["Valid for 32-42°C"],
    tags=["enzyme", "temperature"]
)
```
