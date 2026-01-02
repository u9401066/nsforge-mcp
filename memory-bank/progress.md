# Progress (Updated: 2026-01-02)

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

## Doing

- 準備 Git commit + push（包含所有推導案例和文檔）

## Next

- 實作 search_formulas() 查詢功能
- 增加其他領域推導範例（如電路、流體力學）
- 整合 verify tools 到推導工作流
- 建立 Code Generation 功能測試
- 建立更多臨床應用範例
