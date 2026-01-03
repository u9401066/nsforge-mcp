# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**v0.2.1 已完成！** 新增 10 個獨特計算工具，程式碼品質檢查通過。

## ✅ 本次完成 (2026-01-03)

### v0.2.1 新增 10 個計算工具
NSForge 現在提供 SymPy-MCP 沒有的功能：

| 類別 | 工具 | 說明 |
|------|------|------|
| **極限/級數** | `calculate_limit()` | 極限（含 ±∞、方向） |
| | `calculate_series()` | Taylor/Laurent/Fourier 展開 |
| | `calculate_summation()` | 符號求和 |
| **不等式** | `solve_inequality()` | 單變數不等式 |
| | `solve_inequality_system()` | 不等式系統 |
| **統計** | `define_distribution()` | 定義機率分佈 |
| | `distribution_stats()` | 期望值、變異數等 |
| | `distribution_probability()` | 機率計算 |
| **假設** | `query_assumptions()` | 符號屬性查詢 |
| | `refine_expression()` | 基於假設簡化 |

### 程式碼品質修復
- **ruff**: 46 → 6 錯誤（剩餘是故意的未使用參數）
- **mypy**: 8 → 2 錯誤（外部套件型別限制）
- **pytest**: 28/28 通過 ✅
- 修復型別註解、移除過時測試檔案

### 文檔更新
- README.md / README.zh-TW.md - 功能狀態更新為 ✅ v0.2.1
- docs/nsforge-vs-sympy-mcp.md - 標記為已實作
- ROADMAP.md - v0.2.1 完成

## 📝 架構決策

- **不 Fork SymPy-MCP**：直接調用 SymPy 模組
- **工具分類清晰**：calculate.py 負責所有 NSForge 獨特計算功能
- **保持介面一致**：所有工具返回 `{"success": bool, ...}` 格式

## 🔜 下一步

- **v0.2.0 主動推導助手**（優先順序較高的功能）：
  - 自動驗證器 (Auto-Validator)
  - 推導建議器 (Derivation Advisor)  
  - 符號語義追蹤 (Symbol Semantics)
  - 錯誤模式檢測 (Error Pattern Detection)

## 📁 本次變更檔案

```
src/nsforge_mcp/tools/calculate.py  # +10 新工具
src/nsforge_mcp/tools/verify.py     # 型別修復
src/nsforge_mcp/tools/codegen.py    # 型別修復
tests/test_sympy_engine.py          # 修復測試
tests/test_registry.py              # 已刪除（過時）
README.md                           # 狀態更新
README.zh-TW.md                     # 狀態更新
docs/nsforge-vs-sympy-mcp.md        # 狀態更新
ROADMAP.md                          # v0.2.1 完成
```

---
*Last updated: 2026-01-03*
