# Changelog

所有重要變更都會記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

## [Unreleased]

## [0.2.4] - 2026-01-21

### Fixed

- 🛠️ **類型安全性修正** - 修復 41 個 MyPy 類型錯誤
  - `simplify.py`: 修正 int/bool 類型混淆 (lines 168-184, 252-258)
  - `sympy_engine.py`: 為 equals() 方法添加顯式 bool() 轉換 (line 213)
  - `derivation.py`: 使用 Union type `str | float` 處理 param_value (line 1904)
  - `wikidata_formulas.py`: 完整類型標註 (lines 285-324)
  - `biomodels.py`: 新增內部函數與上下文管理器類型標註 (lines 305-443)
  - `adapters/__init__.py`: 使用 TYPE_CHECKING 模式避免循環導入 (lines 1-46)
  - `formula.py`: 重新命名變數避免類型衝突

- 🎨 **程式碼品質提升**
  - Ruff 自動修正 17 issues (f-strings, 未使用 imports)
  - 格式化 8 個檔案以保持一致性
  - 新增安全豁免標記 (biomodels.py line 253: trusted XML source)

- 🔒 **安全性**
  - Bandit 掃描通過 (0 critical/high issues)
  - 3 個 Low severity issues 均為可接受模式 (intentional try-except-pass, trusted XML)

### Changed

- 📚 **ARCHITECTURE.md 完整重寫**
  - 新增完整 DDD 架構文檔 (~150 lines)
  - 76 個工具詳細分類
  - 資料流程圖與目錄結構說明

- 📦 **版本同步**
  - `pyproject.toml` version 更新至 "0.2.4"
  - `src/nsforge/__init__.py` __version__ 更新至 "0.2.4"
  - `src/nsforge_mcp/__init__.py` __version__ 更新至 "0.2.4"

### Technical Details

- **MyPy 驗證**: 標準模式 0 errors in 28 files ✅
- **測試狀態**: 31/31 passed in 5.79s ✅
- **覆蓋率**: Domain layer 100%, 整體 29% ✅
- **Ruff 狀態**: 1 minor E402 in test file (acceptable) ✅

---

## [Unreleased - Future]

### Added

- 🧬 **生理學 Vd 體組成調整模型** (2026-01-16)
  - **完整 PBPK 推導**：Poulin-Theil 組織分布模型
  - **驗證分析**：9 種藥物測試，發現 logP-only Kp 預測的根本限制
  - **公式重新定位**：從「通用 Vd 預測」→「體組成調整公式」
  - **適用範圍定義**：logP > 2、中性分子、被動擴散
  - **文檔**：`formulas/derivations/pharmacokinetics/physiological_vd_body_composition.md`
  - **Python 實作**：`examples/physiological_vd_model.py` (PhysiologicalVdModel 類別)

- 🆕 **Phase 2 - 積分變換工具** (4 個新 MCP 工具)
  - **P2 Laplace 變換** (2 個，🔥🔥 高優先度)：
    - `laplace_transform_expression` - Laplace 變換 exp(-k*t) → 1/(s+k)
    - `inverse_laplace_transform_expression` - 反 Laplace 變換（ODE 代數解 → 時域解）
  - **P2 Fourier 變換** (2 個，🔥 優先度)：
    - `fourier_transform_expression` - Fourier 變換（頻域分析）
    - `inverse_fourier_transform_expression` - 反 Fourier 變換（頻域 → 時域）
- 🧪 **Phase 2 測試套件**：`tests/test_phase2_tools.py` - 所有 4 個工具通過測試
- 📊 **涵蓋率提升**：SymPy 涵蓋率從 90% 提升至 92%
- 🔬 **藥動學應用增強**：
  - 與 `apart_expression` 搭配，完整 Laplace 變換工作流
  - 多隔室模型完整求解（s-domain → time-domain）
  - 轉移函數分析（穩定性、響應）
