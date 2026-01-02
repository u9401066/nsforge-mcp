# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

設計「公式知識庫」架構 - 讓推導出的公式可以儲存、重用、增長。

**關鍵發現**：sympy-mcp 已經可以執行藥動學推導（ODE 求解、代入、簡化），
不需要額外的推導引擎！NSForge 的價值在於「知識管理」而非「計算」。

## Current Goals

- ## 🎯 當前焦點
- 完成推導引擎核心實作，準備進行 Git commit。
- ## ✅ 本次完成
- ### 推導引擎核心 (DerivationSession)
- - `src/nsforge/domain/formula.py` - Formula domain model + FormulaParser
- - `src/nsforge/domain/derivation_session.py` - 推導會話管理
- - `src/nsforge/infrastructure/derivation_repository.py` - 推導結果儲存庫
- - `src/nsforge/infrastructure/adapters/scipy_constants.py` - 物理常數適配器
- ### MCP 工具集
- - `src/nsforge_mcp/tools/derivation.py` - 完整的推導 MCP 工具
- - derivation_start/resume/abort/status
- - derivation_load_formula
- - derivation_substitute/simplify/solve_for/differentiate/integrate
- - derivation_complete/get_steps
- - derivation_list_saved/get_saved/search_saved/update_saved/delete_saved
- ### 推導範例
- - `formulas/derivations/README.md` - 說明文檔
- - `formulas/derivations/pharmacokinetics/temp_corrected_elimination.md`
- - `formulas/derivations/pharmacokinetics/fat_adjusted_vd.md`
- ### 測試
- - `tests/test_derivation_engine.py` - 推導引擎整合測試
- - `tests/test_registry.py` - 公式註冊表測試
- ### 其他
- - 新增 `py.typed` 支援類型檢查
- - 歸檔 RC low-pass 模板到 `templates/archive/`
- ## 📝 架構決策
- 推導引擎採用：
- - **有狀態會話管理** - DerivationSession 可暫停/恢復
- - **完整步驟追蹤** - 每步都有 SymPy 指令記錄
- - **自動持久化** - 防止中斷遺失
- - **學術溯源** - 追蹤公式來源
- ## 🔜 下一步
- - 整合 verify tools
- - 增加更多推導範例
- - 建立 Code Generation 測試
- ---
- *Last updated: 2026-01-02*

## 📝 今日變更

| 檔案 | 變更內容 |
|------|----------|
| `.github/copilot-instructions.md` | 整合 AGENTS.md 內容 |
| `.vscode/mcp.json` | 修正 MCP 配置，使用 ${workspaceFolder} |
| `src/nsforge_mcp/server.py` | 修正 FastMCP 參數 |
| `AGENTS.md` | 已刪除（整合進 copilot-instructions） |
| `vendor/sympy-mcp/` | 新增 sympy-mcp 依賴 |

## ⚠️ 待解決

（已解決：copilot-instructions.md 編碼問題）

## 💡 重要決定

- **公式知識庫三層架構**：
  - principles/ - 基礎物理定律（不變）
  - domain/ - 領域公式（有文獻）
  - derived/ - 推導公式（可增長，分 proposed/verified）
- **sympy-mcp 足以執行推導**，NSForge 專注知識管理
- 公式有生命週期：proposed → verified → deprecated
- 詳見 decisionLog.md

## 📁 相關檔案

```
.vscode/mcp.json           # MCP 配置
vendor/sympy-mcp/          # sympy-mcp 依賴
formulas/                  # 🆕 公式知識庫（待建立）
  ├── principles/          # 基礎原理
  ├── domain/              # 領域公式
  └── derived/             # 推導公式
      ├── proposed/        # 待檢驗
      └── verified/        # 已檢驗
```

## 🔜 下一步

1. 建立 formulas/ 目錄結構
2. 建立第一批基礎原理 YAML
3. 實作 save_derived_formula() MCP 工具
4. 儲存今天推導的溫度校正藥動學模型

---
*Last updated: 2026-01-02*
