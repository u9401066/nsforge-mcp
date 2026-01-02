---
name: nsforge-verification-suite
description: 驗證工具組合：等式驗證、導數/積分驗證、維度分析、反向驗證。觸發詞：驗證, verify, check, 是否正確, 維度, dimension, prove。
---

# NSForge 驗證工具組合 Skill

## 觸發條件

當用戶說：
- 「驗證」「verify」「check」
- 「是否正確」「是否相等」「對不對」
- 「維度」「單位」「dimension」
- 「證明」「prove」「confirm」
- 「導數是否正確」「積分對嗎」

## 必備工具

這個 Skill 主要使用 `nsforge-mcp` 的驗證工具：

| 驗證類型 | NSForge 工具 | SymPy-MCP 替代 |
|----------|--------------|----------------|
| 符號等價 | `symbolic_equal` | - |
| 等式驗證 | `verify_equality` | - |
| 導數驗證 | `verify_derivative` | `differentiate_expression` |
| 積分驗證 | `verify_integral` | `integrate_expression` |
| 方程解驗證 | `verify_solution` | `solve_algebraically` |
| 維度分析 | `check_dimensions` | `convert_to_units` |
| 反向驗證 | `reverse_verify` | - |

## 執行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    驗證工具選擇指南                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用戶問題分析：                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 「A 和 B 相等嗎？」                                  │   │
│  │   → symbolic_equal(expr1, expr2)                    │   │
│  │   → verify_equality(expr1, expr2)                   │   │
│  │                                                     │   │
│  │ 「f'(x) = g(x) 對嗎？」                              │   │
│  │   → verify_derivative(original, claimed, var)       │   │
│  │                                                     │   │
│  │ 「∫f(x)dx = g(x) 對嗎？」                           │   │
│  │   → verify_integral(original, claimed, var)         │   │
│  │                                                     │   │
│  │ 「x=2 是方程的解嗎？」                               │   │
│  │   → verify_solution(equation, solution, var)        │   │
│  │                                                     │   │
│  │ 「這個公式的維度對嗎？」                             │   │
│  │   → check_dimensions(expr, units_map)               │   │
│  │                                                     │   │
│  │ 「反過來驗證一下」                                   │   │
│  │   → reverse_verify(expr, operation, var)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 詳細工具說明

### symbolic_equal

**目的**：檢查兩個表達式是否符號等價

**參數**：
- `expr1` (必須): 第一個表達式
- `expr2` (必須): 第二個表達式

**使用方式**：
```python
symbolic_equal(
    expr1="x**2 - 1",
    expr2="(x+1)*(x-1)"
)
```

**回傳**：
```json
{
  "equal": true,
  "method": "simplification",
  "simplified_diff": "0"
}
```

**使用時機**：
- 檢查代數恆等式
- 驗證推導步驟

---

### verify_equality

**目的**：驗證兩個表達式是否相等（更詳細的分析）

**參數**：
- `expr1` (必須): 第一個表達式
- `expr2` (必須): 第二個表達式
- `method` (可選): 驗證方法 `"symbolic"`, `"numeric"`, `"both"`

**使用方式**：
```python
verify_equality(
    expr1="sin(x)**2 + cos(x)**2",
    expr2="1",
    method="both"
)
```

**回傳**：
```json
{
  "equal": true,
  "symbolic_check": true,
  "numeric_check": true,
  "test_points": [0, 1, 3.14],
  "confidence": "high"
}
```

**與 symbolic_equal 的差異**：
- `symbolic_equal`: 快速，純符號比較
- `verify_equality`: 詳細，可加數值驗證

---

### verify_derivative

**目的**：驗證宣稱的導數是否正確

**參數**：
- `original` (必須): 原函數
- `claimed` (必須): 宣稱的導數
- `var` (必須): 微分變數

**使用方式**：
```python
# 驗證 d/dx[ln(x²)] = 2/x
verify_derivative(
    original="ln(x**2)",
    claimed="2/x",
    var="x"
)
```

**回傳**：
```json
{
  "correct": true,
  "computed_derivative": "2/x",
  "difference": "0"
}
```

**失敗回傳**：
```json
{
  "correct": false,
  "computed_derivative": "2/x",
  "claimed": "1/x",
  "difference": "1/x"
}
```

---

### verify_integral

**目的**：驗證宣稱的積分是否正確

