# Roadmap

專案發展路線圖與功能規劃。

## 已完成 ✅

### v0.1.0+ (2025-12-15)
- [x] 專案初始化
- [x] Memory Bank 系統建立
- [x] Claude Skills 基礎架構
- [x] Git 文檔自動更新 Skill
- [x] 🎯 **NSForge Skills 系統** - 5 個專業推導工作流程
  - [x] `nsforge-derivation-workflow` - 完整推導工作流
  - [x] `nsforge-verification-suite` - 驗證工具組合
  - [x] `nsforge-formula-management` - 公式庫管理
  - [x] `nsforge-code-generation` - 程式碼/報告生成
  - [x] `nsforge-quick-calculate` - 快速計算
- [x] 📚 **完整文檔系統**
  - [x] `docs/nsforge-skills-guide.md` (588 行) - Agent 使用指南
  - [x] `.claude/skills/nsforge-verification-suite/SKILL.md` (522 行)
  - [x] Skills 觸發詞、工作流程圖、41 個工具清單
- [x] 🔬 **3 個高品質推導範例**
  - [x] NPO 抗生素效應（pH 依賴性吸收）
  - [x] 溫度校正 Michaelis-Menten（酵素動力學）
  - [x] Cisatracurium 多次給藥（水解型藥物累積）
- [x] 🐍 **Python 應用範例**
  - [x] `examples/npo_antibiotic_analysis.py` (251 行)
- [x] 🔄 **Handoff 機制** - NSForge ↔ SymPy-MCP 無縫整合
  - [x] `derivation_export_for_sympy()` - 導出狀態
  - [x] `derivation_import_from_sympy()` - 導入結果
  - [x] `derivation_handoff_status()` - 能力邊界查看
- [x] 📝 **步進式推導工作流**
  - [x] `derivation_record_step()` - 記錄計算 + 人類洞見
  - [x] `derivation_add_note()` - 加入臨床註記
- [x] ✅ **驗證工具增強** (6 個函數)

## 進行中 🚧

- [ ] 完善 Skills 觸發機制（部分完成 - NSForge Skills 已上線）
- [ ] 測試文檔自動更新流程（部分完成 - CHANGELOG/README 已測試）

## 計劃中 📋

### 短期目標
- [ ] 新增更多實用 Skills
- [ ] 建立專案模板系統
- [ ] 整合 CI/CD 流程

### 長期目標
- [ ] Skills 分享與匯入機制
- [ ] 多專案 Memory Bank 同步
- [ ] 自定義 Agent 建立
