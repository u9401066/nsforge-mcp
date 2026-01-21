# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-15 | 採用憲法-子法層級架構 | 類似 speckit 的規則層級，可擴展且清晰 |
| 2025-12-15 | DDD + DAL 獨立架構 | 業務邏輯與資料存取分離，提高可測試性 |
| 2025-12-15 | Skills 模組化拆分 | 單一職責，可組合使用，易於維護 |
| 2025-12-15 | Memory Bank 與操作綁定 | 確保專案記憶即時更新，不遺漏 |
| 2026-01-01 | Neural-Symbolic 混合架構 | Agent 做推導規劃，SymPy 做精確計算 |
| 2026-01-01 | MVP 暫不含 Lean4 | 技術複雜度高，先用維度檢查 + 反向驗證 |
| 2026-01-01 | Test-Driven Design 方法 | 先定義題目和期望結果，再實作系統 |
| 2026-01-02 | 公式知識庫三層架構 | principles（基礎）→ domain（領域）→ derived（推導），支援狀態追蹤和社群貢獻 |
| 2026-01-02 | sympy-mcp 足以執行推導 | 實測藥動學 ODE 推導成功，NSForge 專注知識管理而非計算引擎 |
| 2026-01-02 | **步進式推導哲學** | 人類推導是一步一步的，每步都可加入新元素變成新公式。不應該一步求解！這是我們與純符號系統最大的不同。 |
| 2026-01-02 | 新增橋接工具 | `derivation_record_step` + `derivation_add_note` 讓人類知識可以在推導過程中隨時注入 |
| 2026-01-02 | **強化 NSForge 推導工具** | 5 個推導工具（substitute, simplify, solve_for, differentiate, integrate）直接支援 notes/assumptions/limitations 參數，每步計算都帶知識記錄 |
| 2026-01-02 | **Handoff 機制** | 新增 `derivation_export_for_sympy` + `derivation_import_from_sympy` + `derivation_handoff_status`，實現 NSForge ↔ SymPy-MCP 無縫轉換。當 NSForge 無法處理（ODE, 矩陣, 極限等）時自動轉給 SymPy-MCP，完成後再導入回來繼續步進式推導。 |
| 2026-01-21 | **v0.2.4 Production-Level 品質標準** | 完成全面品質驗證：類型安全（MyPy 0 errors）、程式碼品質（Ruff）、安全掃描（Bandit）、測試覆蓋（31/31）。確立提交 ToolUniverse PR 的準備標準：文檔完整、類型安全、測試通過。 |
| 2026-01-21 | **ToolUniverse PR 策略** | 經分析確認 NSForge 高度適合 PR 至 ToolUniverse：(1) 互補性高：現有 700+ 工具缺符號推導能力；(2) 不重複：PK/PD 工具僅查詢資料，不推導公式；(3) 不會太重：作為 local MCP tool 獨立運作。定位為「Computational Science Tools」，強調與現有藥學工具的協同作用。 |
| 2026-01-04 | **USolver 協作橋接** | 新增 `derivation_prepare_for_optimization()` 支援與 USolver MCP 協作。NSForge 負責推導領域修正公式，USolver 負責找最佳參數值。採用橋接工具模式：自動分類變數類型、提取參數值、生成領域約束、輸出 USolver 範本。協作帶來價值：領域智慧（藥物交互作用、體脂、年齡）+ 數學精確（Z3/OR-Tools/CVXPY/HiGHS 優化）= 可操作的最佳值。 |

---

## [2026-01-04] USolver 協作橋接：從推導到優化

### 核心問題
> **「NSForge 可以推導出修正後的公式，但如何找到最佳參數值？」**

NSForge 強項：
- 推導領域修正公式
- 注入專業知識（藥物交互作用、體質差異）
- 追蹤推導溯源

USolver 強項：
- 找到最佳參數值
- 四種求解器（Z3, OR-Tools, CVXPY, HiGHS）
- 滿足約束條件

### 解決方案：橋接工具模式

#### `derivation_prepare_for_optimization()`

**功能**：將 NSForge 推導結果轉換為 USolver 可用格式

**自動處理**：
1. **變數分類** - 啟發式識別優化變數 vs 參數
   ```python
   if "dose" in var.lower() or var in ["t", "x", "y"]:
       optimization_vars.append(var)  # 需要找最佳值
   else:
       parameters[var] = extract_from_steps(var)  # 從推導中提取
   ```

