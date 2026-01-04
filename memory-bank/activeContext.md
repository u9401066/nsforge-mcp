# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**v0.2.4 Phase 1+2 工具實作完成！** 新增 14 個進階代數和積分變換工具，SymPy 涵蓋率提升至 92%。

## ✅ 本次完成 (2026-01-04)

### � Phase 1: 進階代數簡化 (10 工具)

| 類別 | 工具 | 用途 |
|------|------|------|
| **P0 基礎** | expand, factor, collect | 展開、因式分解、收集同類項 |
| **P0 特殊** | trigsimp, powsimp, radsimp, combsimp | 三角、冪次、根式、階乘 |
| **P1 有理** | apart, cancel, together | 🔥 部分分式、約分、合併 |

**關鍵功能**: `apart_expression` 是反 Laplace 變換的必備前置步驟！

### 📊 Phase 2: 積分變換 (4 工具)

| 工具 | 變換 | 藥動學應用 |
|------|------|------------|
| `laplace_transform` | f(t) → F(s) | ODE 轉代數 |
| `inverse_laplace_transform` | F(s) → f(t) | 🔥 多隔室 PK 解析解 |
| `fourier_transform` | f(x) → F(k) | 週期給藥頻譜 |
| `inverse_fourier_transform` | F(k) → f(x) | 訊號重建 |

**完整工作流**:
```
apart_expression("1/((s+λ1)*(s+λ2))", "s")  → 部分分式
inverse_laplace_transform(...)                → 時域解
→ C(t) = A·e^(-λ1·t) + B·e^(-λ2·t)
```

### 📖 外部公式資料來源 - ✅ 已實作

Background agent 已實作外部公式搜尋功能：

| 來源 | 工具 | 狀態 |
|------|------|------|
| Wikidata | `formula_search`, `formula_get` | ✅ 已實作 |
| BioModels | `formula_pk_models`, `formula_kinetic_laws` | ✅ 已實作 |
| SciPy | `formula_constants` | ✅ 已實作 |

**新增 Skill**: `nsforge-formula-search`

### �🔗 USolver 協作功能

新增與 USolver MCP 的協作能力，擴展 NSForge 從推導到優化：

| 功能層 | 內容 | 說明 |
|--------|------|------|
| **MCP 工具** | `derivation_prepare_for_optimization` | 自動分類變數/參數、生成約束、輸出 USolver 範本 |
| **Agent Skill** | `.claude/skills/nsforge-usolver-collab/SKILL.md` | 完整協作工作流程文檔（~300 行） |
| **文檔** | README + README.zh-TW 更新 | 生態系統圖、協作流程、比較表格 |

**協作流程**：
```
NSForge: 推導領域修正公式 → derivation_prepare_for_optimization()
    ↓ 自動分類：優化變數 vs 參數
    ↓ 生成約束：劑量範圍、時間非負...
    ↓ 輸出範本：USolver 可用格式
USolver: 求解最佳值 → optimal_dose, objective_value
    ↓ 四種求解器：Z3, OR-Tools, CVXPY, HiGHS
結果: 領域智慧 + 數學精確 → 可操作的最佳值
```

**範例用例**：65 歲體脂 30% + midazolam 併用 → 最佳 Fentanyl 劑量 = 35mcg

### 🔍 技術發現

- **USolver 能力**：
  - Z3: SMT 求解器（邏輯謎題、約束滿足）
  - OR-Tools: 組合優化（排程、路由）
  - CVXPY: 凸優化（投資組合、信號處理）
  - HiGHS: 線性/整數規劃（生產、物流）
  
- **SymPy-MCP 安裝**：
  - 位置：`vendor/sympy-mcp/`
  - 依賴：mcp[cli]>=1.9.0, sympy>=1.14.0

### 📖 文檔更新

- **README.md** (英文):
  - 新增 USolver 生態系統條目
  - 新增協作專區（流程圖、比較表、設定指引）
  
- **README.zh-TW.md** (中文):
  - 同步所有英文更新
  - 本地化範例和說明

- **新增 Skill**:
  - `.claude/skills/nsforge-usolver-collab/SKILL.md`
  - 包含：工作流程、用例、故障排除、求解器選擇指南

## ✅ 上次完成 (2026-01-03)

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
