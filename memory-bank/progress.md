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

## Doing

- 測試與驗證推導引擎
- 準備 Git commit + push

## Next

- 實作 search_formulas() 查詢功能
- 增加更多藥動學推導範例
- 整合 verify tools 到推導工作流
- 建立 Code Generation 功能測試
