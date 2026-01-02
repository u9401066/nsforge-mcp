# NSForge Skills 使用指南

> 📖 給人看的文檔：說明 Agent 如何使用 NSForge 工具完成任務

## ⚠️ 最重要的原則（必讀！）

### 數學計算黃金法則

> **「先用 SymPy-MCP 計算驗證，再用 NSForge 存檔管理！」**
>
> **「每步計算都要用 `print_latex_expression` 顯示給用戶確認！」**

### 正確的工作流程

```text
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: SymPy-MCP 執行計算                                │
│  ─────────────────────────────────────────────────────────  │
│  1. intro_many([...])              # 定義變數              │
│  2. introduce_expression(...)      # 建立表達式            │
│  3. substitute/solve/dsolve...     # 執行運算              │
│  4. print_latex_expression(...)    # ⚠️ 顯示給用戶確認！   │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: 用戶確認結果                                      │
│  ─────────────────────────────────────────────────────────  │
│  Agent: 「計算結果是 $E = mc^2$，這個正確嗎？」             │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: NSForge 存檔知識                                  │
│  ─────────────────────────────────────────────────────────  │
│  1. derivation_start(...)          # 開始會話（可選）      │
│  2. 建立 Markdown 文件             # 人類可讀格式          │
│     formulas/derivations/xxx.md    # 正確的存檔位置        │
└─────────────────────────────────────────────────────────────┘
```

### 分工原則

| 任務 | 使用工具 | 原因 |
|------|----------|------|
| **數學計算** | SymPy-MCP | ODE/PDE、矩陣、單位換算等完整功能 |
| **公式顯示** | `print_latex_expression` | 每步都要顯示給用戶確認！ |
| **知識存檔** | Markdown 文件 | 存到 `formulas/derivations/` |
| **維度檢查** | NSForge `check_dimensions` | 驗證物理維度 |

### ❌ 禁止行為

1. **不要跳過公式顯示** - 用戶需要看到並確認每步結果
2. **不要存成 YAML** - 存檔格式應為 Markdown（參考 `formulas/derivations/` 範例）
3. **不要直接生成程式碼** - 先用 SymPy-MCP 驗證計算正確性

---

## 設計理念

### 為什麼需要 Skills？

NSForge 提供 **41 個 MCP 工具**，直接丟給 Agent 會造成：
- 🤯 工具太多，不知道從哪開始
- 🔄 工具使用順序混亂
- ❌ 忘記關鍵步驟（如驗證、存檔）

**Skills = 工具的使用說明書**，告訴 Agent：
1. 何時使用這組工具
2. 工具的正確調用順序
3. 每步的成功/失敗處理

### 架構總覽

```
┌─────────────────────────────────────────────────────────────┐
│                    NSForge Skills 架構                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔥 derivation-workflow    ← 核心：完整推導工作流           │
│     └─ 建立會話 → 載入公式 → 推導操作 → 驗證 → 存檔         │
│                                                             │
│  📚 formula-management     ← 公式庫管理                     │
│     └─ 查詢 → 取得 → 更新 → 刪除                            │
│                                                             │
│  ✅ verification-suite     ← 驗證工具組合                   │
│     └─ 等式驗證 → 維度檢查 → 反向驗證                       │
│                                                             │
│  💻 code-generation        ← 程式碼/報告生成                │
│     └─ Python 函數 → LaTeX → Markdown 報告                 │
│                                                             │
│  ⚡ quick-calculate        ← 快速計算（無需會話）           │
│     └─ 簡化 → 求解 → 微分 → 積分                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Skill 1: derivation-workflow（推導工作流）

### 💡 設計理念

這是 NSForge 的核心！**Forge = 鍛造新公式**。

傳統做法：Agent 直接輸出推導（可能出錯，無法追溯）
NSForge 做法：Agent 規劃步驟 → SymPy 執行 → 每步可驗證可追溯

### ✅ 能完成的任務

| 任務類型 | 範例 |
|----------|------|
| 組合公式 | 將 Arrhenius 方程代入藥動學模型，得到溫度校正消除率 |
| 推導變形 | 從 PV=nRT 推導密度公式 ρ = PM/RT |
| 數學推導 | 對運動方程積分得到位移公式 |
| 模型建立 | 從質量守恆推導藥物濃度隨時間變化 |

### 🔧 使用的工具（按順序）

```
1. derivation_start(name, description)     # 開始推導會話
2. derivation_load_formula(formula, ...)   # 載入基礎公式（可多次）
3. derivation_substitute(var, replacement) # 代入操作
   derivation_simplify()                   # 簡化
   derivation_solve_for(variable)          # 求解
   derivation_differentiate(var)           # 微分
   derivation_integrate(var)               # 積分
