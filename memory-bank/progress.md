# Progress (Updated: 2026-01-16)

## Done

### 生理學 Vd 體組成調整模型 (2026-01-16)
- ✅ **PBPK 方法論推導**：Poulin-Theil 組織分布模型
- ✅ **公式驗證**：9 種藥物測試（1/9 符合文獻值）
- ✅ **公式重新定位**：從「通用 Vd 預測」→「體組成調整公式」
- ✅ **完整文檔**：`formulas/derivations/pharmacokinetics/physiological_vd_body_composition.md`
- ✅ **Python 實作**：`examples/physiological_vd_model.py` (PhysiologicalVdModel 類別)
- ✅ **NSForge 會話**：881df03b (physiological_vd_corrected, 5 步驟)
- ✅ **適用範圍**：logP > 2、中性分子、被動擴散

### derivation_show() + Skill 更新 (2026-01-05)
- ✅ **derivation_show() 工具**：顯示當前推導狀態（LaTeX/SymPy/摘要）
- ✅ **Skill 文檔更新**：所有 NSForge Skill 添加「必須向用戶展示公式」提醒
- ✅ **Bug 修復**：DerivationStep 屬性存取、類型標註
- ✅ **Lint 通過**：Ruff + ty 全數通過
- ✅ **工具數量**：76 NSForge + 32 SymPy = 108 總計

### Phase 1+2 工具實作 (2026-01-04)
- ✅ **Phase 1: 10 個進階代數簡化工具**
  - expand, factor, collect, trigsimp, powsimp, radsimp, combsimp
  - apart (部分分式 - 反 Laplace 必備), cancel, together
- ✅ **Phase 2: 4 個積分變換工具**
  - laplace_transform, inverse_laplace_transform
  - fourier_transform, inverse_fourier_transform
- ✅ **測試**: test_phase1_tools.py (10 tests), test_phase2_tools.py (10 tests)
- ✅ **文檔**: phase1/2 報告, 快速參考, 涵蓋率分析更新
- ✅ **SymPy 涵蓋率**: 85% → 92% (+7%)
- ✅ **工具總數**: 36 → 50 (+14)

### 外部公式資料來源調研 (2026-01-04)
- ✅ Wikidata SPARQL (P2534 定義公式) - **已實作**
- ✅ BioModels (SBML 藥動學模型) - **已實作**
- ✅ SciPy constants - **已實作**
- ✅ MCP 工具實作: formula_search, formula_get, formula_categories, formula_pk_models, formula_kinetic_laws, formula_constants
- ✅ 對應 Skill: `nsforge-formula-search`
- ✅ **工具總數**: 50 → 56 (+6)

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

- (無進行中項目)

## Next

- 重啟 MCP 伺服器以載入新工具 (14 個新工具)
- 實作外部公式搜尋功能 (Wikidata adapter)
- 測試 apart + inverse_laplace 多隔室 PK 工作流
