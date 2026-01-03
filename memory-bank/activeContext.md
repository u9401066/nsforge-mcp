# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**Skills 精簡化完成！** 5 個 SKILL.md 檔案減量 80-92%，已準備 git push。

## ✅ 本次完成 (2026-01-03)

### Skills 精簡化
由於 SKILL.md 會完整載入 context，進行了全面精簡：

| Skill | 原始 | 精簡後 | 減量 |
|-------|------|--------|------|
| nsforge-quick-calculate | 794 行 | 65 行 | 92% |
| nsforge-derivation-workflow | 442 行 | 93 行 | 79% |
| nsforge-verification-suite | 266 行 | 55 行 | 79% |
| nsforge-formula-management | 472 行 | 49 行 | 90% |
| nsforge-code-generation | 526 行 | 77 行 | 85% |

**保留內容**：
- 工具名 + 參數簽名
- 1-2 行簡潔範例
- 決策表（何時用哪個工具）

**刪除內容**：
- Agent 回應範例
- ASCII 流程圖
- JSON 返回格式詳情
- 冗長使用場景

### copilot-instructions.md 更新
- 新增「86 工具快速選擇指南」表格
- 標記 v0.2.1 新增工具（極限/級數/求和可用 NSForge）
- 更新 Handoff 機制說明

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
