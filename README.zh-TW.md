# 🔥 Neurosymbolic Forge (NSForge)

> **"Forge" = 透過驗證式推導來創造新公式**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

🌐 [English](README.md) | **繁體中文**

## 🔨 核心概念：「Forge（鍛造）」

**NSForge 不是公式資料庫** — 而是一個**推導工廠**，用來創造新公式。

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🔨 FORGE = 透過推導創造新公式                                              │
│                                                                             │
│   輸入：基礎公式                輸出：新的推導公式                            │
│   ┌─────────────────────┐       ┌─────────────────────────────────────┐    │
│   │ • 一室模型          │       │ 溫度修正消除率模型                   │    │
│   │ • Arrhenius 方程    │  ──→  │ 體脂調整分布容積                     │    │
│   │ • Fick 擴散定律     │       │ 腎功能劑量調整                       │    │
│   │ • ...               │       │ 自訂 PK/PD 模型                      │    │
│   └─────────────────────┘       └─────────────────────────────────────┘    │
│         (來自 sympy-mcp)                    (存放於 NSForge)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ 四大核心能力

| 能力 | 說明 | 工具 |
| ---- | ---- | ---- |
| **推導 (DERIVE)** | 組合基礎公式創造新公式 | `substitute`, `simplify`, `differentiate`, `integrate` |
| **控制 (CONTROL)** | 完整步驟控制：查看、編輯、回滾、插入 | `get_step`, `update_step`, `rollback`, `delete_step`, `insert_note` |
| **驗證 (VERIFY)** | 多種方法確保正確性 | `check_dimensions`, `verify_derivative`, `symbolic_equal` |
| **存儲 (STORE)** | 保存推導公式與完整溯源 | `formulas/derivations/` 儲存庫 |

---

## 🌍 生態系：不重複造輪子

NSForge 與其他 MCP 伺服器協作，而非競爭：

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP 科學計算生態系                                   │
│                          🔢 108 個工具總計 🔢                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  sympy-mcp (32 工具)                                                        │
│  └── 基礎公式：F=ma、PV=nRT、Arrhenius...                                   │
│  └── 物理常數：c、G、h、R...（SciPy CODATA）                                │
│  └── 符號運算引擎（ODE、PDE、矩陣）                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  nsforge-mcp (76 工具) ← 你在這裡                                           │
│  └── 🔨 推導框架：組合、驗證、生成程式碼                                     │
│  └── 📁 推導成果庫：存放創造的公式與溯源資訊                                 │
│  └── ✅ 驗證層：維度分析、逆向驗證                                          │
│  └── 🌐 公式搜尋：Wikidata、BioModels、SciPy 常數                           │
│  └── 🔗 優化橋接：為 USolver 準備公式                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  medical-calc-mcp (75+ 工具)                                                │
│  └── 臨床評分：APACHE、SOFA、GCS、MELD、qSOFA...                            │
│  └── 醫學計算：eGFR、IBW、BSA、MEWS...                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  usolver-mcp（可選協作）                                                     │
│  └── 🎯 為 NSForge 推導的公式找到最佳值                                      │
│  └── 四種求解器：Z3、OR-Tools、CVXPY、HiGHS                                 │
│  └── 用例：藥物劑量優化、電路設計、資源分配                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### NSForge 存放什麼？

| ✅ 屬於 NSForge | ❌ 不屬於（請用其他工具） |
| --------------- | ------------------------ |
| 溫度修正藥物消除率 | 基礎物理公式（sympy-mcp） |
| 體脂調整分布容積 | 物理常數（sympy-mcp） |
| 腎功能劑量調整 | 臨床評分（medical-calc-mcp） |
| 自訂複合 PK/PD 模型 | 教科書公式（參考資料） |

---

## 🚀 NSForge 獨特功能

NSForge 直接調用 SymPy 模組，提供 **SymPy-MCP 沒有的功能**：