**參數**：
- `original` (必須): 被積函數
- `claimed` (必須): 宣稱的積分結果
- `var` (必須): 積分變數

**使用方式**：
```python
# 驗證 ∫sin(x)dx = -cos(x)
verify_integral(
    original="sin(x)",
    claimed="-cos(x)",
    var="x"
)
```

**回傳**：
```json
{
  "correct": true,
  "verification_method": "differentiation",
  "derivative_of_claimed": "sin(x)"
}
```

**注意**：積分結果可能相差常數，驗證時會考慮這點。

---

### verify_solution

**目的**：驗證宣稱的值是否為方程的解

**參數**：
- `equation` (必須): 方程（可用 `"lhs = rhs"` 或 `"expr"` 表示 expr=0）
- `solution` (必須): 宣稱的解
- `var` (必須): 求解變數

**使用方式**：
```python
# 驗證 x=2 是 x²-4=0 的解
verify_solution(
    equation="x**2 - 4 = 0",
    solution="2",
    var="x"
)
```

**回傳**：
```json
{
  "correct": true,
  "substitution_result": "0",
  "is_zero": true
}
```

---

### check_dimensions

**目的**：檢查表達式的物理維度是否正確

**參數**：
- `expression` (必須): 要檢查的表達式
- `units_map` (必須): 變數到單位的映射

**使用方式**：
```python
# 檢查 F = ma 的維度
check_dimensions(
    expression="m * a",
    units_map={
        "m": "kg",
        "a": "m/s**2"
    }
)
```

**回傳**：
```json
{
  "dimension": "[mass]*[length]/[time]**2",
  "is_dimensionless": false,
  "equivalent_to": "Force (Newton)",
  "consistent": true
}
```

**常用單位映射**：
```python
# 力學
{"F": "N", "m": "kg", "a": "m/s**2", "v": "m/s", "t": "s"}

# 藥動學
{"C": "mg/L", "V": "L", "k": "1/h", "t": "h", "D": "mg"}

# 熱力學
{"T": "K", "E": "J", "R": "J/(mol*K)", "n": "mol"}
```

---

### reverse_verify

**目的**：通過反向操作驗證結果

**參數**：
- `expression` (必須): 要驗證的表達式
- `operation` (必須): 原操作 `"derivative"`, `"integral"`, `"solve"`
- `var` (必須): 變數

**使用方式**：
```python
# 如果 f'(x) = 2x，驗證積分回去是否得到 f(x)
reverse_verify(
    expression="2*x",
    operation="derivative",
    var="x"
)
# 會積分 2x 得到 x²，確認是否合理
```

**回傳**：
```json
{
  "verified": true,
  "reverse_operation": "integration",
  "result": "x**2",
  "note": "Integrated 2*x to get x**2 (plus constant)"
}
```

---

## 何時需要 SymPy-MCP

某些驗證場景需要 `sympy-mcp` 提供更強大的計算：

| 場景 | NSForge 工具 | SymPy-MCP 補充 |
|------|--------------|----------------|
| 複雜導數驗證 | `verify_derivative` | `differentiate_expression` 先計算 |
| ODE 解驗證 | - | `dsolve_ode` + 代回驗證 |
| 方程完整求解 | `verify_solution` | `solve_algebraically` 找所有解 |
| 精確單位換算 | `check_dimensions` | `convert_to_units` |
| 矩陣特徵值驗證 | - | `matrix_eigenvalues` |

### 複雜驗證範例：ODE 解

```python
# 用戶：「驗證 C(t) = C₀e^(-kt) 是 dC/dt = -kC 的解」

# Step 1: 用 SymPy-MCP 定義變數和函數
intro("t", ["real", "positive"], [])
intro("k", ["real", "positive"], [])
intro("C_0", ["real", "positive"], [])
introduce_function("C")

# Step 2: 計算宣稱解的導數
claimed_solution = introduce_expression("C_0 * exp(-k*t)")
derivative = differentiate_expression(claimed_solution, "t")
# → -k * C_0 * exp(-k*t)

# Step 3: 代入 ODE 右邊
rhs = introduce_expression("-k * C_0 * exp(-k*t)")

# Step 4: 用 NSForge 驗證等式
symbolic_equal(
    expr1="-k * C_0 * exp(-k*t)",  # dC/dt
    expr2="-k * C_0 * exp(-k*t)"   # -kC
)
# → equal: true ✅
```

