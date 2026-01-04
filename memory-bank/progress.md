# Progress (Updated: 2026-01-04)

## Done

### SymPy 功能涵蓋分析 (2026-01-04)
- ✅ 完整分析 SymPy-MCP 工具（37 個）
- ✅ 完整分析 NSForge 工具（55 個）
- ✅ 比對遺漏功能（發現 6 類，4 類低優先度）
- ✅ 比對重複功能（12 個無衝突）
- ✅ 檢查錯誤描述（0 錯誤）
- ✅ 生成完整報告 `docs/sympy-coverage-analysis.md`
- ✅ 更新 `docs/nsforge-vs-sympy-mcp.md`

**核心發現**：
- 整體涵蓋率：**85%**（高頻功能 100%）
- 遺漏功能主要為低頻專業模組（geometry, logic）
- 建議新增：expand, factor, trigsimp（中高優先度）

### v0.2.3 USolver 協作橋接 (2026-01-04)
- ✅ Git pull 合併遠端更新（72 檔案，+12,728/-810 行）
- ✅ SymPy-MCP 安裝到 vendor/ 目錄
- ✅ USolver 能力研究（4 種求解器分析）
- ✅ 實作 `derivation_prepare_for_optimization` 工具（~150 行）
  - 自動分類優化變數 vs 參數
  - 生成領域特定約束（劑量範圍、時間非負）
  - 輸出 USolver 範本
- ✅ 創建 NSForge-USolver 協作 Skill（~300 行）
  - 完整工作流程文檔
  - Fentanyl 劑量優化範例
  - 故障排除指南
- ✅ 更新 README.md（英文）+ README.zh-TW.md（中文）
  - 新增 USolver 生態系統條目
  - 新增協作專區（流程圖、比較表）
- ✅ 更新 Memory Bank（activeContext, progress, systemPatterns, decisionLog）

### v0.2.2 步驟控制系統 (2026-01-03)
- ✅ 實作步驟 CRUD 功能 (5 個新工具)
- ✅ 更新 skill 文件反映新功能
- ✅ Ruff 檢查通過 (All checks passed)
- ✅ README/README.zh-TW 大幅更新（步驟控制功能）
- ✅ CHANGELOG 新增 v0.2.2 版本

## Doing

- Git commit + push (v0.2.3 變更)

## Next

- 重啟 MCP 伺服器以載入新工具
- 測試 NSForge-USolver 協作流程
- 考慮其他 MCP 協作機會