| 功能 | SymPy 模組 | 應用場景 | 狀態 |
| ---- | ---------- | -------- | ---- |
| **統計與機率** | `sympy.stats` | PopPK 變異分析、不確定性 | ✅ v0.2.1 |
| **極限與級數** | `sympy.limit`, `sympy.series` | 穩態近似、累積分析 | ✅ v0.2.1 |
| **不等式求解** | `sympy.solvers.inequalities` | 治療窗口計算 | ✅ v0.2.1 |
| **假設查詢** | `sympy.assumptions` | 自動驗證約束 | ✅ v0.2.1 |
| **進階代數** | `sympy.expand/factor/apart...` | 表達式操作 | ✅ v0.2.4 |
| **積分變換** | `sympy.laplace/fourier_transform` | ODE 求解、頻率分析 | ✅ v0.2.4 |
| **推導工作流** | NSForge 獨有 | 步驟追蹤、溯源 | ✅ 可用 |
| **驗證套件** | NSForge 獨有 | 維度分析 | ✅ 可用 |

> 📖 **詳細說明**：參見 [NSForge vs SymPy-MCP 功能比較](docs/nsforge-vs-sympy-mcp.md)。

---

## 🎬 工作流程圖

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   用戶問題                        NSForge 處理流程                          │
│   ════════                        ════════════════                          │
│                                                                            │
│   "藥物在 38°C 發燒病人           1️⃣ 查詢公式知識庫                          │
│    體內的濃度變化？"         ──→     ├─ 一室藥動學模型: C(t) = C₀·e^(-kₑt)   │
│                                     └─ Arrhenius 方程: k(T) = A·e^(-Ea/RT)  │
│                                                                            │
│                                  2️⃣ 組合推導                                │
│                                     ├─ 代入 k(T) 到藥動學模型               │
│                                     └─ 得到溫度修正公式                     │
│                                                                            │
│                                  3️⃣ 符號計算 (SymPy)                        │
│                                     └─ C(t,T) = C₀·exp(-kₑ,ref·t·exp(...)) │
│                                                                            │
│                                  4️⃣ 驗證結果                                │
│                                     ├─ T=37°C 時退化為標準模型 ✓            │
│                                     └─ 維度檢查通過 ✓                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ 步驟控制功能（v0.2.2 新增）

NSForge 現在提供**完整的推導步驟 CRUD 控制**：

