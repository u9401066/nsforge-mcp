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
