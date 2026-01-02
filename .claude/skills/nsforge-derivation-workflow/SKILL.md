---
name: nsforge-derivation-workflow
description: 完整的數學推導工作流。建立會話 → 載入公式 → 推導操作 → 驗證 → 存檔。觸發詞：推導, derive, 從...推導, 組合公式, 建立模型, prove。
---

# NSForge 步進式推導工作流 Skill

## 🎯 核心哲學：步進式推導

> **「人類的推導是一個步驟一個步驟來的！」**
>
> 每步都可加入新元素 → 變成更穩定、不一樣的**新公式**！

### ❌ 不是這樣（一步求解）

```
給定: MM equation + Arrhenius
求: 自動求解
結果: ??? (人類無法介入)
```

### ✅ 而是這樣（步進式）

```
Step 1: 載入 Michaelis-Menten
Step 2: 代入 Arrhenius
        📝 Note: 假設 V_max 遵循 Arrhenius，但酵素在高溫會變性
Step 3: 加入 Hill-type 校正因子  ← 人類洞見注入！
        📝 Note: γ(T) = 1 / (1 + (T/T_denat)^n)
Step 4: 簡化
        → 這是一個「新公式」！
```

---

## ⚠️ 重要：雙 MCP 協作工作流

> **「SymPy-MCP 做計算，NSForge 記錄知識！」**