4. check_dimensions(expr, units_map)       # 驗證維度 ⚠️ 重要
5. derivation_complete(description, ...)   # 完成並存檔
```

### 📋 Agent 會看到的觸發詞

- 「推導」「derive」「從...推導」
- 「組合公式」「combine formulas」
- 「建立模型」「create model」
- 「證明」「prove」

### 🎯 成功標準

- [ ] 推導結果通過維度檢查
- [ ] 每步都有記錄（可用 `derivation_get_steps()` 查看）
- [ ] 結果已存檔（可用 `derivation_list_saved()` 確認）

---

## Skill 2: formula-management（公式庫管理）

### 💡 設計理念

推導出的公式是**知識資產**，需要妥善管理：
- 儲存：保留完整推導過程和元資料
- 查詢：快速找到需要的公式
- 更新：補充臨床情境、驗證狀態
- 復用：作為新推導的基礎

### ✅ 能完成的任務

| 任務類型 | 範例 |
|----------|------|
| 查詢公式 | 「找出所有關於溫度校正的公式」 |
| 檢視詳情 | 「這個公式的假設條件是什麼？」 |
| 更新元資料 | 「把這個公式標記為已驗證」 |
| 統計資訊 | 「公式庫有多少條目？」 |

### 🔧 使用的工具

```
derivation_list_saved(category)        # 列出公式
derivation_search_saved(query)         # 關鍵字搜尋
derivation_get_saved(result_id)        # 取得詳情
derivation_update_saved(result_id, **) # 更新元資料
derivation_delete_saved(result_id)     # 刪除（需確認）
derivation_repository_stats()          # 統計資訊
```

### 📋 Agent 會看到的觸發詞

- 「找公式」「search formula」
- 「列出」「list」「有哪些」
- 「更新公式」「標記為」
- 「刪除」「移除」

---

## Skill 3: verification-suite（驗證工具組合）

### 💡 設計理念

數學推導**必須可驗證**。三層驗證機制：

1. **符號等式驗證** - 兩個表達式是否等價
2. **維度分析** - 物理量的單位是否正確
3. **反向驗證** - 對結果反向操作是否回到原式

### ✅ 能完成的任務

| 任務類型 | 範例 |
|----------|------|
| 等式驗證 | 「x²-1 和 (x+1)(x-1) 是否相等？」 |
| 導數驗證 | 「ln(x) 的導數是 1/x 嗎？」 |
| 積分驗證 | 「∫sin(x)dx = -cos(x) 對嗎？」 |
| 維度檢查 | 「F = ma 的維度正確嗎？」 |
| 方程驗證 | 「x=2 是 x²-4=0 的解嗎？」 |

### 🔧 使用的工具

```
verify_equality(expr1, expr2)              # 等式驗證
verify_derivative(original, claimed, var)  # 導數驗證
verify_integral(original, claimed, var)    # 積分驗證
verify_solution(equation, solution, var)   # 方程解驗證
check_dimensions(expr, units_map)          # 維度分析
reverse_verify(expr, operation, var)       # 反向驗證
symbolic_equal(expr1, expr2)               # 符號等價
```

### 📋 Agent 會看到的觸發詞

- 「驗證」「verify」「check」
- 「是否正確」「是否相等」
- 「維度」「單位」「dimension」
- 「證明」「prove」

---

## Skill 4: code-generation（程式碼生成）

### 💡 設計理念

推導完成後，需要**實際應用**：
- 生成可執行的 Python 函數
- 生成 LaTeX 用於論文/報告
- 生成完整的 Markdown 報告

⚠️ **重要**：生成的程式碼使用 SymPy，不是 Agent 自己寫的！

### ✅ 能完成的任務

| 任務類型 | 範例 |
|----------|------|
| Python 函數 | 生成可計算的函數，帶完整 docstring |
| LaTeX 公式 | 生成論文級的數學公式排版 |
| 推導報告 | 生成完整的 Markdown 報告（含步驟、驗證） |
| SymPy 腳本 | 生成可重現推導的 Python 腳本 |

### 🔧 使用的工具

```
generate_python_function(name, params, steps, return_vars)
generate_latex_derivation(steps)
generate_derivation_report(title, given, steps, result)
generate_sympy_script(expressions, operations)
```

### 📋 Agent 會看到的觸發詞

- 「生成程式碼」「generate code」
- 「寫成函數」「create function」
- 「LaTeX」「論文」
- 「報告」「report」「文檔」

---

## Skill 5: quick-calculate（快速計算）

### 💡 設計理念

有時候只需要**快速計算**，不需要完整的推導會話：
- 簡化一個表達式
- 求解一個方程
- 快速微分/積分

這些工具是**無狀態**的，直接輸入得到輸出。

### ✅ 能完成的任務

| 任務類型 | 範例 |
|----------|------|
| 簡化 | 「簡化 (x²-1)/(x-1)」 |
| 展開 | 「展開 (a+b)³」 |
| 因式分解 | 「分解 x²-5x+6」 |
| 求解 | 「解 x² + 2x - 3 = 0」 |
| 微分 | 「對 sin(x²) 微分」 |
| 積分 | 「積分 1/(1+x²)」 |
| 代入 | 「把 x=2 代入 x²+3x」 |
| 數值計算 | 「計算 sin(π/4) 的值」 |

### 🔧 使用的工具

```
simplify(expression, method)           # 簡化
expand(expression)                     # 展開
factor(expression)                     # 因式分解
solve(equation, variable, domain)      # 求解
differentiate(expr, var, order)        # 微分
integrate(expr, var, lower, upper)     # 積分
substitute(expr, substitutions)        # 代入
evaluate_numeric(expr, substitutions)  # 數值計算
parse_expression(expr, format)         # 解析表達式
validate_expression(expr, format)      # 驗證表達式
extract_symbols(expression)            # 提取符號
```

### 📋 Agent 會看到的觸發詞

- 「計算」「calculate」「compute」
- 「簡化」「simplify」
- 「求解」「solve」
- 「微分」「積分」

---

## 工具總覽（41 個）

### 推導引擎（17 個）
| 工具 | 說明 |
|------|------|
| `derivation_start` | 開始推導會話 |
| `derivation_resume` | 恢復暫停的會話 |
| `derivation_list_sessions` | 列出所有會話 |
| `derivation_status` | 當前會話狀態 |
| `derivation_load_formula` | 載入公式 |
| `derivation_substitute` | 代入操作 |
| `derivation_simplify` | 簡化 |
| `derivation_solve_for` | 求解變數 |
| `derivation_differentiate` | 微分 |
| `derivation_integrate` | 積分 |
| `derivation_get_steps` | 取得步驟 |
| `derivation_complete` | 完成推導 |
| `derivation_abort` | 放棄推導 |
| `derivation_list_saved` | 列出已存檔 |
| `derivation_get_saved` | 取得已存檔 |
| `derivation_search_saved` | 搜尋已存檔 |
| `derivation_update_saved` | 更新已存檔 |
| `derivation_delete_saved` | 刪除已存檔 |
| `derivation_repository_stats` | 統計資訊 |

### 計算工具（10 個）
| 工具 | 說明 |
|------|------|
| `simplify` | 簡化表達式 |
| `substitute` | 代入數值 |
| `solve` | 求解方程 |
| `differentiate` | 微分 |
| `integrate` | 積分 |
| `expand` | 展開 |
| `factor` | 因式分解 |
| `evaluate_numeric` | 數值計算 |
| `symbolic_equal` | 符號等價 |

### 表達式工具（3 個）
| 工具 | 說明 |
|------|------|
| `parse_expression` | 解析表達式 |
| `validate_expression` | 驗證表達式 |
| `extract_symbols` | 提取符號 |

### 驗證工具（6 個）
| 工具 | 說明 |
|------|------|
| `verify_equality` | 等式驗證 |
| `verify_derivative` | 導數驗證 |
| `verify_integral` | 積分驗證 |
| `verify_solution` | 方程解驗證 |
| `check_dimensions` | 維度分析 |
| `reverse_verify` | 反向驗證 |

### 程式碼生成（4 個）
| 工具 | 說明 |
|------|------|
| `generate_python_function` | 生成 Python 函數 |
| `generate_latex_derivation` | 生成 LaTeX |
| `generate_derivation_report` | 生成報告 |
| `generate_sympy_script` | 生成 SymPy 腳本 |

---

## 🔧 與 SymPy-MCP 的整合

NSForge 專注於**知識管理**，而 SymPy-MCP 提供**底層符號計算**。兩者互補：

### 何時用 NSForge vs SymPy-MCP

| 場景 | 使用工具 | 原因 |
|------|----------|------|
| 簡單公式推導 | NSForge | 有推導會話、自動溯源 |
| **複雜方程式求解** | SymPy-MCP | `solve_algebraically`, `solve_linear_system` |
| **ODE/PDE 求解** | SymPy-MCP | `dsolve_ode`, `pdsolve_pde` |
| **向量場計算** | SymPy-MCP | `calculate_curl`, `calculate_divergence` |
| **矩陣運算** | SymPy-MCP | `matrix_eigenvalues`, `matrix_inverse` |
| **單位系統換算** | SymPy-MCP | `convert_to_units` |
| 公式存檔管理 | NSForge | 有持久化、分類、搜尋 |
| **廣義相對論張量** | SymPy-MCP | `create_predefined_metric`, `calculate_tensor` |

### SymPy-MCP 工具概覽

#### 變數與表達式管理

```python
intro(var_name, pos_assumptions, neg_assumptions)  # 引入符號變數
intro_many(variables)                              # 批量引入變數
introduce_expression(expr_str)                     # 引入表達式
introduce_function(func_name)                      # 引入函數符號（用於 ODE）
print_latex_expression(expr_key)                   # 輸出 LaTeX 格式
reset_state()                                      # 重置所有狀態
```

#### 代數求解

```python
solve_algebraically(expr_key, solve_for_var_name, domain)  # 解單一方程式
solve_linear_system(expr_keys, var_names, domain)          # 解線性聯立方程組
solve_nonlinear_system(expr_keys, var_names, domain)       # 解非線性方程組
```

#### 微積分運算

```python
differentiate_expression(expr_key, var_name, order)                # 微分
integrate_expression(expr_key, var_name, lower_bound, upper_bound) # 積分（定/不定）
simplify_expression(expr_key)                                      # 簡化
substitute_expression(expr_key, var_name, replacement_expr_key)    # 代換
```

#### 微分方程求解

```python
dsolve_ode(expr_key, func_name, hint)  # 解常微分方程 (ODE)
pdsolve_pde(expr_key, func_name, hint) # 解偏微分方程 (PDE)
```

#### 向量場（需先建立座標系）

```python
create_coordinate_system(name, coord_names)             # 建立 3D 座標系
create_vector_field(coord_sys_name, comp_x, y, z)       # 建立向量場
calculate_curl(vector_field_key)                        # 旋度 ∇×F
calculate_divergence(vector_field_key)                  # 散度 ∇·F
calculate_gradient(scalar_field_key)                    # 梯度 ∇f
```

#### 矩陣運算

```python
create_matrix(matrix_data, matrix_var_name)  # 建立矩陣
matrix_determinant(matrix_key)               # 行列式 det(A)
matrix_inverse(matrix_key)                   # 反矩陣 A⁻¹
matrix_eigenvalues(matrix_key)               # 特徵值 λ
matrix_eigenvectors(matrix_key)              # 特徵向量 v
```

#### 單位系統

```python
convert_to_units(expr_key, target_units, unit_system)  # 單位轉換
quantity_simplify_units(expr_key, unit_system)         # 單位簡化
```

**可用單位**：meter, second, kilogram, ampere, kelvin, mole, candela, kilometer, millimeter, gram, joule, newton, pascal, watt, coulomb, volt, ohm, farad, henry, speed_of_light, gravitational_constant, planck, day, year, minute, hour

#### 廣義相對論（需 EinsteinPy）

```python
create_predefined_metric(metric_name)                       # 預定義度規
search_predefined_metrics(query)                            # 搜尋度規
create_custom_metric(components, symbols, config)           # 自訂度規張量
calculate_tensor(metric_key, tensor_type, simplify_result)  # 計算張量
print_latex_tensor(tensor_key)                              # 輸出張量 LaTeX
```

**預定義度規**：Schwarzschild, Minkowski, MinkowskiCartesian, KerrNewman, Kerr, AntiDeSitter, DeSitter, ReissnerNordstrom

**可計算張量**：RICCI_TENSOR, RICCI_SCALAR, EINSTEIN_TENSOR, WEYL_TENSOR, RIEMANN_CURVATURE_TENSOR, STRESS_ENERGY_MOMENTUM_TENSOR

### Domain 參數說明

SymPy 的求解工具支援 domain 參數限制解的範圍：

| Domain      | 說明           | 使用場景                   |
| ----------- | -------------- | -------------------------- |
| `COMPLEX`   | 複數域（預設） | 允許虛數解                 |
| `REAL`      | 實數域         | 只要實數解                 |
| `INTEGERS`  | 整數域         | 只要整數解（如組合問題）   |
| `NATURALS`  | 自然數域       | 只要非負整數解             |

### 典型整合工作流

#### 範例 1：用 SymPy 解 ODE → 存入 NSForge

```python
# 1. 用 SymPy-MCP 求解藥物消除 ODE
intro("t", ["real", "positive"], [])
intro("k", ["real", "positive"], [])
introduce_function("C")
expr = introduce_expression("Derivative(C(t), t) + k*C(t)")
solution = dsolve_ode(expr, "C")
# → C(t) = C1*exp(-k*t)