2. **約束生成** - 根據變數類型生成領域約束
   - `dose`: 0.001 ≤ dose ≤ 0.100 (mg)
   - `t`: t ≥ 0
   - `concentration`: C ≥ 0

3. **範本輸出** - 提供完整 USolver 使用範例

**返回**：
- `function_str`: 函數字串
- `function_latex`: LaTeX 顯示
- `variables`: 優化變數列表
- `parameters`: 參數與值
- `suggested_constraints`: 建議約束
- `usolver_template`: 可直接使用的範本
- `workflow_next_steps`: 工作流指引

### 完整工作流程

```
Phase 1: NSForge 推導
────────────────────
derivation_start("Fentanyl dosing with modifications")
derivation_substitute("CL", "CL_ref * (1 - 0.3*BF) * (1 - 0.02*age)")
derivation_substitute("V1", "V1_ref * (1 + 0.5*BF)")
...
→ C(t, dose) = dose/V1_adj × exp(-CL_adj/V1_adj × t)

Phase 2: 準備優化
────────────────────
derivation_prepare_for_optimization()
→ 返回:
  - variables: ["dose", "t"]
  - parameters: {"CL_adj": 9.52, "V1_adj": 15.875}
  - constraints: ["dose >= 0.001", "dose <= 0.100", "t >= 0"]
  - USolver template with examples

Phase 3: USolver 求解
────────────────────
[使用 USolver MCP]
solve_optimization(
    function="dose/15.875 * exp(-9.52/15.875 * t)",
    objective="C(t=5) close to 2.5",
    constraints=["dose >= 0.001", "dose <= 0.100"]
)
→ optimal_dose = 0.035 mg (35 mcg)
```

### 範例：Fentanyl 劑量優化

**情境**：65 歲體脂 30% 併用 midazolam 的病人

**NSForge 推導**：
- 體脂修正清除率：-30%
- 年齡修正：-2%/年
- 藥物交互作用（midazolam）：-25%
- → 最終清除率降至 9.52 L/hr

**USolver 優化**：
- 目標：術後 5 分鐘血中濃度 2-3 ng/mL（鎮痛有效）
- 約束：劑量 1-100 mcg
- → 最佳劑量 = 35 mcg

### 價值主張

| 單獨使用 | 協作使用 |
|---------|---------|
| NSForge: 推導公式，但不知道給多少 | NSForge: 考量所有修正因子 |
| USolver: 優化參數，但用標準公式 | USolver: 找到最佳值 |
| 結果: 精確但不貼近現實 | 結果: **35 mcg，同時考量體質、年齡、交互作用** |

### 設計決策

**為何不在 NSForge 內建優化？**
1. 職責分離：NSForge 專注推導，USolver 專注優化
2. 避免重複造輪子：USolver 已有 4 種工業級求解器
3. 擴展性：未來可與其他 MCP 協作（Lean4 驗證、CORE 文獻）

**為何選擇橋接工具模式？**
1. 自動化：減少 Agent 手動格式轉換
2. 領域知識注入：約束條件來自專業判斷
3. 可追溯：完整工作流記錄在 Skill 文檔

### Skill 文檔

創建 `.claude/skills/nsforge-usolver-collab/SKILL.md`（~300 行）：
- 4 階段工作流程
- 3 個典型用例（藥物劑量、電路設計、資源分配）
- 完整 Fentanyl 範例（含數值）
- 故障排除（變數分類錯誤、約束過嚴）
- 求解器選擇指南（線性→HiGHS、組合→OR-Tools）

### 生態系統擴展

NSForge 定位更新：
```
原來: 推導領域修正公式（終點）
現在: 推導領域修正公式（起點） → 為下游工具準備輸入
       ├─ USolver: 優化求解
       ├─ SymPy-MCP: 複雜計算（已有 Handoff）
       └─ 未來: Lean4 形式驗證、CORE 文獻檢索
```

---

## [2026-01-02] Handoff 機制：NSForge ↔ SymPy-MCP 無縫協作

### 核心問題
> **「我們的推導如果無法執行的時候要轉給 SymPy-MCP，但怎麼轉？」**

NSForge 專注於：
- 步進式記錄
- 人類知識注入
- 公式溯源存檔

