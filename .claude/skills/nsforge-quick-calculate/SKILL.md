---
name: nsforge-quick-calculate
description: 快速計算（無需會話）：簡化、展開、因式分解、求解、微分、積分。觸發詞：計算, calculate, 簡化, simplify, 求解, solve, 微分, 積分。
---

# NSForge 快速計算 Skill

## ⚠️ 重要：使用 SymPy-MCP 進行計算！

> **數學計算必須使用 SymPy-MCP！**
>
> NSForge 的計算工具已**移除**（simplify, solve, differentiate 等）
> 只保留 `evaluate_numeric` 和 `symbolic_equal`

### 正確流程

```text
1. 用 SymPy-MCP 執行計算
   intro_many([{"var_name": "x", "pos_assumptions": ["real"], ...}])
   expr = introduce_expression("x**2 - 4")
   solve_algebraically(expr, "x", "REAL")
   
2. 用 print_latex_expression 顯示結果
   print_latex_expression(result)
   # → 顯示 LaTeX 給用戶確認

3. 如需存檔，建立 Markdown 文件
   formulas/derivations/xxx.md
```

---

## 觸發條件

當用戶說：

- 「計算」「calculate」「compute」「算」
- 「簡化」「simplify」「化簡」
- 「展開」「expand」
- 「因式分解」「factor」「分解」
- 「求解」「solve」「解方程」
- 「微分」「differentiate」「導數」「derivative」
- 「積分」「integrate」「求積」
- 「代入」「substitute」「把...代入」
- 「等於多少」「是多少」

## 工具選擇指南

```text
┌─────────────────────────────────────────────────────────────┐
│              🌟 使用 SymPy-MCP 進行計算 🌟                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SymPy-MCP 工具（計算專用！）：                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ intro_many + introduce_expression  # 定義變數/表達式│   │
│  │ simplify_expression                # 簡化          │   │
│  │ expand_expression                  # 展開          │   │
│  │ factor_expression                  # 因式分解      │   │
│  │ solve_algebraically                # 求解（指定域）│   │
│  │ solve_linear_system                # 聯立方程組    │   │
│  │ differentiate_expression           # 微分          │   │
│  │ integrate_expression               # 積分          │   │
│  │ substitute_expression              # 代換          │   │
│  │ dsolve_ode / pdsolve_pde          # 微分方程      │   │
│  │ matrix_* 系列                      # 矩陣運算      │   │
│  │ convert_to_units                   # 單位換算      │   │
│  │ print_latex_expression             # ⚠️ 顯示結果！ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NSForge 工具（只保留輔助功能）：                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ evaluate_numeric(expr, vals) # 最終數值計算        │   │
│  │ symbolic_equal(e1, e2)       # 快速等價檢查        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ❌ 已移除的工具（使用 SymPy-MCP 替代）：                    │
│     simplify, expand, factor, solve,                       │
│     differentiate, integrate, substitute                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## SymPy-MCP 快速計算範例

### 範例 1：求解方程

```python
# 1. 定義變數
intro("x", ["real"], [])

# 2. 建立方程
expr = introduce_expression("x**2 - 5*x + 6")

# 3. 求解
result = solve_algebraically(expr, "x", "REAL")

# 4. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → x = 2, 3
```

### 範例 2：微分

```python
# 1. 定義變數
intro("x", ["real"], [])

# 2. 建立表達式
expr = introduce_expression("sin(x)**2")

# 3. 微分
result = differentiate_expression(expr, "x")

# 4. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → 2 sin(x) cos(x)
```

### 範例 3：簡化

```python
# 1. 建立表達式
expr = introduce_expression("sin(x)**2 + cos(x)**2")

# 2. 簡化
result = simplify_expression(expr)

# 3. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → 1
```

### 範例 4：展開

```python
# 1. 建立表達式
expr = introduce_expression("(x + 1)**3")

# 2. 展開
result = expand_expression(expr)

# 3. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → x³ + 3x² + 3x + 1
```

### 範例 5：積分

```python
# 1. 定義變數
intro("x", ["real"], [])

# 2. 建立表達式
expr = introduce_expression("x**2")

# 3. 積分
result = integrate_expression(expr, "x")

# 4. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → x³/3
```

### 範例 6：單位換算

```python
# 1. 建立帶單位的表達式
expr = introduce_expression("100 * kilometer / hour")

# 2. 轉換單位
result = convert_to_units(expr, ["meter", "1/second"])