```text
┌────────────────────────────────────────────────────────────────────────────┐
│  🎛️ 步驟控制 - 導航與編輯您的推導過程！                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   步驟 1 → 步驟 2 → 步驟 3 → 步驟 4 → 步驟 5 → 步驟 6  (目前)            │
│                        ↑                                                   │
│                        │                                                   │
│   「等等，步驟 3 看起來有問題...」                                           │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │  🔍 查讀    │ derivation_get_step(3) → 查看步驟詳情         │    │
│   │  ✏️ 更新    │ derivation_update_step(3, notes="...") → 修正註記│    │
│   │  ⏪ 回滾    │ derivation_rollback(2) → 返回步驟 2           │    │
│   │  📝 插入    │ derivation_insert_note(2, "...") → 加入說明    │    │
│   │  🗑️ 刪除    │ derivation_delete_step(6) → 刪除最後一步     │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   回滾後：步驟 1 → 步驟 2  (現在的位置)                                    │
│   → 從步驟 2 繼續推導，嘗試不同的路徑！                                    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 步驟 CRUD 工具（5 個新工具）

| 工具 | 操作 | 說明 |
| ---- | ---- | ---- |
| `derivation_get_step` | **查讀** | 取得任一步驟的詳情（表達式、註記、假設） |
| `derivation_update_step` | **更新** | 修改元資料（註記、假設、限制）- 不能改表達式 |
| `derivation_delete_step` | **刪除** | 只能刪除最後一步（安全限制） |
| `derivation_rollback` | **回滾** | ⚡ 跳回任一步驟，刪除後續步驟 |
| `derivation_insert_note` | **插入** | 在任一位置插入說明性註記 |

> 💡 **關鍵概念**：表達式不能直接編輯（會破壞驗證）。使用 `rollback` 返回有效狀態，然後重新推導。

### 使用情境

1. **同儕審查**：「步驟 5 的假設有疑慮」 → `update_step(5, notes="僅在 T<42°C 時有效")`
2. **走錯路**：「應該用積分而不是微分」 → `rollback(3)` → 重新開始
3. **加入說明**：「需要解釋 Arrhenius 代入」 → `insert_note(4, "溫度對酵素動力學的影響...")`
4. **清除錯誤**：「最後一步錯了」 → `delete_step(8)`

---

## 🧠 為什麼需要 NSForge？

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   問題：LLM 直接做數學推導                                                   │
│   ══════════════════════════                                                │
│                                                                             │
│   ❌ 可能算錯（幻覺）      ❌ 每次答案不同      ❌ 無法驗證正確性            │
│                                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│   解決：LLM + NSForge                                                       │
│   ═══════════════════                                                       │
│                                                                             │
│   LLM 負責：                        NSForge 負責：                          │
│   ┌─────────────────────┐          ┌─────────────────────┐                 │
│   │ • 理解用戶問題      │          │ • 存儲驗證過的公式  │                 │
│   │ • 規劃推導策略      │    ──→   │ • 精確符號計算      │                 │
│   │ • 解釋結果          │          │ • 追蹤推導來源      │                 │
│   └─────────────────────┘          │ • 驗證結果正確性    │                 │
│      「理解與規劃」                 └─────────────────────┘                 │
│                                       「計算與驗證」                        │
│                                                                             │
│   ✅ 計算保證正確      ✅ 結果可重現      ✅ 推導可追溯                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 推導成果庫架構

NSForge 存儲**推導公式**，並追蹤完整溯源：

```text
formulas/
└── derivations/                    ← 所有推導公式存放於此
    ├── README.md                   ← 文件
    └── pharmacokinetics/           ← 藥動學模型推導
        ├── temp_corrected_elimination.md   ← 溫度修正消除率
        └── fat_adjusted_vd.md              ← 肥胖調整分布容積
```

### 每個推導成果包含

- LaTeX 數學表達式
- SymPy 可計算形式  
- **推導來源**：組合了哪些基礎公式
- **推導步驟**：實際的推導過程
- **驗證狀態**：維度分析、極限情況驗證
- 臨床情境與使用指引
- YAML 元資料供程式化存取

**推導範例：**

| 推導 | 領域 | 描述 |
| --- | --- | --- |
| [溫度校正消除](formulas/derivations/pharmacokinetics/temp_corrected_elimination.md) | 藥動學 | 一次動力學消除 + Arrhenius 溫度依賴 |
| [NPO 抗生素效應](formulas/derivations/pharmacokinetics/npo_antibiotic_effect.md) | PK/PD | Henderson-Hasselbalch + Emax 模型（pH 依賴性吸收） |
| [溫度校正 Michaelis-Menten](formulas/derivations/pharmacokinetics/temp_corrected_michaelis_menten.md) | 藥動學 | 非線性飽和動力學含溫度效應 |
| [Cisatracurium 多次給藥](formulas/derived/ce30161d.yaml) | 藥動學 | 水解型藥物累積含溫度校正 |
| [生理學 Vd 體組成調整](formulas/derivations/pharmacokinetics/physiological_vd_body_composition.md) | PK/PBPK | PBPK 方法體組成調整分布容積 (logP > 2) |
| [動脈導管波形估算主動脈瓣面積](formulas/derivations/hemodynamics/aortic_valve_area_from_aline.md) | 血流動力學/心臟 | 以 a-line 波形特徵進行床邊 AVA 估算 |

### NPO（禁食）對抗生素效力的影響範例

```yaml
id: npo_antibiotic_effect
name: NPO 對口服抗生素效力的影響
expression: E_0 + (E_max * C_eff^n) / (EC_50^n + C_eff^n)
  where: C_eff = F_base * D / (Vd * (1 + 10^(pH - pKa)))