SymPy-MCP 專長於：
- ODE/PDE 求解
- 矩陣運算
- 極限/級數
- 向量微積分

### 解決方案：三個 Handoff 工具

#### 1. `derivation_export_for_sympy()`

**功能**：導出當前推導狀態給 SymPy-MCP

**返回**：
- `intro_many_command`: 可直接執行的變數定義指令
- `current_expression`: 當前表達式
- `introduce_expression_command`: 可直接執行的表達式載入指令
- `suggested_actions`: 建議的下一步操作

#### 2. `derivation_import_from_sympy()`

**功能**：從 SymPy-MCP 導入計算結果

**參數**：
- `expression`: SymPy-MCP 的結果
- `operation_performed`: 執行了什麼操作
- `sympy_tool_used`: 使用的工具名稱
- `notes`: 人類說明
- `assumptions_used`: 使用的假設
- `limitations`: 結果的限制

**效果**：
- 記錄為新步驟
- 更新當前表達式
- 保持完整的推導歷史

#### 3. `derivation_handoff_status()`

**功能**：顯示能力邊界和 Handoff 選項

**返回**：
- NSForge 能做什麼
- 什麼需要交給 SymPy-MCP
- 當前推導狀態
- Handoff 流程指引

### 工作流程

```
NSForge: derivation_start → ... → 遇到 ODE
                ↓
NSForge: derivation_export_for_sympy()
                ↓
        → intro_many_command
        → current_expression
                ↓
SymPy-MCP: intro_many([...], 'real positive')
SymPy-MCP: introduce_expression("...")
SymPy-MCP: dsolve_ode(...)
SymPy-MCP: print_latex_expression(...)
                ↓
NSForge: derivation_import_from_sympy(
           expression="...",
           operation_performed="Solved ODE",
           sympy_tool_used="dsolve_ode",
           notes="...",
           assumptions_used=[...],
           limitations=[...]
         )
                ↓
NSForge: 繼續步進式推導...
```

### 價值
1. **能力互補** - NSForge 知識管理 + SymPy-MCP 複雜計算
2. **無縫銜接** - 不需要手動轉換格式
3. **保持追蹤** - 即使轉給 SymPy-MCP，步驟仍然完整記錄
4. **知識注入** - import 時可以加入 notes、assumptions、limitations

### 設計原則
- **NSForge 是主控** - 推導會話始終在 NSForge
- **SymPy-MCP 是執行器** - 只負責計算，不管理狀態
- **Agent 做橋接** - 根據需要呼叫 export/import
- **人類知識不丟失** - 每次 import 都可以加入說明

---

## [2026-01-02] 步進式推導哲學 (Step-by-Step Derivation Philosophy)

### 核心洞察
> **「人類的推導是一個步驟一個步驟來的！」**

這意味著：
1. **不是一步求解** - 不能給起點終點就自動跑完
2. **每步都可加入新元素** - 推導過程中發現的洞見可以即時注入
3. **變成新公式** - 加入修正後就是一個更穩定、不一樣的新公式

### 與純符號系統的差異

| 純符號系統 | NSForge 步進式推導 |
|-----------|-------------------|
| 輸入 → 自動求解 → 輸出 | 輸入 → 步驟1 → 人類洞見 → 步驟2 → 修正 → ... |
| 公式是靜態的 | 公式是演化的 |
| 人類只看結果 | 人類參與過程 |
| 無法加入領域知識 | 每步都可注入專業判斷 |

### 實際例子：酵素活性與溫度

傳統做法（一步求解）：
```
給定: MM equation + Arrhenius
求: V_max(T)
結果: V_max_ref * exp(E_a/R * (1/T_ref - 1/T))
```

步進式推導：
```
Step 1: 載入 Michaelis-Menten
Step 2: 代入 Arrhenius for V_max
        📝 Note: 假設 V_max 遵循 Arrhenius，但酵素在高溫會變性
Step 3: 加入 Hill-type 校正因子
        📝 Note: γ(T) = 1 / (1 + (T/T_denat)^n) 描述變性行為
Step 4: 簡化得到最終形式
        → 這是一個「新公式」，比原始 Arrhenius 更適用於生物系統！
```

### 設計決定

