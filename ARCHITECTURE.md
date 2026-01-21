# Architecture

NSForge MCP 架構文檔 (v0.2.4)

---

## 系統概覽

NSForge 是一個 **Neurosymbolic AI 工具**，透過 MCP (Model Context Protocol) 為 AI 代理提供精確的符號推理能力。

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent (Claude, etc.)                     │
├─────────────────────────────────────────────────────────────────┤
│                     MCP Protocol Layer                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              nsforge_mcp (76 Tools)                         ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐ ││
│  │  │Derivation │ │ Calculate │ │ Simplify  │ │   Verify    │ ││
│  │  │ 31 tools  │ │ 12 tools  │ │ 14 tools  │ │  6 tools    │ ││
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────┬──────┘ ││
│  │        │             │             │              │         ││
│  │  ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐ ┌──────┴──────┐ ││
│  │  │  Formula  │ │Expression │ │  Codegen  │ │   Others    │ ││
│  │  │  6 tools  │ │  3 tools  │ │  4 tools  │ │             │ ││
│  │  └───────────┘ └───────────┘ └───────────┘ └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                     nsforge (Core Library)                       │
│  ┌───────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │    Domain     │  │   Application   │  │  Infrastructure   │  │
│  │  Pure Logic   │◄─│   Use Cases     │──►│   Persistence    │  │
│  └───────────────┘  └─────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## DDD 分層架構

### 1. Domain Layer (`src/nsforge/domain/`)

純業務邏輯，無外部依賴。

| 模組 | 說明 |
|------|------|
| `entities/` | Formula, DerivationStep, DerivationSession |
| `value_objects/` | Expression, Assumption, Metadata |
| `services/` | SymPyEngine, DerivationEngine |
| `repositories/` | FormulaRepository (抽象介面) |

### 2. Application Layer (`src/nsforge/application/`)

協調 Domain 與 Infrastructure。

| 模組 | 說明 |
|------|------|
| `use_cases/` | 推導、驗證、公式管理用例 |
| `dto/` | 資料傳輸物件 |

### 3. Infrastructure Layer (`src/nsforge/infrastructure/`)

外部系統介面。

| 模組 | 說明 |
|------|------|
| `persistence/` | YAML/JSON 檔案存儲 |
| `formula_repository_impl.py` | FormulaRepository 實作 |

### 4. MCP Layer (`src/nsforge_mcp/`)

MCP 協議介面，獨立於核心庫。

| 模組 | 說明 |
|------|------|
| `server.py` | MCP Server 入口 |
| `tools/` | 76 個 MCP 工具實作 |

---

## 工具分類 (76 Tools)

| 類別 | 數量 | 說明 |
|------|------|------|
| **Derivation** | 31 | 推導會話管理、步驟操作 |
| **Calculate** | 12 | 極限、級數、求和、Laplace/Fourier 變換 |
| **Simplify** | 14 | 展開、因式分解、三角簡化等 |
| **Verify** | 6 | 等價驗證、維度檢查 |
| **Formula** | 6 | 公式庫 CRUD |
| **Expression** | 3 | 表達式解析、符號提取 |
| **Codegen** | 4 | Python/LaTeX 生成 |

---

## 資料流

```
User Request → MCP Tool → Use Case → Domain Service → SymPy Engine
                                           │
                                           ▼
                              Infrastructure (YAML/JSON)
```

### 推導工作流範例

1. `derivation_start()` - 開始會話
2. `derivation_record_step()` - 記錄每步
3. `derivation_substitute()` / `derivation_integrate()` - 操作
4. `derivation_show()` - 顯示當前狀態
5. `derivation_complete()` - 存檔

---

## 目錄結構

```
nsforge-mcp/
├── src/
│   ├── nsforge/              # Core Library (DDD)
│   │   ├── domain/           # 純業務邏輯
│   │   ├── application/      # 用例協調
│   │   └── infrastructure/   # 持久化
│   └── nsforge_mcp/          # MCP Server
│       ├── server.py         # 入口
│       └── tools/            # 76 工具
├── formulas/                 # 公式庫
│   ├── derivations/          # 原始推導
│   └── derived/              # 推導結果
├── derivation_sessions/      # 會話存檔
├── templates/                # 公式模板
└── tests/                    # 測試
```

---

## 技術棧

- **Python**: 3.12+
- **SymPy**: 符號計算引擎
- **MCP SDK**: Model Context Protocol
- **uv**: 套件管理
- **Ruff**: Linting
- **pytest**: 測試框架

---

## 相關文檔

- [README.md](README.md) - 專案說明
- [CONSTITUTION.md](CONSTITUTION.md) - 開發原則
- [docs/nsforge-skills-guide.md](docs/nsforge-skills-guide.md) - 技能指南