- 🆕 **Phase 1 - 進階代數簡化工具** (10 個新 MCP 工具)
  - **P0 基礎代數** (7 個)：
    - `expand_expression` - 展開表達式 (x+1)² → x²+2x+1
    - `factor_expression` - 因式分解 x²-1 → (x-1)(x+1)
    - `collect_expression` - 收集同類項
    - `trigsimp_expression` - 三角函數化簡 sin²+cos² → 1
    - `powsimp_expression` - 冪次化簡 x²·x³ → x⁵
    - `radsimp_expression` - 根式化簡 1/(√3+√2) → -√2+√3
    - `combsimp_expression` - 組合函數化簡 n!/(n-2)! → n(n-1)
  - **P1 有理函數處理** (3 個)：
    - `apart_expression` - 部分分式分解（關鍵：反 Laplace 變換準備）
    - `cancel_expression` - 約分有理式
    - `together_expression` - 合併分式

### Changed

- 🔧 **工具註冊系統**
  - 擴展 `simplify.py` 模組至 1150+ 行（Phase 1 + Phase 2）
  - Phase 2 工具整合至同一註冊函數

### Technical Details

- **Phase 2 設計原則**：
  - Laplace 變換：ODE → 代數方程（s-domain）
  - 反 Laplace：與 apart_expression 完美搭配
  - Fourier 變換：週期性給藥分析、頻譜分析
- **變數處理**：正確的符號替換（t→s、x→k）
- **收斂條件**：Laplace 變換返回收斂平面資訊
- **Phase 1 設計原則**：精確控制（expand vs simplify 的確定性差異）
- **Python 兼容**：加入 `from __future__ import annotations` 支援 Python 3.9

---

## [0.2.2] - 2026-01-03

### Added
- 🎛️ **步驟控制系統** - 5 個新 MCP 工具，完整 CRUD 控制推導步驟
  - `derivation_get_step` - 查讀任一步驟詳情（表達式、註記、假設）
  - `derivation_update_step` - 更新步驟元資料（註記、假設、限制）
  - `derivation_delete_step` - 刪除最後一步（安全限制）
  - `derivation_rollback` - ⚡ 回滾到任一步驟，刪除後續步驟
  - `derivation_insert_note` - 在任一位置插入說明性註記
- 📖 **README 大幅更新**
  - 新增「步驟控制功能」專區，含 ASCII 流程圖
  - 核心能力從 3 個增加到 4 個（新增 CONTROL）
  - 工具數量更新：31 → 36（推導引擎 21 → 26）
- 🧪 **完整測試覆蓋**
  - `tests/test_step_crud.py` - 步驟 CRUD 單元測試
  - `tests/demo_crud.py` - 互動式 CRUD 示範

### Changed
- 🧠 **Skills 文件更新**
  - `nsforge-derivation-workflow/SKILL.md` 新增步驟 CRUD 工具表格
  - `docs/nsforge-skills-guide.md` 工具數量 41 → 46
- 🔧 **程式碼品質**
  - Ruff 檢查通過（65 個問題已修復）
  - 新增 `# noqa: ARG002` 標記保留參數

### Technical Details
- **新增方法**：`DerivationSession` 類別新增 5 個方法（~150 行）
- **安全設計**：表達式不可直接編輯，需透過 rollback 重新推導
- **自動重編號**：插入/刪除步驟後自動調整步驟編號
- **持久化整合**：所有 CRUD 操作自動觸發 session 儲存

---

## [Unreleased]

### Added
- 🎯 **NSForge Skills 系統** - 5 個專業推導工作流程
  - `nsforge-derivation-workflow` - 完整推導工作流（會話→載入→推導→驗證→存檔）
  - `nsforge-verification-suite` - 驗證工具組合（等式、導數、積分、維度分析）
  - `nsforge-formula-management` - 公式庫管理（查詢、取得、更新、刪除）
  - `nsforge-code-generation` - 程式碼/報告生成（Python、LaTeX、Markdown、SymPy 腳本）
  - `nsforge-quick-calculate` - 快速計算（簡化、展開、因式分解、求解、微分、積分）
- 📚 **完整文檔系統**
  - `docs/nsforge-skills-guide.md` (588 行) - Agent 使用指南與黃金法則
  - `.claude/skills/nsforge-verification-suite/SKILL.md` (522 行) - 驗證工具技能定義
  - Skills 觸發詞、工作流程圖、41 個工具清單
