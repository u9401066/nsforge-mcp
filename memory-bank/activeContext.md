# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**多 agent 服務化硬化（安全+並發）第一批完成。** 從 local MCP 轉共享服務的最大風險是「單機假設寫進全域變數」。已用 Explore subagent 盤點爆炸半徑，並 YOLO 三塊純程式碼硬化（各 harness 9/9、已推送）：(1) 安全 parse 護欄擋 sympify DoS（`domain/safe_parse.py`，接進引擎/verify/derivation）；(2) 會話原子寫入 + `SessionManager` 並發鎖（`domain/derivation_session.py`）；(3) `music.py` matplotlib 改物件式 `Figure` 去全域狀態。剩餘為 infra 耦合項（DI 組合根、全量 `session_id` 化+租戶隔離、process-pool timeout、HTTP+auth、DB 後端、快取、observability、分散式鎖）——需 infra 決策，設計已記 decisionLog，逐項確認再上。（泛公式路線圖階段 4 自我修正環仍待做。）

## ✅ 本次完成 (2026-07-07)

### 🚀 YOLO 三任務（安全網保護下）

- **Task 1**：修完 41 個 mypy strict 型別債（含 formula.py 過濾 None 的真 bug）→ type gate 由紅轉綠，harness 7/7
- **Task 2**：清除 agent harness 的 asset-aware-mcp 污染 — 刪 7 純污染檔、重寫 5 核心（AGENTS.md、.clinerules/{00-project,10-python,40-release}、workflows/full-check）為 NSForge 專屬
- **Task 3**：L2 `domain/task_spec.py`（DTS 宣告式規格）+ L3 `application/task_orchestrator.py`（把 DTS 實體化為帶 provenance 的工具調用計畫）+ `tools/task.py`（task_plan/task_run）+ 5 測試 + 範例 JSON；端到端跑出 15 步計畫；工具 76→78

### 🛠️ Agent 自駕基座 L0+L1

- **診斷**：agent harness（`AGENTS.md`/`.clinerules`/`full-check.md`）繼承自 asset-aware-mcp，指向不存在路徑（`scripts/`、`vscode-extension/`、`src/presentation/`）；`.github/workflows` 無 CI → agent 無法取得可信 pass/fail
- `scripts/check.py`：單一 ground-truth 驗證 harness（lint/format/type/import/manifest/test/diff，支援 `--json` 供 agent 解析）
- `scripts/gen_capabilities.py` + `docs/agent/capabilities.json`：從 `@mcp.tool` AST 自動產生 76 工具自描述清單
- `.github/workflows/ci.yml`：補上缺失的 CI
- 基線：6/7 gate 轉綠；`type`（41 個 mypy strict 錯誤）列為基座揪出的第一個可驗證翻新任務
- 待辦：修 `AGENTS.md`/`.clinerules` 的專案污染、L2 DTS + L3 編排器

### 🧭 方向文件 + 正典對齊

- 新增 `docs/reification-ladder-direction.md`：實體化階梯、北極星判準、四斷點診斷、四決策（ADR）、去風險路線圖 P0–P5
- `decisionLog.md`：記錄 2026-07-07 方向決策（提案，待人類 ratify）
- `projectBrief.md` / `productContext.md`：從通用模板校正為 NSForge 正典
- 四決策：(A) 單一真相來源、(B) Concept 一等公民、(C) pseudocode 補階、(D) provenance ledger

> ⚠️ 用戶暫離線授權自主拍板 → 屬提案版本，待 ratify。下一步建議從 P1「實體檢視器」（唯讀、低風險）著手。

## ✅ 上次完成 (2026-01-05)

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