derived_from:
  - henderson_hasselbalch       # pH 依賴性離子化
  - emax_model                  # 藥效學效應
verified: true
verification_method: sympy_symbolic_substitution
clinical_context: |
  預測 NPO 患者因胃內 pH 值升高導致抗生素效力降低。
  對弱酸性抗生素如 Amoxicillin (pKa=2.4) 特別重要，
  NPO 狀態可使效果降低 >90%。
```

**另請參閱：**[Python 實作範例](examples/npo_antibiotic_analysis.py)含臨床建議。

---

## ✨ 功能特色

| 類別 | 功能 |
| ---- | ---- |
| 🔢 **符號計算** | 微積分、代數、線性代數、ODE/PDE |
| 📖 **公式管理** | 存儲、查詢、版本控制、來源追蹤 |
| 🔄 **推導組合** | 多公式組合、變數替換、條件修改 |
| ✅ **結果驗證** | 維度檢查、邊界條件、逆向驗證 |
| 🐍 **程式碼生成** | 從符號公式生成 Python 計算函數 |

## 📦 安裝

### 環境需求

- **Python 3.12+**
- **uv** (推薦的套件管理器)

```bash
# 使用 uv（推薦）
uv add nsforge-mcp

# 或使用 pip
pip install nsforge-mcp
```

### 從原始碼安裝

```bash
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# 建立環境並安裝依賴
uv sync --all-extras

# 驗證安裝
uv run python -c "import nsforge; print(nsforge.__version__)"
```

## 🚀 快速開始

### 作為 MCP Server

```json
// Claude Desktop 配置 (claude_desktop_config.json)
{
  "mcpServers": {
    "nsforge": {
      "command": "uvx",
      "args": ["nsforge-mcp"]
    }
  }
}
```

### 使用範例

**微積分計算**：

```text
用戶：計算 ∫(x² + 3x)dx 並驗證結果

Agent 呼叫 NSForge：
→ 結果：x³/3 + 3x²/2 + C
→ 驗證：d/dx(x³/3 + 3x²/2) = x² + 3x ✓
→ 步驟：分解積分 → 冪次規則 → 合併
```

**物理推導**：

```text
用戶：理想氣體等溫膨脹做的功？

Agent 呼叫 NSForge：
→ W = nRT ln(V₂/V₁)
→ 推導：PV=nRT → P=nRT/V → W=∫PdV → 積分
```

**演算法分析**：

```text
用戶：分析 T(n) = 2T(n/2) + n

