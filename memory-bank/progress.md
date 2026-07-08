# Progress (Updated: 2026-07-08)

## Done
### 🧩 Agent harness 完整化：自描述 + 自守衛 (2026-07-08)
- ✅ **Stage A** manifest v2（`gen_capabilities.py`）：除工具外自描述 version／north_star／module_summaries／live gate 清單（匯自 `check.py`）／commands——單一機讀契約（61ffdcd）
- ✅ **Stage B** `meta` 模組（`tools/meta.py`）：`nsforge_health`＋`nsforge_manifest` runtime 自省；工具 89→91、雙語 README/tools-reference 同步（ad458b8）
- ✅ **Stage C** 第 11 gate `harness`（`scripts/harness_selfcheck.py`）：版本單一真相、manifest／gate 對齊、工具自描述品質、AGENTS.md gate 漂移；harness 守衛自身；AGENTS/.clinerules 同步（2889c15）
- ✅ harness 10→11 全綠；CI 本就跑同一 harness
### 📖 README 視覺化雙語大改版 + GitHub metadata (2026-07-08)
- ✅ 建 2 個自含式 SVG（`docs/images/nsforge-hero.svg`、`reification-ladder.svg`）＋ 6 個 Mermaid（生態系／SymPy-first 工作流／explore／步進控制 stateDiagram，中英各 6）取代 ASCII art
- ✅ 龐大工具表移至 `docs/tools-reference.md`（89 工具、10 模組單一真相）；README 精簡化、補 task/suggest/music 模組與實體化階梯敘事；工具數校正 75/87→89
- ✅ 中英 README 對照同步（各 15 章節、6 Mermaid、無殘留 HTML 實體）；GitHub 描述更新、新增 16 topics；commits 9b44378/58d3c05
### 🧩 infra 層純程式碼收尾：DI 組合根 + process-pool timeout (2026-07-08)
- ✅ `nsforge_mcp/composition.py`：組合根（frozen `Services`：engine/verifier/session_manager/repository）+ `build_services()` + `get_services()` 雙重檢查鎖，object graph「建一次、注入」的單一組裝點
- ✅ `task.py` 改用 `get_services()`（不再每次 `SymPyEngine()`/`BasicVerifier()`）；`derivation.py` 的 `_get_manager` + 新 `_get_repository` 全走組合根，消除自有 `_manager` 全域與 7 處重複 `Path("formulas")`
- ✅ `infrastructure/timeout.py` `run_with_timeout`（spawn 子行程硬牆鐘逾時，超時 terminate→`ComputationTimeout`；PEP 695 泛型）；`task_run`/`task_explore` 加 opt-in `timeout_s`（子行程執行、可真殺失控推導）
- ✅ tests/test_composition.py（單例/埠/共用 store 身分）+ tests/test_timeout.py（回值/殺超時/WorkerError/非正逾時）；Explore 子代理複審：無孤兒、無重造輪；harness 10/10
### 🌳 階段 6：explore mode (2026-07-08)
- ✅ `application/explorer.py` `Explorer` + `task_explore` 工具：DTS 的 `alternatives` 視為分支，對 base＋每分支各跑完整 L3 迴圈，回傳全部候選
- ✅ 依「verified > 通過神諭數 > 較簡潔」排序，每候選帶 acceptance＋provenance；工具 88→89、manifest 重生
- ✅ tests/test_explorer.py（全分支探索、驗證者排前、皆 provenance 完整）；harness 10/10。路線圖階段 1-6 全部落地
### 🔑 (3) 全量 session_id 化（多 agent Tier 0） (2026-07-08)
- ✅ 22 個有狀態 derivation 工具皆加 `session_id: str = ""`（向後相容）+ `_resolve_session(session_id)` helper（給 id 查該會話、否則退回 current）
- ✅ complete/abort 只在完成者正是 current 時才清 current（不清別 agent 的）；manifest 重生
- ✅ tests/test_session_id.py（B 為 current 時用 id 操作 A 互不干擾）；harness 10/10。配合先前 SessionManager 並發鎖，為租戶隔離銖路（owner 身分需 transport/auth 層）
### 🧬 階段 5：provenance ledger 強制 (2026-07-08)
- ✅ `domain/provenance.py`（ProvenanceEntry/ProvenanceLedger，純）：每推導帶「出生證明」帳本（base 公式=input、每步=工具、最終=engine）
- ✅ orchestrator `_build_ledger` + 強制：codegen **只在 provenance 完整時才產碼**，否則 ALGORITHM PLANNED「refused: 無溯源」；`task_run` 輸出 provenance
- ✅ `scripts/provenance.py` 成 `provenance` gate → harness 9→10（每 benchmark 推導都須可溯源，鎖住「AI 不徒手生」不變量）
- ✅ tests/test_provenance.py；AGENTS/.clinerules gate 清單加 provenance
### 🧹 品質清理：孤兒盤點 + 消除重造輪子 (2026-07-08)
- ✅ 用 Explore subagent 全面盤點：**幾乎無孤兒死碼**（唯 `FormulaRepository` ABC 是預留 port，保留）
- ✅ **集中 SymPy 解析**（`infrastructure/parsing.py`）：3 份 `_parse_safe`→1；順帶修復 calculate/simplify **繞過 DoS 護欄** 的安全漏洞（含 calculate 另 2 處直接 parse_expr）；`TRANSFORMATIONS` 7→3（commit 5de5ac1）
- ✅ **集中 `SYMPY_RESERVED_NAMES`**（`domain/safe_parse.py`）：3 份不一致（23 vs 11 名）→1；修正 bench/suggester 過去漏掉 cot/sinh 等的分類 bug（commit 1745e1e）
- 🔜 選配：symbol_context 邏輯（orchestrator vs bench）、unicode preprocess 下沉 domain### � 階段 4：自我修正環（critic-retry） (2026-07-08)
- ✅ `run()` 成重試迴圈：base 推導未通過 acceptance → 依 DTS `alternatives` 逐一組合重試 → 取第一個通過者
- ✅ DTS 加 `alternatives: list[Modification]`；`TaskRunResult` 加 `attempts`（label/derived/verified）；`task_run` 輸出 attempts
- ✅ tests/test_self_correction.py（base→gain_2 失敗→gain_5 通過）；harness 9/9；至此階段 1-4 全部落地、探索迴圈閉環
### �🛡️ 多 agent 服務化硬化：安全 parse + 會話原子/並發 + matplotlib (2026-07-08)
- ✅ 用 Explore subagent 盤點爆炸半徑：31 個 derivation 工具依賴 `_current_session` 全域、3 個全域單例、sympify 無 DoS 防護、src 無 exec/eval、music.py matplotlib 全域狀態
- ✅ **安全 parse 護欄**（`domain/safe_parse.py`）：拒 power tower/超長/深巢/巨大字面量；接進 `SymPyEngine.parse` + `verify._parse_safe` + `derivation._preprocess_for_sympify`（commit e0030d6）
- ✅ **會話原子/並發**：`DerivationSession.save()` temp+os.replace 原子寫入；`SessionManager` RLock + `get_session_manager` 雙重檢查鎖（commit 8cb58e8）
- ✅ **matplotlib 並發**：`music.py` 改物件式 `Figure`+`FigureCanvasAgg`，去 pyplot 全域狀態（commit c64293b）
- ✅ **DI 組合根 + process-pool timeout** 純程式碼部分已收尾（見上）；`session_id`×22 亦完成
- 🔜 infra 層剩餘（需 infra 決策/相依）：租戶隔離、Streamable HTTP+auth、DB 後端、context-aware 快取、observability、分散式鎖
### 🪜 階段 A/B/C：接完階梯 + 維度下沉 + 推薦器 (2026-07-07)
- ✅ **A**：`task_run` 跑完 concept→symbol→derivation→verify→code。solve_for（engine.solve）、ALGORITHM 產碼（domain/codegen.py→generated_code）、acceptance 神諭執行（equivalence/boundary/limit/dimensional + verified 旗標）、DTS assumptions（k>0）接入、新增 engine.limit
- ✅ **B**：維度分析下沉 `infrastructure/dimensional.py`（單一真相，化約基本維度 N/kg==m/s**2），`BasicVerifier.check_dimensions` 真實作消除 stub，MCP 工具 DRY
- ✅ **C**：`derivation_suggest_next`（domain/suggester.py 純排序 + tools/suggest.py）retrieve-then-rank，工具 87→88
- ✅ 新增測試：test_orchestrator_ladder / test_dimensional / test_orchestrator_acceptance / test_suggester；harness 9/9
### 📊 階段 2：推導評測 gate + 通用性 gate (2026-07-07)
- ✅ `benchmarks/*.json`（4 個已知推導：PK/力學/電路）+ `scripts/bench.py`：用引擎 `equals` 符號比對推導結果與期望（順序無關）；4/4 推導正確
- ✅ `scripts/genericity.py`：程序化隨機生成「從未手寫」的公式組合，過 L3 後與獨立 SymPy `.subs()` 參考答案交叉比對（40/40）→ 證明是通用推導演算法、非手建公式庫
- ✅ 納入 `scripts/check.py` 成為 `bench` + `generic` gate → harness 7→9 gate，「程式碼綠」升級成「推導正確＋通用」
- ✅ AGENTS.md/.clinerules 的 gate 清單同步加 bench、generic
### � 階段 1：接通 L3 引擎 (2026-07-07)
- ✅ `task_run` 的 derivation 階段實際執行：`SymbolicEngine` 組合 base_formulas（代入鏈）→ `derived_expression`
- ✅ `Modification` 加 `target` 欄位（自動代入）；端到端驗證溫度校正得 `C = C0*exp(-A*t*exp(-Ea/(R*T)))`
- ✅ 修 C0→C*0 解析 bug（MathContext 宣告符號）；harness 7/7；屬「泛公式探討」路線圖階段 1
- ✅ mcp 釘 `<2`（避 v2 破壞性發布）、sympy 底線 1.14

