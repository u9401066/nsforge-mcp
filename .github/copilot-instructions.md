# Copilot 自定義指令

此文件為 VS Code GitHub Copilot 的 Agent Mode 提供專案上下文。

---

## 開發哲學 💡

> **「想要寫文件的時候，就更新 Memory Bank 吧！」**
> 
> **「想要零散測試的時候，就寫測試檔案進 tests/ 資料夾吧！」**

---

## 法規遵循

你必須遵守以下法規層級：

1. **憲法**：`CONSTITUTION.md` - 最高原則，不可違反
2. **子法**：`.github/bylaws/*.md` - 細則規範
3. **技能**：`.claude/skills/*/SKILL.md` - 操作程序

---

## 架構原則

- 採用 **DDD (Domain-Driven Design)**
- **DAL (Data Access Layer) 必須獨立**
- 依賴方向：`Presentation → Application → Domain ← Infrastructure`

詳見：`.github/bylaws/ddd-architecture.md`

---

## Python 環境（uv 優先）

- **優先使用 uv** 管理套件和虛擬環境
- 新專案必須建立 `pyproject.toml` + `uv.lock`
- 禁止全域安裝套件

```bash
# 初始化環境
uv venv
uv sync --all-extras

# 安裝依賴
uv add package-name
uv add --dev pytest ruff
```

詳見：`.github/bylaws/python-environment.md`

---

## Memory Bank 同步

每次重要操作必須更新 Memory Bank：

| 操作 | 更新文件 |
|------|----------|
| 完成任務 | `progress.md` (Done) |
| 開始任務 | `progress.md` (Doing), `activeContext.md` |
| 重大決策 | `decisionLog.md` |
| 架構變更 | `architect.md` |

詳見：`.github/bylaws/memory-bank.md`

---

## Git 工作流

提交前必須執行檢查清單：

1. ✅ Memory Bank 同步（必要）
2. 📖 README 更新（如需要）
3. 📋 CHANGELOG 更新（如需要）
4. 🗺️ ROADMAP 標記（如需要）

詳見：`.github/bylaws/git-workflow.md`

---

## 可用 Skills

位於 `.claude/skills/` 目錄：

### 🔥 NSForge 專用 Skills（MCP 工具組合）

| Skill | 說明 | 觸發詞 |
|-------|------|--------|
| **nsforge-derivation-workflow** | 完整推導工作流 | 推導, derive, 組合公式 |
| **nsforge-formula-management** | 公式庫管理 | 找公式, 列出, 更新公式 |
| **nsforge-verification-suite** | 驗證工具組合 | 驗證, 維度, check |
| **nsforge-code-generation** | 程式碼/報告生成 | 生成程式碼, LaTeX, 報告 |
| **nsforge-quick-calculate** | 快速計算（無需會話） | 計算, 簡化, 求解 |

> 詳細說明見 `docs/nsforge-skills-guide.md`

### ⚠️ 數學計算黃金法則

> **「先用 SymPy-MCP 計算驗證，再用 NSForge 存檔管理！」**
>
> **「每步計算都要用 `print_latex_expression` 顯示給用戶確認！」**
>
> **「人類的推導是一步一步的，每步都可加入新元素！」**

