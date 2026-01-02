# Changelog

所有重要變更都會記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
專案遵循 [語義化版本](https://semver.org/lang/zh-TW/)。

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
