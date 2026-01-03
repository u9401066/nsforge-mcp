---
name: nsforge-quick-calculate
description: 快速計算（無需會話）。觸發詞：計算, 簡化, 求解, 微分, 積分, 極限, 級數, 不等式, 機率。
---

# 快速計算 Skill

## 工具分工

| 我想要... | MCP | 工具 |
|-----------|-----|------|
| 簡化/展開/分解 | SymPy | `simplify_expression`, `expand_expression`, `factor_expression` |
| 微分/積分 | SymPy | `differentiate_expression`, `integrate_expression` |
| 解方程 | SymPy | `solve_algebraically`, `solve_linear_system` |
| ODE/PDE | SymPy | `dsolve_ode`, `pdsolve_pde` |
| 矩陣 | SymPy | `matrix_*` 系列 |
| 單位換算 | SymPy | `convert_to_units` |
| **極限** | **NSForge** | `calculate_limit(expr, var, point, direction?)` |
| **級數展開** | **NSForge** | `calculate_series(expr, var, point?, order?)` |
| **求和 Σ** | **NSForge** | `calculate_summation(expr, index, lower, upper)` |
| **不等式** | **NSForge** | `solve_inequality(ineq, var, domain?)` |
| **不等式系統** | **NSForge** | `solve_inequality_system(ineqs, var)` |
| **定義分佈** | **NSForge** | `define_distribution(type, params, name?)` |
| **統計量** | **NSForge** | `distribution_stats(type, params, stats?)` |
| **機率計算** | **NSForge** | `distribution_probability(type, params, condition)` |
| **假設查詢** | **NSForge** | `query_assumptions(expr, query, assumptions?)` |
| **假設簡化** | **NSForge** | `refine_expression(expr, assumptions)` |
| 數值計算 | NSForge | `evaluate_numeric(expr, values, precision?)` |
| 等價檢查 | NSForge | `symbolic_equal(expr1, expr2)` |

## SymPy-MCP 調用模式

```python
intro("x", ["real"], [])                    # 定義變數
expr = introduce_expression("x**2 - 1")     # 建立表達式
result = simplify_expression(expr)          # 計算
print_latex_expression(result)              # ⚠️ 必須顯示給用戶！
```

## NSForge 獨特工具範例

```python
# 極限
calculate_limit("sin(x)/x", "x", "0")                    # → 1
calculate_limit("1/x", "x", "0", direction="+")          # → oo

# 級數
calculate_series("exp(x)", "x", "0", order=4)            # Taylor 展開

# 求和
calculate_summation("k", "k", "1", "n")                  # → n*(n+1)/2

# 不等式
solve_inequality("x**2 - 4 < 0", "x")                    # → (-2, 2)
solve_inequality_system(["x > 0", "x < 5"], "x")         # → (0, 5)

# 機率
distribution_stats("normal", {"mean": "mu", "std": "sigma"})
distribution_probability("exponential", {"rate": "1"}, "X < 2")

# 假設
query_assumptions("x**2", "positive", {"x": ["real", "nonzero"]})  # → True
refine_expression("sqrt(x**2)", {"x": ["positive"]})               # → x
```

## 需要推導追蹤？

切換到 `nsforge-derivation-workflow` skill。
