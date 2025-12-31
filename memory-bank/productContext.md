# Product Context

> 📌 此檔案描述專案的技術架構和產品定位，專案初期建立後較少更新。

## 📋 專案概述

**專案名稱**：AI 輔助開發專案模板

**一句話描述**：整合 Claude Skills、Memory Bank 和憲法-子法規則系統的專案模板。

**目標用戶**：使用 VS Code + GitHub Copilot/Claude 的開發者

## 🏗️ 架構

```
專案模板
├── 規則系統 (憲法 → 子法 → Skills)
├── 記憶系統 (Memory Bank)
├── 技能系統 (Claude Skills)
└── 工具鏈 (CI/CD, 測試, Linting)
```

### 分層架構 (DDD)

```
Presentation → Application → Domain ← Infrastructure
```

## ✨ 核心功能

- 🏛️ 憲法-子法層級規則系統
- 🧠 Memory Bank 跨對話記憶
- 🛠️ 12 個可組合 Claude Skills
- 📋 完整 CI/CD 流程
- 🧪 測試金字塔支援

## 🔧 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.11+ |
| 套件管理 | uv (優先) / pip |
| Linting | Ruff, MyPy, Bandit |
| 測試 | pytest, Playwright |
| CI/CD | GitHub Actions |
| AI 工具 | VS Code + Claude Skills |

## 📦 依賴

### 核心依賴
- (根據專案填寫)

### 開發依賴
- pytest, pytest-cov
- ruff, mypy, bandit
- playwright (E2E)

---
*Last updated: 2025-12-15*