#### 🔥 步進式推導工作流（核心）

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: NSForge 開始會話                                  │
│     derivation_start(name="...", description="...")         │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: 循環 - 每一步都可加入人類知識！                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2a. SymPy-MCP: 執行計算                                │ │
│  │     intro_many([...])                                  │ │
│  │     introduce_expression(...)                          │ │
│  │     substitute_expression(...)                         │ │
│  │     print_latex_expression(...)  # ⚠️ 顯示給用戶！     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 2b. NSForge: 記錄這一步                                │ │
│  │     derivation_record_step(      # 🆕 橋接工具         │ │
│  │       expression="...",          # SymPy 結果          │ │
│  │       description="代入 Arrhenius",                    │ │
│  │       notes="酵素在高溫會變性..."  # ⚡ 人類知識！      │ │
│  │     )                                                  │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 2c. NSForge: 加入說明（可選）                          │ │
│  │     derivation_add_note(         # 🆕 橋接工具         │ │
│  │       note="建議加入校正因子",                         │ │
│  │       note_type="correction"     # ⚡ 修正建議         │ │
│  │     )                                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  → 重複 2a-2c，每步都可加入新洞見 → 演化成新公式！          │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: NSForge 完成存檔                                  │
│     derivation_complete(...)        # 存檔 + 元資料        │
└─────────────────────────────────────────────────────────────┘
```

#### 分工原則

| 任務 | 工具 | 原因 |
|------|------|------|
| **計算求解** | SymPy-MCP | 功能完整（ODE、矩陣、單位） |
| **公式顯示** | `print_latex_expression` | 讓用戶確認結果 |
| **知識存檔** | NSForge | 有溯源、分類、搜尋 |
| **簡單驗證** | NSForge | `check_dimensions` 等 |

#### ❌ 禁止行為

- 不要直接用 `generate_python_function` 生成未經驗證的程式碼
- 不要跳過 `print_latex_expression`，用戶需要看到公式
- 不要把 SymPy-MCP 的計算結果存成 YAML 檔案（應存為 Markdown）

#### 🔄 Handoff 機制：無法計算時怎麼辦？

**當 NSForge 無法處理時（ODE、矩陣、極限等），使用 Handoff 工具：**

```
NSForge 遇到無法處理的操作
        ↓
derivation_export_for_sympy()
        ↓
→ 返回 intro_many_command, current_expression
        ↓
[SymPy-MCP] intro_many([...])
[SymPy-MCP] introduce_expression("...")
[SymPy-MCP] dsolve_ode(...) / solve_linear_system(...) / etc.
[SymPy-MCP] print_latex_expression(...)
        ↓
derivation_import_from_sympy(
    expression="...",
    operation_performed="Solved ODE",
    sympy_tool_used="dsolve_ode",
    notes="...",
    assumptions_used=[...],
    limitations=[...]
)
        ↓
繼續 NSForge 步進式推導！
```

**Handoff 工具三件套：**
- `derivation_export_for_sympy()` - 導出當前狀態給 SymPy-MCP
- `derivation_import_from_sympy()` - 從 SymPy-MCP 導入結果回來
- `derivation_handoff_status()` - 查看能力邊界和工作流程

**使用時機：**
- NSForge 工具返回錯誤
- 需要解 ODE/PDE
- 需要矩陣運算、極限、級數等複雜操作

### 通用開發 Skills

| Skill | 說明 |
|-------|------|
| **git-precommit** | Git 提交前編排器 |
| **ddd-architect** | DDD 架構輔助與檢查 |
| **code-refactor** | 主動重構與模組化 |
| **memory-updater** | Memory Bank 同步 |
| **memory-checkpoint** | 記憶檢查點（Summarize 前外部化） |
| **readme-updater** | README 智能更新 |
| **changelog-updater** | CHANGELOG 自動更新 |
| **roadmap-updater** | ROADMAP 狀態追蹤 |
| **code-reviewer** | 程式碼審查 |
| **test-generator** | 測試生成（Unit/Integration/E2E） |
| **project-init** | 專案初始化 |

---

## 💾 Memory Checkpoint 規則

為避免對話被 Summarize 壓縮時遺失重要上下文：

### 主動觸發時機
1. 對話超過 **10 輪**
2. 累積修改超過 **5 個檔案**
3. 完成一個 **重要功能/修復**
4. 使用者說要 **離開/等等**

### 執行指令
- 「記憶檢查點」「checkpoint」「存檔」
- 「保存記憶」「sync memory」

### 必須記錄
- 當前工作焦點
- 變更的檔案列表（完整路徑）
- 待解決事項
- 下一步計畫

---

## 回應風格

- 使用**繁體中文**
- 提供清晰的步驟說明
- 引用相關法規條文
- 執行操作後更新 Memory Bank
