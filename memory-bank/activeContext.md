# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**v0.2.2 步驟控制系統完成！** 5 個新 MCP 工具實現完整 CRUD 控制。

## ✅ 本次完成 (2026-01-03)

### 🎛️ 步驟 CRUD 功能

實現了推導步驟的完整控制：

| 工具 | 操作 | 說明 |
|------|------|------|
| `derivation_get_step` | 查讀 | 取得任一步驟詳情 |
| `derivation_update_step` | 更新 | 修改元資料（註記、假設、限制） |
| `derivation_delete_step` | 刪除 | 只能刪除最後一步 |
| `derivation_rollback` | ⚡回滾 | 跳回任一步驟，刪除後續 |
| `derivation_insert_note` | 插入 | 在任一位置插入註記 |

**關鍵設計決策**：
- 表達式不可直接編輯（會破壞驗證）
- 用 `rollback` 返回有效狀態再重新推導
- 插入/刪除後自動重編號

### 📖 文檔更新

- **README.md** + **README.zh-TW.md**：
  - 核心能力從 3 → 4（新增 CONTROL）
  - 新增「步驟控制功能」專區（含 ASCII 流程圖）
  - 工具數量 31 → 36
- **CHANGELOG.md**：新增 v0.2.2 版本紀錄

### 🧪 測試覆蓋

- `tests/test_step_crud.py` - 完整單元測試
- `tests/demo_crud.py` - 互動式示範
- Ruff 檢查通過（65 個問題修復）

## 📁 本次變更檔案

```
# 核心功能
src/nsforge/domain/derivation_session.py    # +5 方法 (~150 行)
src/nsforge_mcp/tools/derivation.py          # +5 MCP 工具註冊

# 測試
tests/test_step_crud.py                      # 新增
tests/demo_crud.py                           # 新增

# 文檔
README.md                                    # 大幅更新
README.zh-TW.md                              # 同步更新
CHANGELOG.md                                 # v0.2.2 版本
.claude/skills/nsforge-derivation-workflow/SKILL.md  # 更新
docs/nsforge-skills-guide.md                 # 工具數量更新
```

## 🔜 下一步

1. **Git commit + push**
2. 重啟 MCP 伺服器以載入新工具
3. 測試新工具在實際推導中的效果

---
*Last updated: 2026-01-03*