### �🚀 自駕基座 + L2/L3 + 型別債清零 (2026-07-07)
- ✅ **Agent 自駕基座 L0+L1**：`scripts/check.py`（單一 ground-truth harness：lint/format/type/import/manifest/test/diff）、`scripts/gen_capabilities.py` + `docs/agent/capabilities.json`（78 工具自描述）、`.github/workflows/ci.yml`（補上缺失的 CI）
- ✅ **型別債清零**：修完 41 個 mypy strict 錯誤（含 formula.py 過濾 None 真 bug）→ harness 7/7 全綠
- ✅ **agent harness 去污染**：`AGENTS.md`、`.clinerules/*` 改為 NSForge 專屬
- ✅ **L2 DTS + L3 編排器**：`domain/task_spec.py` + `application/task_orchestrator.py` + `task_plan`/`task_run` 工具（76→78）+ 測試 + 範例 JSON
- ✅ **方向文件**：`docs/reification-ladder-direction.md`（實體化階梯）

### v0.2.4 Production-Level 品質驗證 (2026-01-21)
- ✅ **版本同步**：3 個檔案更新至 0.2.4（pyproject.toml, __init__.py x2）
- ✅ **ARCHITECTURE.md 完整重寫**：~150 行 DDD 文檔（76 工具分類、資料流圖）
- ✅ **類型安全 100%**：修正 41 個 MyPy 錯誤（標準模式 0 錯誤）
  - simplify.py: int/bool 類型混淆
  - sympy_engine.py: Any 返回類型
  - derivation.py: Union type
  - wikidata_formulas.py: 完整類型標註
  - biomodels.py: 上下文管理器類型
  - adapters/__init__.py: TYPE_CHECKING 模式
  - formula.py: 變數命名衝突
- ✅ **程式碼品質**：Ruff 自動修正 17 issues（f-strings, 未使用 imports）
- ✅ **安全掃描**：Bandit 0 critical/high issues（3 Low 可接受）
- ✅ **測試覆蓋**：31/31 通過，Domain layer 100%
- ✅ **ToolUniverse 評估**：確認適合 PR（互補性高、不重複）

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