- 🔬 **高品質推導範例** (3 個完整案例)
  - **NPO 抗生素效應** (`formulas/derivations/pharmacokinetics/npo_antibiotic_effect.md`)
    - Henderson-Hasselbalch + Emax 模型
    - pH 依賴性吸收（弱酸性抗生素）
    - 臨床場景：Amoxicillin 在 NPO 患者效力可降低 >90%
  - **溫度校正 Michaelis-Menten** (`formulas/derivations/pharmacokinetics/temp_corrected_michaelis_menten.md`)
    - 非線性飽和動力學 + Arrhenius 溫度依賴
    - 酵素活性溫度效應（Vmax、Km 校正）
    - 臨床場景：CPB 手術體溫 32°C 時酵素活性降低
  - **Cisatracurium 多次給藥** (`derivation_sessions/session_ce30161d.json`, `formulas/derived/ce30161d.yaml`)
    - 水解型藥物累積模型
    - 溫度校正消除率（Arrhenius）
    - 穩態波峰/波谷計算（累積因子 R_ac）
    - 8 步完整推導 + 臨床註記
- 🐍 **Python 應用範例**
  - `examples/npo_antibiotic_analysis.py` (251 行)
  - 實作 NPO 抗生素效應模型
  - 臨床場景分析（pH 2.0, 4.5, 7.0）
  - 繪圖與臨床建議生成
- 🔄 **Handoff 機制**
  - `derivation_export_for_sympy()` - 導出狀態給 SymPy-MCP
  - `derivation_import_from_sympy()` - 從 SymPy-MCP 導入結果
  - `derivation_handoff_status()` - 查看能力邊界
  - 支援 ODE/PDE、矩陣運算、極限、級數等複雜操作
- 📝 **步進式推導工作流**
  - `derivation_record_step()` - 記錄每步計算 + 人類洞見
  - `derivation_add_note()` - 加入臨床註記、假設、限制
  - 演化式推導：每步都可加入新知識
- ✅ **驗證工具增強**
  - `symbolic_equal()` - 快速等式驗證
  - `verify_equality()` - 完整驗證報告
  - `verify_derivative()` - 導數反向驗證
  - `verify_integral()` - 積分反向驗證
  - `check_dimensions()` - 維度一致性檢查
  - `reverse_verify()` - 逆向求解驗證

### Changed
- 📖 **README 大幅更新**
  - 新增推導範例表格（4 個案例）
  - 新增 NPO 抗生素效應範例段落
  - 連結至 Python 實作範例
  - 繁體中文版同步更新
- 🧠 **Memory Bank 更新**
  - `progress.md` 記錄 3 個高品質推導案例
  - 記錄完整文檔系統建立
  - 記錄 Python 應用範例

### Technical Details
- **推導會話數量**：3 個完整案例（9ed14ddb, c8cbb753, ce30161d）
- **公式庫增長**：4 個推導 Markdown 文件 + 3 個 YAML 元資料
- **文檔總量**：~1,361 行（Skills 文檔）+ 4 個推導文檔 + 1 個 Python 範例
- **SymPy-MCP 整合**：完整 Handoff 機制支援複雜計算
- **驗證工具**：6 個驗證函數涵蓋等式、導數、積分、維度

## [0.1.0] - 2025-12-15

### Added
- 初始化專案結構
- 新增 Claude Skills 支援
  - `git-doc-updater` - Git 提交前自動更新文檔技能
- 新增 Memory Bank 系統
  - `activeContext.md` - 當前工作焦點
  - `productContext.md` - 專案上下文
  - `progress.md` - 進度追蹤
  - `decisionLog.md` - 決策記錄
  - `projectBrief.md` - 專案簡介
  - `systemPatterns.md` - 系統模式
  - `architect.md` - 架構文檔
- 新增 VS Code 設定
  - 啟用 Claude Skills
  - 啟用 Agent 模式
  - 啟用自定義指令檔案