Agent 呼叫 NSForge：
→ T(n) = Θ(n log n)
→ 方法：Master Theorem Case 2
→ 範例：Merge Sort
```

## 📖 文檔

### 設計文檔

- [設計演化：推導框架](docs/design-evolution-derivation-framework.md) - 從模板到可組合推導框架的架構演化
- [領域規劃：音響電路學](docs/domain-audio-circuits.md) - Audio circuits principles 與 modifications
- [原始設計](docs/symbolic-reasoning-mcp-design.md) - 完整架構與 API 設計（參考）

### 實例推導

- [Power Amp 交聯電容設計](docs/examples/power-amp-coupling-capacitor.md) - RC 高通濾波器的完整推導流程
  - 從理想公式到實際考慮（輸出阻抗、ESR、喇叭阻抗曲線）
  - 展示 NSForge "Principles + Modifications" 框架實際應用

### API 參考

- [API 參考](docs/api.md) - MCP 工具詳細說明（待補）

## 🛠️ MCP 工具

NSForge 提供 **76 個 MCP 工具**，分為多個模組：

### 🔥 推導引擎 (31 個工具)

| 工具 | 用途 |
| ---- | ---- |
| `derivation_start` | 開始新的推導會話 |
| `derivation_resume` | 恢復先前的會話 |
| `derivation_status` | 取得當前會話狀態 |
| `derivation_load_formula` | 載入基礎公式 |
| `derivation_substitute` | 變數替換 |
| `derivation_simplify` | 簡化表達式 |
| `derivation_solve_for` | 解出變數 |
| `derivation_differentiate` | 微分表達式 |
| `derivation_integrate` | 積分表達式 |
| `derivation_record_step` | 記錄步驟與備註 (**⚠️ 必須向用戶顯示公式！**) |
| `derivation_add_note` | 加入人類洞見 |
| `derivation_complete` | 完成並儲存 |
| `derivation_abort` | 放棄當前會話 |
| `derivation_list_saved` | 列出已儲存的推導 |
| `derivation_get_saved` | 取得已儲存的推導 |
| `derivation_search_saved` | 搜尋推導 |
| `derivation_update_saved` | 更新元資料 |
| `derivation_delete_saved` | 刪除推導 |
| `derivation_repository_stats` | 儲存庫統計 |
| `derivation_list_sessions` | 列出所有會話 |
| `derivation_get_steps` | 取得推導步驟 |
| `derivation_get_step` | 🆕 取得單一步驟詳情 |
| `derivation_update_step` | 🆕 更新步驟元資料 |
| `derivation_delete_step` | 🆕 刪除最後一步 |
| `derivation_rollback` | 🆕 ⚡ 回滾到任一步驟 |
| `derivation_insert_note` | 🆕 在指定位置插入註記 |

### ✅ 驗證 (6 個工具)

| 工具 | 用途 |
| ---- | ---- |
| `verify_equality` | 驗證兩個表達式是否相等 |
| `verify_derivative` | 透過積分驗證微分 |
| `verify_integral` | 透過微分驗證積分 |
| `verify_solution` | 驗證方程式解 |
| `check_dimensions` | 維度分析 |
| `reverse_verify` | 逆向操作驗證 |

### 🔢 計算 (2 個工具)

| 工具 | 用途 |
| ---- | ---- |
| `evaluate_numeric` | 數值計算 |
| `symbolic_equal` | 符號相等檢查 |

### 📝 表達式 (3 個工具)

| 工具 | 用途 |
| ---- | ---- |
| `parse_expression` | 解析數學表達式 |
| `validate_expression` | 驗證表達式語法 |
| `extract_symbols` | 提取符號與元資料 |

### 💻 程式碼生成 (4 個工具)

| 工具 | 用途 |
| ---- | ---- |
| `generate_python_function` | 生成 Python 函數 |
| `generate_latex_derivation` | 生成 LaTeX 文件 |
| `generate_derivation_report` | 生成 Markdown 報告 |
| `generate_sympy_script` | 生成獨立 SymPy 腳本 |

## 🧠 Agent Skills 架構

NSForge 包含 **18 個預建 Skills**，教導 AI Agent 如何有效使用工具：

### 🔥 NSForge 專用 Skills (5 個)

| Skill | 觸發詞 | 說明 |
| ----- | ------ | ---- |
| `nsforge-derivation-workflow` | derive, 推導, prove | 完整推導工作流含會話管理 |
| `nsforge-formula-management` | list, 公式庫, 找公式 | 查詢、更新、刪除已儲存公式 |
| `nsforge-verification-suite` | verify, check, 維度 | 等式、微分、積分、維度檢查 |
| `nsforge-code-generation` | generate, export, LaTeX | Python 函數、報告、SymPy 腳本 |
| `nsforge-quick-calculate` | calculate, simplify, solve | 快速計算（無需會話） |

### 🔧 通用開發 Skills (13 個)

包含 `git-precommit`、`memory-updater`、`code-reviewer`、`test-generator` 等。

> 📖 **詳細說明**：參見 [NSForge Skills 使用指南](docs/nsforge-skills-guide.md) (588 行完整文件)

### 黃金守則：先用 SymPy-MCP

```text
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: SymPy-MCP 執行計算                                   │
│     intro_many([...]) → introduce_expression(...) →             │
│     substitute/solve/dsolve... → print_latex_expression(...)   │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: NSForge 記錄與儲存                                   │
│     derivation_record_step(...) → derivation_add_note(...) →    │
│     derivation_complete(...)                                    │
└─────────────────────────────────────────────────────────────────┘
```

**分工原則：**

| 任務 | 工具 | 原因 |
|------|------|------|
| 數學計算 | SymPy-MCP | 完整 ODE/PDE/矩陣功能 |
| 公式顯示 | `print_latex_expression` | 每步讓用戶確認 |
| 知識存檔 | NSForge | 溯源追蹤、可搜尋 |
| 維度檢查 | NSForge `check_dimensions` | 物理單位驗證 |

---

## 🏗️ 專案結構

本專案採用 **DDD (Domain-Driven Design)** 架構，Core 與 MCP 分離：

```text
nsforge-mcp/
├── .claude/skills/            # 🧠 Agent Skills (18 個)
│   ├── nsforge-derivation-workflow/  # 核心工作流 Skill
│   ├── nsforge-verification-suite/   # 驗證 Skill
│   └── ...                           # 其他 16 個 Skills
│
├── src/
│   ├── nsforge/               # 🔷 Core Domain (純邏輯，無 MCP 依賴)
│   │   ├── domain/            # Domain Layer
│   │   │   ├── entities.py    #   - 實體 (Expression, Derivation)
│   │   │   ├── value_objects.py #   - 值物件 (MathContext, Result)
│   │   │   └── services.py    #   - 領域服務介面
│   │   ├── application/       # Application Layer
│   │   │   └── use_cases.py   #   - 用例 (Calculate, Derive, Verify)
│   │   └── infrastructure/    # Infrastructure Layer
│   │       ├── sympy_engine.py #   - SymPy 引擎實作
│   │       └── verifier.py    #   - 驗證器實作
│   │
│   └── nsforge_mcp/           # 🔶 MCP Layer (Presentation)
│       ├── server.py          #   - FastMCP Server
│       └── tools/             #   - MCP 工具定義 (36 個工具)
│           ├── derivation.py  #     - 🔥 推導引擎 (26 個工具)
│           ├── verify.py      #     - 驗證 (6 個工具)
│           ├── calculate.py   #     - 計算 (2 個工具)
│           ├── expression.py  #     - 表達式解析 (3 個工具)
│           └── codegen.py     #     - 程式碼生成 (4 個工具)
│
├── formulas/                  # 📁 公式儲存庫
│   ├── derivations/           #   - 人類可讀 Markdown
│   │   ├── pharmacokinetics/  #     - 藥動學推導範例
│   │   └── hemodynamics/      #     - 心臟/血流動力學推導範例
│   └── derived/               #   - YAML 元資料 (自動生成)
│
├── derivation_sessions/       # 💾 會話持久化 (JSON)
├── docs/                      # 📖 文檔
│   └── nsforge-skills-guide.md #   - Skills 使用指南 (588 行)
├── examples/                  # 🐍 Python 範例
│   ├── npo_antibiotic_analysis.py  # 臨床應用
│   ├── physiological_vd_model.py   # PBPK 體組成模型
│   └── aortic_valve_area_aline.py  # 從 a-line 波形估算 AVA
├── tests/                     # 測試
└── pyproject.toml             # 專案配置 (uv/hatch)
```

### 架構優勢

- **Core 可獨立測試**：不依賴 MCP，可單獨使用 `nsforge` 套件
- **MCP 可替換**：未來可支援其他協議（REST, gRPC）
- **依賴反轉**：Domain 定義介面，Infrastructure 實作

## 🧪 開發

```bash
# Clone
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# 建立環境 (uv 會自動使用 Python 3.12+)
uv sync --all-extras