### 單位系統整合範例

```python
# 用戶：「確認動能公式 E = ½mv² 的單位是焦耳」

# Step 1: 用 SymPy-MCP 做精確單位分析
intro_many([
    {"var_name": "m", "pos_assumptions": ["positive"]},
    {"var_name": "v", "pos_assumptions": ["positive"]}
])
energy = introduce_expression("0.5 * m * v**2")

# Step 2: 設定單位
# m = 1 kg, v = 1 m/s
result = convert_to_units(energy, ["joule"])
# → 0.5 joule ✅

# 或用 NSForge 檢查維度
check_dimensions(
    expression="0.5 * m * v**2",
    units_map={"m": "kg", "v": "m/s"}
)
# → dimension: [mass]*[length]**2/[time]**2 = Energy ✅
```

---

## 常見使用場景

### 場景 1：「sin²x + cos²x = 1 對嗎？」

```python
symbolic_equal(
    expr1="sin(x)**2 + cos(x)**2",
    expr2="1"
)
```

**Agent 回應**：
> ✅ 正確！這是畢氏恆等式（Pythagorean identity）。
> 驗證方法：符號簡化後差為 0。

---

### 場景 2：「驗證 d/dx[e^(x²)] = 2xe^(x²)」

```python
verify_derivative(
    original="exp(x**2)",
    claimed="2*x*exp(x**2)",
    var="x"
)
```

**Agent 回應**：
> ✅ 正確！使用鏈式法則：
> d/dx[e^(x²)] = e^(x²) · d/dx[x²] = e^(x²) · 2x = 2xe^(x²)

---

### 場景 3：「F = ma 的維度對嗎？」

```python
check_dimensions(
    expression="m * a",
    units_map={"m": "kg", "a": "m/s**2"}
)
```

**Agent 回應**：
> ✅ 維度正確！
> - m·a = [kg] × [m/s²] = [kg·m/s²] = [N]
> - 這就是力的單位：牛頓 (Newton)

---

### 場景 4：「x = 3 是 x² - 9 = 0 的解嗎？」

```python
verify_solution(
    equation="x**2 - 9 = 0",
    solution="3",
    var="x"
)
```

**Agent 回應**：
> ✅ 正確！代入驗證：3² - 9 = 9 - 9 = 0
> 
> 注意：x = -3 也是這個方程的解。

---

### 場景 5：「這個推導結果對嗎？」（反向驗證）

```python
# 如果用戶說推導出 ∫(1/x)dx = ln|x|
reverse_verify(
    expression="ln(x)",
    operation="integral",
    var="x"
)
```

**Agent 回應**：
> ✅ 反向驗證通過！
> 對 ln(x) 微分得到 1/x，確認積分結果正確。

---

## 驗證策略建議

### 多層驗證
對於重要的推導結果，建議使用多種驗證方法：

```python
# Layer 1: 符號等價
symbolic_equal(expr1, expr2)

# Layer 2: 維度分析
check_dimensions(result, units_map)

# Layer 3: 數值抽樣
verify_equality(expr1, expr2, method="numeric")

# Layer 4: 反向驗證
reverse_verify(result, operation, var)
```

### 驗證順序
1. **先做維度分析** - 維度錯了，結果一定錯
2. **再做符號驗證** - 確認代數正確
3. **最後數值抽樣** - 處理特殊情況

---

## 錯誤處理

### 表達式解析失敗
```json
{
  "success": false,
  "error": "Cannot parse expression: ..."
}
```
→ 檢查表達式語法，確保用 SymPy 格式

### 維度不一致
```json
{
  "consistent": false,
  "error": "Dimension mismatch",
  "left_dim": "[length]",
  "right_dim": "[time]"
}
```
→ 推導可能有錯，檢查每一步

### 驗證不確定
```json
{
  "verified": "uncertain",
  "reason": "Expression too complex for symbolic analysis"
}
```
→ 嘗試用數值方法或簡化表達式

---

## 相關 Skills

- `nsforge-derivation-workflow`: 建立推導時同步驗證
- `nsforge-formula-management`: 標記公式為「已驗證」
- `nsforge-quick-calculate`: 快速計算驗證
- `sympy-mcp`: 複雜計算支援（ODE、矩陣）