### 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: NSForge 開始會話                                  │
│  ─────────────────────────────────────────────────────────  │
│  derivation_start(name="...", description="...")           │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: SymPy-MCP 計算 + NSForge 記錄（循環）             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─ 2a. SymPy-MCP 執行計算 ─────────────────────────────┐  │
│  │  intro_many([...])              # 定義變數           │  │
│  │  introduce_expression(...)      # 建立表達式         │  │
│  │  substitute_expression(...)     # 代入               │  │
│  │  print_latex_expression(...)    # 顯示結果           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌─ 2b. NSForge 記錄這一步 ─────────────────────────────┐  │
│  │  derivation_record_step(        # 🆕 橋接工具        │  │
│  │    expression="...",            # SymPy 結果         │  │
│  │    description="代入 Arrhenius",                     │  │
│  │    notes="酵素在高溫會變性..."  # ⚡ 人類知識！      │  │
│  │  )                                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌─ 2c. NSForge 加入額外說明（可選）────────────────────┐  │
│  │  derivation_add_note(           # 🆕 橋接工具        │  │
│  │    note="建議加入校正因子 γ(T)",                     │  │
│  │    note_type="correction"       # ⚡ 修正建議        │  │
│  │  )                                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌─ 重複 2a-2c 直到完成 ────────────────────────────────┐  │
│  │  → 每一步都可加入新的人類洞見                        │  │
│  │  → 最終得到的是「演化過的新公式」                    │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: NSForge 完成存檔                                  │
│  ─────────────────────────────────────────────────────────  │
│  derivation_complete(                                       │
│    description="...",                                       │
│    assumptions=[...],                                       │
│    limitations=[...],      # Notes 會自動整合               │
│    references=[...]                                         │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Handoff 機制：NSForge ↔ SymPy-MCP

> **當 NSForge 做不到的時候，自動轉給 SymPy-MCP！**

### 什麼時候需要 Handoff？

| 需求 | NSForge | SymPy-MCP |
|------|---------|-----------|
| 基本代入/簡化 | ✅ | ✅ |
| 單變數求解 | ✅ | ✅ |
| 微分/積分 | ✅ | ✅ |
| **解 ODE/PDE** | ❌ | ✅ |
| **矩陣運算** | ❌ | ✅ |
| **線性方程組** | ❌ | ✅ |
| **極限/級數** | ❌ | ✅ |
| **向量微積分** | ❌ | ✅ |

### Handoff 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  NSForge 遇到無法處理的操作                                  │
│  例如：需要解 ODE、矩陣運算、極限等                          │
├─────────────────────────────────────────────────────────────┤
│  Step 1: 導出給 SymPy-MCP                                   │
│  ─────────────────────────────────────────────────────────  │
│  derivation_export_for_sympy()                              │
│    → 返回：                                                  │
│      - intro_many_command: "intro_many([...], 'real positive')"
│      - current_expression: "k*exp(-E/(R*T))*C/(K_m + C)"    │
│      - introduce_expression_command: ...                     │
├─────────────────────────────────────────────────────────────┤
│  Step 2: SymPy-MCP 執行複雜操作                              │
│  ─────────────────────────────────────────────────────────  │
│  [SymPy-MCP] intro_many([...], 'real positive')             │
│  [SymPy-MCP] introduce_expression("...", "current")         │
│  [SymPy-MCP] dsolve_ode(...) / solve_linear_system(...)     │
│  [SymPy-MCP] print_latex_expression(...)                    │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 導入回 NSForge                                      │
│  ─────────────────────────────────────────────────────────  │
│  derivation_import_from_sympy(                              │
│    expression="C1*exp(k*t)",                                │
│    operation_performed="Solved first-order ODE",            │
│    sympy_tool_used="dsolve_ode",                            │
│    notes="General solution, C1 is integration constant",    │
│    assumptions_used=["k is real positive"],                 │
│    limitations=["Needs initial condition for C1"]           │
│  )                                                          │
├─────────────────────────────────────────────────────────────┤
│  回到 NSForge 繼續步進式推導！                               │
│  可以繼續 derivation_substitute(), derivation_add_note()... │
└─────────────────────────────────────────────────────────────┘
```

### Handoff 工具

| 工具 | 方向 | 用途 |
|------|------|------|
| `derivation_export_for_sympy` | NSForge → SymPy-MCP | 導出當前狀態 |
| `derivation_import_from_sympy` | SymPy-MCP → NSForge | 導入計算結果 |
| `derivation_handoff_status` | - | 查看能力邊界 |

### 範例：解 ODE 並繼續推導

```python
# 1. NSForge 推導中...遇到需要解 ODE
derivation_start(name="drug_elimination", description="...")
# ... 幾步後需要解 dC/dt = -k*C ...

# 2. 導出給 SymPy-MCP
result = derivation_export_for_sympy()
# → intro_many_command: "intro_many(['k', 'C', 't'], 'real positive')"
# → current_expression: "-k*C"

# 3. SymPy-MCP 解 ODE
[SymPy-MCP] intro_many(['k', 'C', 't', 'C0'], 'real positive')
[SymPy-MCP] dsolve_ode("diff(C, t) + k*C", "C", "t")
[SymPy-MCP] print_latex_expression(...)
# → C(t) = C1*exp(-k*t)

# 4. 導入回 NSForge
derivation_import_from_sympy(
    expression="C0*exp(-k*t)",  # 已代入初始條件 C(0)=C0
    operation_performed="Solved first-order elimination ODE",
    sympy_tool_used="dsolve_ode",
    notes="Applied initial condition C(0) = C0 to determine constant",
    assumptions_used=["First-order kinetics", "k is constant"],
    limitations=["Assumes constant elimination rate", "Single compartment model"]
)

# 5. 繼續 NSForge 步進式推導
derivation_add_note(
    note="可以加入溫度校正：k → k_ref * exp(-Ea/R * (1/T - 1/T_ref))",
    note_type="correction"
)
# ...
derivation_complete(...)
```

---

## 🔧 核心工具

### 階段 1：開始會話

| 工具 | 用途 |
|------|------|
| `derivation_start` | 開始新推導會話 |

### 階段 2：計算 + 記錄（循環）

| MCP | 工具 | 用途 |
|-----|------|------|
| **SymPy-MCP** | `intro_many` | 定義變數 |
| **SymPy-MCP** | `introduce_expression` | 建立表達式 |
| **SymPy-MCP** | `substitute_expression` | 代入 |
| **SymPy-MCP** | `solve_algebraically` | 求解 |
| **SymPy-MCP** | `print_latex_expression` | ⚠️ 必須顯示給用戶！ |
| **NSForge** | `derivation_record_step` | 🆕 記錄 SymPy 結果 + notes |
| **NSForge** | `derivation_add_note` | 🆕 加入人類知識 |

### 階段 3：完成

| 工具 | 用途 |
|------|------|
| `derivation_complete` | 存檔 + 元資料 |

---

## 🆕 橋接工具詳解

### derivation_record_step

**目的**：把 SymPy-MCP 計算結果記錄到 NSForge，並加入人類知識

```python
derivation_record_step(
    expression="C*V_max_ref*exp(E_a*(1/T_ref - 1/T)/R)/(C + K_m)",  # SymPy 結果
    description="Substituted Arrhenius equation for Vmax",
    notes="假設 V_max 遵循 Arrhenius，但酵素在 >42°C 會變性，此時模型不適用",
    source="sympy_mcp"
)
```

**參數**：
- `expression`: SymPy 格式表達式
- `description`: 這步做了什麼
- `notes`: ⚡ **人類知識**（假設、警告、洞見）
- `source`: 來源標記 (`sympy_mcp`, `manual`, `literature`)

### derivation_add_note

**目的**：純粹加入說明，不改變數學表達式

```python
derivation_add_note(
    note="酵素活性 vs 溫度不是線性的！建議加入 Hill-type 校正因子",
    note_type="correction",
    related_variables=["V_max", "T"]
)
```

**note_type 類型**：

| 類型 | Emoji | 用途 |
|------|-------|------|
| `assumption` | 📋 | 假設條件 |
| `limitation` | ⚠️ | 限制/警告 |
| `observation` | 💡 | 觀察/洞見 |
| `correction` | 🔧 | 修正建議 |
| `clinical` | 🏥 | 臨床意義 |
| `physical` | 🔬 | 物理意義 |

---

## 完整範例：溫度校正 Michaelis-Menten

用戶問：「推導考慮溫度影響的 Michaelis-Menten 方程，但要考慮酵素變性」

### Phase 1: NSForge 開始

```python
# NSForge
derivation_start(
    name="temp_corrected_mm_with_denaturation",
    description="Michaelis-Menten with temperature correction and enzyme denaturation"
)
```

### Phase 2a: SymPy-MCP 計算 (Step 1)

```python
# SymPy-MCP
intro_many([
    {"name": "C", "assumptions": ["positive"]},
    {"name": "V_max", "assumptions": ["positive"]},
    {"name": "K_m", "assumptions": ["positive"]},
    {"name": "T", "assumptions": ["positive"]},
    {"name": "V_max_ref", "assumptions": ["positive"]},
    {"name": "E_a", "assumptions": ["positive"]},
    {"name": "R", "assumptions": ["positive"]},
    {"name": "T_ref", "assumptions": ["positive"]}
])

mm = introduce_expression("V_max * C / (K_m + C)")
print_latex_expression(mm)  # 顯示給用戶
```

### Phase 2b: NSForge 記錄 (Step 1)

```python
# NSForge
derivation_record_step(
    expression="V_max * C / (K_m + C)",
    description="Base Michaelis-Menten equation",
    notes="這是理想狀態下的酵素動力學，假設溫度恆定",
    source="sympy_mcp"
)
```

### Phase 2a: SymPy-MCP 計算 (Step 2)

```python
# SymPy-MCP
arrhenius = introduce_expression("V_max_ref * exp(E_a/R * (1/T_ref - 1/T))")
mm_temp = substitute_expression(mm, "V_max", arrhenius)
print_latex_expression(mm_temp)  # 顯示給用戶
```

### Phase 2b: NSForge 記錄 (Step 2)

```python
# NSForge
derivation_record_step(
    expression="V_max_ref * exp(E_a/R * (1/T_ref - 1/T)) * C / (K_m + C)",
    description="Substituted Arrhenius for V_max",
    notes="⚠️ Arrhenius 假設酵素活性隨溫度單調增加，但實際上酵素會變性！",
    source="sympy_mcp"
)

derivation_add_note(
    note="酵素在高溫 (>42°C) 會變性，活性急劇下降。需要加入校正因子 γ(T)。",
    note_type="limitation",
    related_variables=["V_max", "T"]
)
```

### Phase 2a: SymPy-MCP 計算 (Step 3) - 加入校正因子！

```python
# SymPy-MCP
intro_many([
    {"name": "gamma", "assumptions": ["positive"]},  # 校正因子
    {"name": "T_denat", "assumptions": ["positive"]},  # 變性溫度
    {"name": "n", "assumptions": ["positive"]}  # Hill 係數
])

gamma_expr = introduce_expression("1 / (1 + (T/T_denat)**n)")
mm_corrected = introduce_expression(
    "gamma * V_max_ref * exp(E_a/R * (1/T_ref - 1/T)) * C / (K_m + C)"
)
print_latex_expression(mm_corrected)  # 顯示給用戶
```

### Phase 2b: NSForge 記錄 (Step 3)

```python
# NSForge
derivation_record_step(
    expression="1/(1 + (T/T_denat)**n) * V_max_ref * exp(E_a/R * (1/T_ref - 1/T)) * C / (K_m + C)",
    description="Added Hill-type denaturation correction factor γ(T)",
    notes="γ(T) 描述酵素變性行為。當 T << T_denat 時 γ≈1；當 T >> T_denat 時 γ→0。"
          "Hill 係數 n 控制過渡的陡峭度（蛋白質變性通常 n=10-20）",
    source="sympy_mcp"
)

derivation_add_note(
    note="這個修正後的公式在 32-50°C 範圍內都有效，比原始 Arrhenius 更適用於生物系統",
    note_type="observation"
)
```

### Phase 3: NSForge 完成

```python
# NSForge
derivation_complete(
    description="Temperature-corrected Michaelis-Menten with enzyme denaturation. "
                "Combines Arrhenius temperature dependence with Hill-type denaturation correction.",
    clinical_context="Use for predicting enzyme activity across a wide temperature range, "
                     "especially in hypothermia (32°C) to hyperthermia (42°C) conditions.",
    assumptions=[
        "Michaelis-Menten kinetics",
        "Arrhenius temperature dependence for activation",
        "Cooperative denaturation (Hill model)"
    ],
    limitations=[
        "Requires estimation of T_denat and n for specific enzyme",
        "Does not account for irreversible denaturation",
        "May not apply to thermophilic enzymes"
    ],
    references=[
        "Michaelis & Menten, 1913",
        "Arrhenius equation",
        "Daniel et al., Biochem J, 2010 - Enzyme thermal stability"
    ],
    tags=["enzyme", "temperature", "michaelis-menten", "denaturation", "arrhenius"]
)
```

---

## 分工原則

| 任務 | 工具 | 原因 |
|------|------|------|
| **變數定義** | SymPy-MCP `intro_many` | 支援 assumptions |
| **計算求解** | SymPy-MCP | ODE、矩陣、單位 |
| **顯示公式** | SymPy-MCP `print_latex_expression` | ⚠️ 讓用戶確認！ |
| **記錄步驟** | NSForge `derivation_record_step` | 含人類知識 |
| **加入說明** | NSForge `derivation_add_note` | 純文字洞見 |
| **知識存檔** | NSForge `derivation_complete` | 溯源、分類、搜尋 |

---

## ❌ 禁止行為

1. **不要跳過 `print_latex_expression`** - 用戶需要看到並確認每步結果
2. **不要一步求解** - 每步都要記錄，每步都可能加入新洞見
3. **不要忽略人類說明** - notes 是知識的核心部分
4. **不要直接用 NSForge 的計算工具** - 用 SymPy-MCP 計算

---

## 觸發條件

當用戶說：
- 「推導」「derive」「derivation」
- 「從 X 推導 Y」
- 「組合公式」「combine formulas」
- 「建立模型」「create model」
- 「一步一步推導」
- 「加入...考慮」「加入...修正」

---

## 相關 Skills

- `nsforge-verification-suite`: 驗證工具
- `nsforge-formula-management`: 管理已存檔的公式
- `nsforge-code-generation`: 生成 Python 函數或報告
