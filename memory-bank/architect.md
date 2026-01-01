# System Architect

> 📌 此檔案記錄重大架構決策，架構變更時更新。

## 🌐 系統架構圖

```
┌─────────────────────────────────────────────┐
│              專案模板結構                      │
├─────────────────────────────────────────────┤
│  🏔️ 規則層                                        │
│  ┌─────────────┐                                  │
│  │ CONSTITUTION │ ───┐                             │
│  └─────────────┘     │                             │
│        │            ▼                             │
│        │     ┌────────────┐                        │
│        ├────▶│  Bylaws   │                        │
│        │     └────────────┘                        │
│        │            │                             │
│        ▼            ▼                             │
│  ┌───────────────────────┐                      │
│  │    Claude Skills      │                      │
│  └───────────────────────┘                      │
├─────────────────────────────────────────────┤
│  🧠 記憶層                                        │
│  ┌───────────────────────┐                      │
│  │     Memory Bank       │                      │
│  │  (7 markdown files)   │                      │
│  └───────────────────────┘                      │
├─────────────────────────────────────────────┤
│  ⚙️ 工具層                                        │
│  ┌────────┐ ┌─────────┐ ┌─────────┐           │
│  │ CI/CD  │ │ Testing │ │ Linting │           │
│  └────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────┘
```

## 🏛️ 架構決策紀錄

### ADR-001: 採用憲法-子法層級架構

**日期**：2025-12-15

**背景**：需要一個清晰的規則層級系統

**決定**：採用憲法 → 子法 → Skills 三層結構

**理由**：
- 最高原則集中在 CONSTITUTION.md
- 細則可在 bylaws/ 擴展
- Skills 專注於操作程序

### ADR-002: DDD + DAL 獨立

**日期**：2025-12-15

**背景**：確保業務邏輯與資料存取分離

**決定**：Repository 介面在 Domain，實作在 Infrastructure

**理由**：
- 提高可測試性
- Domain 不依賴資料庫技術
- 可替換儲存實作

### ADR-003: uv 優先套件管理

**日期**：2025-12-15

**背景**：Python 套件管理工具選擇

**決定**：優先使用 uv，後備 pip

**理由**：
- 比 pip 快 10-100 倍
- 原生支援 lockfile
- 與 pip 完全相容

## 📦 元件圖

```
.claude/skills/          # 12 個 Skills
├── git-precommit/       # 編排器
├── ddd-architect/       # 架構
├── code-refactor/       # 重構
├── code-reviewer/       # 審查
├── test-generator/      # 測試
├── memory-updater/      # 記憶
├── memory-checkpoint/   # 檢查點
├── readme-updater/      # README
├── changelog-updater/   # CHANGELOG
├── roadmap-updater/     # ROADMAP
├── project-init/        # 初始化
└── git-doc-updater/     # 文檔更新

.github/bylaws/          # 4 個子法
├── ddd-architecture.md
├── git-workflow.md
├── memory-bank.md
└── python-environment.md
```

---
*Last updated: 2025-12-15*



## Architectural Decisions

- 從完整模板系統演化到可組合推導框架
- Lean4 作為公式知識來源（形式化驗證）
- sympy-mcp 作為計算引擎（符號運算）
- NSForge 作為橋接層（推導編排）



## Design Considerations

- 可擴展性：不窮舉問題，而是提供組合能力
- 可驗證性：通過 Lean4 保證基礎原理正確
- 教育價值：展示從基礎定理到實際問題的推導過程
- 社群協作：允許貢獻 modifications 和 derived_forms



## Components

### Principles Library

提供基礎物理/化學/數學原理，每個 principle 關聯 Lean4 證明

**Responsibilities:**

- 儲存理想化定理
- 提供 Lean4 驗證引用
- 定義變數類型和約束

### Modifications Library

可添加到 principles 的修正項（摩擦力、空氣阻力、熱損失等）

**Responsibilities:**

- 定義修正項表達式
- 說明適用條件
- 提供典型數值範圍

### Derivation Engine

將 principle + modifications 編譯成 sympy-mcp 調用序列

**Responsibilities:**

- 組合公式
- 生成推導步驟
- 調用 sympy-mcp
- 驗證維度和合理性

### Derived Forms Library

社群貢獻的常見問題推導（可選快捷方式）

**Responsibilities:**

- 提供預組合的變體
- 加速常見問題求解
- 作為教學範例