1. **保留計算步驟分離** - 每個操作都是獨立步驟
2. **新增橋接工具** - `derivation_record_step`, `derivation_add_note`
3. **notes 是一等公民** - 人類知識與數學推導同等重要
4. **產生的是「演化過的公式」** - 不只是數學變換，而是加入了領域知識的新公式

### 價值主張

NSForge 不只是「符號計算的 wrapper」，而是：
> **「讓人類專家與符號系統協作，產生經過專業判斷的推導結果」**

---

## [2026-01-02] 公式知識庫設計

### 背景
討論如何實作「Principle + Modifications → Derived Form」框架。

### 關鍵發現
實測 sympy-mcp 可以：
- 解藥動學 ODE（一室模型）
- 代入修正公式（體脂肪校正、溫度校正）
- 從 Arrhenius 方程推導溫度依賴藥動學模型

**結論**：不需要額外的推導引擎，sympy-mcp 已足夠。

### 決定
採用「公式知識庫」架構：

```
formulas/
├── principles/     # 基礎物理定律（不變）
├── domain/         # 領域公式（有文獻）
└── derived/        # 推導公式（可增長）
    ├── proposed/   # 待檢驗
    └── verified/   # 已檢驗
```

### 公式 YAML 格式包含
- 公式（LaTeX + SymPy）
- 推導來源（可追溯）
- 狀態（proposed/verified/deprecated）
- 文獻引用
- 使用限制
- 驗證狀態

### 價值
- 避免重造輪子
- 可追溯推導來源
- 品質分級（proposed vs verified）
- 知識庫可持續增長

---

## [2026-01-01] Neural-Symbolic 混合架構

### 背景
需要讓 AI Agent 能進行可驗證、可重現的符號推導。

### 問題分析
- Agent 可以寫公式（表達沒問題）
- Agent 直接輸出推導（無法保證正確）
- SymPy 執行計算（100% 正確）
- SymPy 不知道「下一步該做什麼」

### Gap 識別
**推導規劃**是核心缺口：
- SymPy 是執行器，不是規劃器
- Lean4 可驗證，但不會自動規劃
- LLM 可規劃，但可能出錯

### 決定
採用 Neural-Symbolic 混合方案：
1. Agent + 人：做推導規劃（選策略、決步驟）
2. MCP Server：檢查步驟合理性
3. SymPy：執行每一步計算
4. Verifier：維度檢查 + 反向驗證

### 理由
- 發揮 Agent 的靈活性
- 保留 SymPy 的精確性
- 可驗證可追蹤
- 技術複雜度可控

---

## [2026-01-01] MVP 定義

### 決定
**MVP 必做**：
1. DSL Parser - 解析推導腳本
2. Step Executor - SymPy 執行
3. Basic Verifier - 維度 + 反向驗證
4. Formula KB - 3-5 領域核心公式
5. MCP Wrapper - Agent 可呼叫工具

**暫不實作**：
- Lean4 形式驗證
- 自動推導規劃
- 完整公式庫

### 理由
- 先驗證核心概念
- 從具體題目擴充公式庫
- 形式驗證可後續加入

---

## [2026-01-01] Test-Driven Design 方法

### 決定
採用 Test-Driven 方法：
1. 先定義具體題目（5 個 Level）
2. 定義期望的 DSL 腳本和輸出
3. 選 2-3 題做 prototype
4. 從 prototype 回饋修正設計

### 選定的測試題目
- Level 1: 單步 SymPy（微分、積分）
- Level 2: 單公式（理想氣體、運動學）
- Level 3: 多步推導（RC 濾波器、碰撞力學）
- Level 3.5: 含 ODE（藥動學）
- Level 4: 交互式（參數不足）
- Level 5: Lean4-style tactics
| 2026-01-01 | 架構演化：從「完整推導模板」到「可組合推導框架」 | 用戶關鍵洞察：「公式是理想化的（如 F=ma），但現實問題需要修正（加入摩擦力）」。這意味著我們不可能窮舉所有問題的完整模板。正確的做法是：
1. 提供基礎原理（principles）- 由 Lean4 證明的理想化定理
2. 提供修正項庫（modifications）- friction, drag, heat_loss 等
3. 提供推導引擎 - Agent 根據問題特徵動態組合
4. 提供常見變體 - 社群貢獻的 derived_forms

這樣既保證理論正確性（Lean4），又能應對無限可能的實際問題。 |
