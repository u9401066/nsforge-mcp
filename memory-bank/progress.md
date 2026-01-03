# Progress (Updated: 2026-01-03)

## Done

- 設定 sympy-mcp MCP Server
- 測試 sympy-mcp 工具
- 複雜問題推導測試（安全帶張力）
- 架構設計重大演化：從模板到推導框架
- 記錄設計決策和架構文檔
- Git commit + push 完成
- 創建音響電路學領域規劃文檔
- 完成 Power Amp 交聯電容實例推導
- 整合 AGENTS.md 到 copilot-instructions.md
- 修復 MCP Server 配置（使用 ${workspaceFolder}）
- 設定 sympy-mcp vendor 目錄
- 驗證 sympy-mcp 可用於藥動學推導（溫度校正模型）
- 確認「公式知識庫」設計方向
- 實作推導引擎核心 (DerivationSession + SessionManager)
- 建立 Formula domain model 和 FormulaParser
- 建立 DerivationRepository 用於儲存推導結果
- 新增 SciPy Constants Adapter (物理常數)
- 實作完整的 MCP 推導工具集 (derivation.py)
- 建立 formulas/derivations/ 目錄結構與範例
- 建立藥動學推導範例 (temp_corrected_elimination, fat_adjusted_vd)
- 新增 py.typed 支援類型檢查
- 建立 NSForge Skills 系統 (5 個 Skills)
- 建立 NPO 抗生素效應推導範例 (npo_antibiotic_effect.md)
- 確立「SymPy-MCP 優先」工作流程
- **移除重複的計算工具** (simplify, solve, differentiate 等) - 改用 SymPy-MCP
- **更新 codegen.py** 加入驗證警告
- **更新 nsforge-quick-calculate SKILL** 反映工具移除
- **新增橋接工具** `derivation_record_step`, `derivation_add_note`
- **更新 Skill 和 Instructions** 定義步進式推導工作流
- **強化 5 個推導工具** 加入 notes/assumptions/limitations 參數
- **完成 3 個高質量推導案例**：
  - NPO 抗生素效應（pH 依賴吸收 + Emax 模型）
  - 溫度校正 Michaelis-Menten（非線性藥動學）
  - Cisatracurium 多次給藥溫度模型（水解藥物 + 累積因子）
- **建立完整文檔系統**：
  - 新增 `docs/nsforge-skills-guide.md` (完整 Skills 使用指南)
  - 新增 `.claude/skills/nsforge-verification-suite/SKILL.md`
  - 建立 3 個推導的 Markdown 文檔（formulas/derivations/pharmacokinetics/）
- **建立 Python 應用範例** `examples/npo_antibiotic_analysis.py`
- **完成 README i18n 更新**（EN + zh-TW 同步）：
  - 更新 MCP 工具表（31 個工具，5 個模組）
  - 新增 Agent Skills 架構章節（18 個 Skills）
  - 更新 Project Structure（含 .claude/skills、formulas 等）
  - 更新 Roadmap 反映實際完成狀態
  - 修正 Python badge（3.10+ → 3.12+）
- **🆕 NSForge vs SymPy-MCP 功能分析** (2026-01-03)：
  - 確認 SymPy-MCP 有 37 個工具
  - 發現 5 個 SymPy 重要模組未被暴露：
    1. `sympy.stats` - 統計與機率
    2. `sympy.limit/series/summation` - 極限與級數
    3. `sympy.solvers.inequalities` - 不等式求解
    4. `sympy.assumptions` - 假設查詢
    5. 不確定性傳播
  - 創建文檔：`docs/nsforge-vs-sympy-mcp.md`
  - 更新 README.md 和 README.zh-TW.md 加入獨特功能章節
  - 更新 ROADMAP.md 加入 v0.2.0 進階數學能力計畫
  - 架構決策：**不 Fork SymPy-MCP，直接調用 SymPy**
- **🎯 重新定位 NSForge** (2026-01-03)：
  - 從「記錄器」轉變為「推導助手」
  - 核心價值：Agent 自己寫 SymPy 也能算，但無法做到：
    1. 每步自動驗證
    2. 智慧建議下一步
    3. 符號語義追蹤
    4. 錯誤模式預警
  - 更新 ROADMAP：v0.2.0 改為「主動推導助手」
  - 更新 docs/nsforge-vs-sympy-mcp.md 反映新定位
- **🎉 v0.2.1 完成！10 個新計算工具** (2026-01-03)：
  - SymPy-MCP 沒有的功能，NSForge 現在有了！
  - **極限/級數** (3 個)：
    - `calculate_limit()` - 極限（含 ±∞、方向）
    - `calculate_series()` - Taylor/Laurent/Fourier 展開
    - `calculate_summation()` - 符號求和
  - **不等式** (2 個)：
    - `solve_inequality()` - 單變數不等式
    - `solve_inequality_system()` - 不等式系統
  - **統計** (3 個)：
    - `define_distribution()` - 定義機率分佈
    - `distribution_stats()` - 期望值、變異數等
    - `distribution_probability()` - 機率計算
  - **假設查詢** (2 個)：
    - `query_assumptions()` - 符號屬性查詢
    - `refine_expression()` - 基於假設簡化
  - NSForge 現在總共 **49 個 MCP 工具**！
- **📦 Skills 精簡化** (2026-01-03)：
  - 5 個 SKILL.md 檔案全面重寫
  - 減量 80-92%（平均從 350+ 行 → 60 行）
  - 保留：工具名+參數+簡潔範例
  - 刪除：Agent 回應範例、ASCII 圖、JSON 格式
  - 更新 copilot-instructions.md 加入 86 工具速查表

## Doing

（無進行中任務）

## Next

- **🧠 v0.2.0 主動推導助手**：
  - 自動驗證器 (Auto-Validator)
  - 推導建議器 (Derivation Advisor)
  - 符號語義追蹤 (Symbol Semantics)
  - 錯誤模式檢測 (Error Pattern Detection)
- 實作 search_formulas() 查詢功能
- 增加其他領域推導範例（如電路、流體力學）
- 整合 verify tools 到推導工作流
- 建立 Code Generation 功能測試
- 建立更多臨床應用範例