# 2. 將結果存入 NSForge 公式庫
derivation_start("first_order_elimination")
derivation_load_formula("C_0 * exp(-k*t)", 
    name="First-order elimination",
    source="sympy_derived")
derivation_complete(
    description="一階消除動力學的通解",
    clinical_context="藥物從體內消除的基本模型"
)
```

#### 範例 2：線性系統求解

```python
# 求解聯立方程組：
#   2x + y = 5
#   x - y = 1

intro_many([
    {"var_name": "x", "pos_assumptions": ["real"], "neg_assumptions": []},
    {"var_name": "y", "pos_assumptions": ["real"], "neg_assumptions": []}
])
eq1 = introduce_expression("2*x + y - 5")
eq2 = introduce_expression("x - y - 1")
result = solve_linear_system([eq1, eq2], ["x", "y"], "REAL")
# → x = 2, y = 1
```

#### 範例 3：向量場散度計算

```python
# 計算 F = (x, y, z) 的散度
create_coordinate_system("R")
vector_field = create_vector_field("R", "R.x", "R.y", "R.z")
div_result = calculate_divergence(vector_field)
print_latex_expression(div_result)
# → 3
```

#### 範例 4：單位換算

```python
# 將光速轉換為 km/h
c = introduce_expression("speed_of_light")
result = convert_to_units(c, ["kilometer", "1/hour"])
print_latex_expression(result)
# → 1.08×10⁹ km/h
```

---

## 常見使用場景

### 場景 1：藥動學模型推導

```text
用戶：「推導一個考慮體溫的藥物消除速率模型」

Agent 使用 Skill: derivation-workflow
1. derivation_start("temp_corrected_elimination")
2. derivation_load_formula("C_0 * exp(-k*t)", source="textbook")
3. derivation_load_formula("k_ref * exp(E_a/R * (1/T_ref - 1/T))")
4. derivation_substitute("k", "k_ref * exp(...)")
5. derivation_simplify()
6. check_dimensions(result, {"k": "1/h", "T": "K", ...})
7. derivation_complete(description="...", clinical_context="...")
```

### 場景 2：快速計算

```text
用戶：「sin(x)² + cos(x)² 等於多少？」

Agent 使用 Skill: quick-calculate
1. simplify("sin(x)**2 + cos(x)**2")
→ 回答：1
```

### 場景 3：驗證學生作業

```text
用戶：「驗證 d/dx[ln(x²)] = 2/x 是否正確」

Agent 使用 Skill: verification-suite
1. verify_derivative("ln(x**2)", "2/x", "x")
→ 回答：✅ 正確
```

---

## 下一步

- 閱讀各 Skill 的詳細文件（`.claude/skills/nsforge-*/SKILL.md`）
- 嘗試上述使用場景
- 有問題請參考 `formulas/derivations/` 中的範例