# 執行測試
uv run pytest

# 程式碼檢查
uv run ruff check src/
uv run mypy src/

# 啟動開發 Server
uv run nsforge-mcp
```

## � 與 USolver 協作（可選）

NSForge 專注於**推導領域修正公式**，而 [USolver](https://github.com/sdiehl/usolver) 專注於**找到最佳參數值**。結合使用：

### 協作流程

```text
┌─────────────────────────────────────────────────────────────────┐
│ 步驟 1：NSForge 推導領域修正公式                                │
│ ─────────────────────────────────────────────────────────       │
│ derivation_start() → derivation_substitute() → ...             │
│ 輸出：C(t, dose) = 修正後的表達式                               │
│ 考量：藥物交互作用、體脂、年齡效應...                           │
├─────────────────────────────────────────────────────────────────┤
│ 步驟 2：準備優化                                                │
│ ─────────────────────────────────────────────────────────       │
│ derivation_prepare_for_optimization()                          │
│ 輸出：函數字串、變數、參數、約束條件、USolver 範本              │
├─────────────────────────────────────────────────────────────────┤
│ 步驟 3：USolver 找到最佳值                                      │
│ ─────────────────────────────────────────────────────────       │
│ solve_optimization(function, constraints)                      │
│ 輸出：optimal_dose, objective_value                            │
└─────────────────────────────────────────────────────────────────┘
```

### 為什麼要結合？

| 工具 | 提供什麼 | 例子 |
| ---- | -------- | ---- |
| **NSForge** | 領域知識 → 修正公式 | 考慮藥物交互作用後的濃度公式 |
| **USolver** | 數學優化 → 最佳參數 | 在安全範圍內的最佳劑量 |
| **結合** | 領域智慧 + 數學精確 | **65 歲體脂 30% + midazolam → 35mcg** |

### 設定

1. **安裝 USolver MCP**：參見 [USolver 文檔](https://github.com/sdiehl/usolver#installation)
2. **使用橋接工具**：`derivation_prepare_for_optimization()`
3. **參考協作 Skill**：見 [`.claude/skills/nsforge-usolver-collab/SKILL.md`](.claude/skills/nsforge-usolver-collab/SKILL.md)

---

## 📋 Roadmap

- [x] 設計文檔
- [x] MVP 實作
  - [x] 推導引擎 (26 個工具)
  - [x] SymPy 整合
  - [x] 驗證套件 (6 個工具)
  - [x] MCP Server
- [x] 步驟控制系統 (v0.2.2)
  - [x] 查讀/更新/刪除步驟
  - [x] 回滾到任一點
  - [x] 在任一位置插入註記
- [x] Agent Skills 系統
  - [x] 5 個 NSForge 專用工作流
  - [x] 13 個通用開發 Skills
  - [x] Skills 文檔 (1,110 行)
- [x] 藥動學領域
  - [x] 溫度校正消除率
  - [x] NPO 抗生素效應模型
  - [x] 含溫度效應的 Michaelis-Menten
  - [x] 多次給藥累積
- [x] MCP 協作 (v0.2.3)
  - [x] USolver 優化橋接工具
  - [x] 協作 Skill 文檔
- [ ] 領域擴展
  - [ ] 物理公式庫
  - [ ] 音響電路 (進行中)
  - [ ] 演算法分析
- [ ] 進階功能
  - [ ] Lean4 形式驗證
  - [ ] 自動推導規劃

## 🤝 貢獻

歡迎貢獻！請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 授權

[Apache License 2.0](LICENSE)

---

**NSForge** — 透過驗證式推導鍛造新公式 | *Where Neural Meets Symbolic*