# 3. ⚠️ 顯示給用戶確認！
print_latex_expression(result)
# → 27.78 m/s
```

---

## NSForge 保留的工具

### evaluate_numeric - 數值計算

**目的**：計算最終數值（在符號計算完成後使用）

**參數**：
- `expression` (必須): 表達式
- `values` (必須): 變數值映射
- `precision` (可選): 小數位數

**使用方式**：
```python
# 計算結果
evaluate_numeric(
    expression="sqrt(x**2 + y**2)",
    values={"x": 3, "y": 4}
)
# → 5.0
```

### symbolic_equal - 等價檢查

**目的**：快速檢查兩個表達式是否等價

**參數**：
- `expr1` (必須): 第一個表達式
- `expr2` (必須): 第二個表達式

**使用方式**：
```python
# 檢查等價
symbolic_equal("(x+1)**2", "x**2 + 2*x + 1")
# → equivalent: True
```

---

## 常見使用場景

### 場景 1：「簡化 sin²x + cos²x」

```python
# 使用 SymPy-MCP
expr = introduce_expression("sin(x)**2 + cos(x)**2")
result = simplify_expression(expr)
print_latex_expression(result)
```

**Agent 回應**：
> $= 1$
> 
> 這是畢氏恆等式。

---

### 場景 2：「展開 (a+b)³」

```python
# 使用 SymPy-MCP
expr = introduce_expression("(a + b)**3")
result = expand_expression(expr)
print_latex_expression(result)
```

**Agent 回應**：
> $= a^3 + 3a^2b + 3ab^2 + b^3$
> 
> 使用二項式定理展開。

---

### 場景 3：「解 x² - 5x + 6 = 0」

```python
# 使用 SymPy-MCP
intro("x", ["real"], [])
expr = introduce_expression("x**2 - 5*x + 6")
result = solve_algebraically(expr, "x", "REAL")
print_latex_expression(result)
```

**Agent 回應**：
> $x = 2$ 或 $x = 3$
> 
> 可驗證：$(x-2)(x-3) = x^2 - 5x + 6$ ✅

---

### 場景 4：「對 e^(x²) 微分」

```python
# 使用 SymPy-MCP
intro("x", ["real"], [])
expr = introduce_expression("exp(x**2)")
result = differentiate_expression(expr, "x")
print_latex_expression(result)
```

**Agent 回應**：
> $= 2x \cdot e^{x^2}$
> 
> 使用鏈式法則：d/dx[e^u] = e^u · du/dx，其中 u = x²

---

### 場景 5：「計算 ∫₀¹ x² dx」

```python
# 使用 SymPy-MCP
intro("x", ["real"], [])
expr = introduce_expression("x**2")
result = integrate_expression(expr, ("x", 0, 1))
print_latex_expression(result)
```

**Agent 回應**：
> $= \frac{1}{3}$
> 
> 計算過程：$[x^3/3]_0^1 = 1/3 - 0 = 1/3$

---

### 場景 6：「把 x=2, y=3 代入 x² + y²」

```python
# 使用 SymPy-MCP
expr = introduce_expression("x**2 + y**2")
result = substitute_expression(expr, {"x": "2", "y": "3"})
print_latex_expression(result)

# 或用 NSForge 數值計算
evaluate_numeric("x**2 + y**2", values={"x": 2, "y": 3})
```

**Agent 回應**：
> $= 4 + 9 = 13$

---

### 場景 7：「π 的值是多少？」

```python
# 使用 NSForge
evaluate_numeric(expression="pi", values={}, precision=15)
```

**Agent 回應**：
> π ≈ 3.14159265358979

---

### 場景 8：「解這個聯立方程」

用戶：「解 2x + y = 5 和 x - y = 1」

```python
# 使用 SymPy-MCP
intro_many([
    {"var_name": "x", "pos_assumptions": ["real"], "neg_assumptions": []},
    {"var_name": "y", "pos_assumptions": ["real"], "neg_assumptions": []}
])
eq1 = introduce_expression("2*x + y - 5")
eq2 = introduce_expression("x - y - 1")
result = solve_linear_system([eq1, eq2], ["x", "y"], "REAL")
print_latex_expression(result)
```

**Agent 回應**：
> 解得：$x = 2, y = 1$
> 
> 驗證：2(2) + 1 = 5 ✅，2 - 1 = 1 ✅

---

## 決策樹

```
用戶要求計算
    │
    ├─ 所有符號計算 → SymPy-MCP
    │   ├─ 簡化 → simplify_expression
    │   ├─ 展開 → expand_expression
    │   ├─ 分解 → factor_expression
    │   ├─ 微分 → differentiate_expression
    │   ├─ 積分 → integrate_expression
    │   ├─ 代入 → substitute_expression
    │   ├─ 單一方程 → solve_algebraically
    │   ├─ 聯立方程 → solve_linear_system
    │   ├─ ODE → dsolve_ode
    │   ├─ PDE → pdsolve_pde
    │   └─ 矩陣 → matrix_* 系列
    │
    ├─ 最終數值計算 → NSForge evaluate_numeric
    │
    └─ 等價檢查 → NSForge symbolic_equal
```

---

## 🔄 需要推導過程追蹤時

**如果需要記錄步驟或複雜推導，切換到 `nsforge-derivation-workflow`：**

```python
# 1. 開始推導會話
derivation_start(name="calculation", description="...")

# 2. 載入公式或表達式
derivation_load_formula("expression")

# 3. 使用 Handoff 機制
# 當遇到 NSForge 無法處理的操作時：
export = derivation_export_for_sympy()
# → 取得 intro_many 和 introduce_expression 指令

# 4. SymPy-MCP 執行計算
[SymPy-MCP] intro_many([...])
[SymPy-MCP] introduce_expression("...")
[SymPy-MCP] dsolve_ode(...) / solve_linear_system(...) / etc.
[SymPy-MCP] print_latex_expression(...)

# 5. 導入回 NSForge
derivation_import_from_sympy(
    expression="...",
    operation_performed="...",
    sympy_tool_used="...",
    notes="...",
    assumptions_used=[...],
    limitations=[...]
)

# 6. 完成並存檔
derivation_complete(...)
```

**詳見 `nsforge-derivation-workflow` skill！**

---

## 相關 Skills

- `nsforge-derivation-workflow`: 需要追蹤步驟時使用
- `nsforge-verification-suite`: 驗證計算結果
- `nsforge-formula-management`: 將結果存檔
- `sympy-mcp`: 所有符號計算的核心引擎
