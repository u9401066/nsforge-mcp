# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**v0.2.4 derivation_show() 工具 + Skill 文檔大更新！** 確保 Agent 每次操作後都向用戶展示公式。

## ✅ 本次完成 (2026-01-05)

### 🆕 derivation_show() 工具

新增推導狀態顯示工具，類似 SymPy-MCP 的 `print_latex_expression`：

| 功能 | 說明 |
|------|------|
| `derivation_show(format="all")` | 顯示 LaTeX + SymPy + 摘要 |
| `derivation_show(format="latex")` | 只顯示 LaTeX |
| `derivation_show(show_steps=True)` | 包含步驟歷史 |

**工具數量**: 75 → 76 (NSForge)，107 → 108 (生態系統)

### 📖 Skill 文檔大更新

更新所有 NSForge 相關 Skill，強調「必須向用戶展示公式」：

| Skill | 新增內容 |
|-------|----------|
| nsforge-derivation-workflow | 🆕 黃金法則區塊 + 2d 步驟 |
| nsforge-quick-calculate | ⚠️ 顯示結果提醒 |
| nsforge-verification-suite | ⚠️ 驗證後展示結果 |
| nsforge-formula-management | ⚠️ 公式展示（LaTeX 格式） |
| nsforge-code-generation | ⚠️ 生成後展示程式碼 |
| nsforge-formula-search | ⚠️ 搜尋結果表格展示 |
| copilot-instructions.md | 工作流圖 + 分工表更新 |

### 🔧 Bug 修復 + Lint

- 修復 `DerivationStep` 屬性存取錯誤（`step.get()` → `getattr()`）
- 修復類型標註（`sp.Expr` → `sp.Basic` 支援 `Equality`）
- Ruff + ty 檢查全數通過

### 📊 Commits 摘要 (2026-01-05)

| Commit | 說明 |
|--------|------|
| `945a11e` | README Ecosystem 更新 (107 tools) |
| `51d1560` | DerivationStep bug fix |
| `ff383f3` | Ruff + ty lint pass |
| `b6afe81` | derivation_show() 工具 |
| `7299bbc` | 所有 Skill 文檔更新 |

## 📁 本次變更檔案

```
# 核心功能
src/nsforge_mcp/tools/derivation.py          # +derivation_show() (~100 行)

# Skill 文檔 (7 檔案)
.claude/skills/nsforge-*/SKILL.md            # 全部更新
.github/copilot-instructions.md              # 工作流圖更新

# README
README.md                                    # 工具數量 108
```

## ✅ 上次完成 (2026-01-04)

### Phase 1+2 工具實作
- 10 個進階代數簡化工具（expand, factor, apart 等）
- 4 個積分變換工具（Laplace, Fourier）
- 外部公式搜尋功能（Wikidata, BioModels, SciPy）
- USolver 協作功能

## 🔜 下一步

1. 測試 derivation_show() 在實際推導中的效果
2. 觀察 Agent 是否正確遵循新的顯示指引

---
*Last updated: 2026-01-05*
