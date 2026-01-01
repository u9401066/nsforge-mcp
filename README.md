# 🔥 Neurosymbolic Forge (NSForge)

> **Where Neural Meets Symbolic**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

**NSForge** 是一個 MCP (Model Context Protocol) Server，為 AI Agent 提供**精確的符號推理**能力。結合 LLM 的自然語言理解與符號引擎的數學精確性，實現可驗證、可重現的科學計算。

## 🎯 核心價值

| 傳統 LLM 方式 | NSForge 方式 |
|--------------|-------------|
| LLM 直接生成答案 | LLM 規劃 → 符號引擎計算 |
| 每次結果可能不同 | **相同輸入 = 相同輸出** |
| 可能計算錯誤 | **數學正確性有保障** |
| 推導過程不透明 | **完整推導步驟可追蹤** |
| 無法驗證 | **可反向驗證結果** |

## 🧠 Neural-Symbolic 架構

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   LLM (Neural)              Engine (Symbolic)                   │
│   ════════════              ═════════════════                   │
│                                                                 │
│   ✓ 理解自然語言            ✓ 精確執行邏輯運算                  │
│   ✓ 規劃推導策略            ✓ 保證計算正確性                    │
│   ✓ 解釋結果給用戶          ✓ 提供推導步驟                      │
│                                                                 │
│   結合：LLM 做「理解與規劃」，Engine 做「精確計算」             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ 功能特色

### 🔢 符號計算
- 微積分（微分、積分、極限、級數）
- 代數（化簡、展開、因式分解、解方程）
- 線性代數（矩陣運算、特徵值）

### 🔬 物理公式
- 力學（運動學、牛頓定律、動量、能量）
- 熱力學（理想氣體、熵、卡諾循環）
- 電磁學（電路分析、頻率響應）

### ⚗️ 化學計算
- 方程式配平
- 化學計量
- 平衡常數

### 📊 演算法分析
- 遞迴關係求解
- Master Theorem
- 複雜度分析

### 🔍 推導驗證
- 維度檢查
- 反向驗證
- 步驟追蹤

## 📦 安裝

### 環境需求

- **Python 3.12+**
- **uv** (推薦的套件管理器)

```bash
# 使用 uv（推薦）
uv add nsforge-mcp

# 或使用 pip
pip install nsforge-mcp
```

### 從原始碼安裝

```bash
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# 建立環境並安裝依賴
uv sync --all-extras

# 驗證安裝
uv run python -c "import nsforge; print(nsforge.__version__)"
```

## 🚀 快速開始

### 作為 MCP Server

```json
// Claude Desktop 配置 (claude_desktop_config.json)
{
  "mcpServers": {
    "nsforge": {
      "command": "uvx",
      "args": ["nsforge-mcp"]
    }
  }
}
```

### 使用範例

**微積分計算**：
```
用戶：計算 ∫(x² + 3x)dx 並驗證結果

Agent 呼叫 NSForge：
→ 結果：x³/3 + 3x²/2 + C
→ 驗證：d/dx(x³/3 + 3x²/2) = x² + 3x ✓
→ 步驟：分解積分 → 冪次規則 → 合併
```

**物理推導**：
```
用戶：理想氣體等溫膨脹做的功？

Agent 呼叫 NSForge：
→ W = nRT ln(V₂/V₁)
→ 推導：PV=nRT → P=nRT/V → W=∫PdV → 積分
```

**演算法分析**：
```
用戶：分析 T(n) = 2T(n/2) + n

Agent 呼叫 NSForge：
→ T(n) = Θ(n log n)
→ 方法：Master Theorem Case 2
→ 範例：Merge Sort
```

## 📖 文檔

### 設計文檔
- [設計演化：推導框架](docs/design-evolution-derivation-framework.md) - 從模板到可組合推導框架的架構演化
- [領域規劃：音響電路學](docs/domain-audio-circuits.md) - Audio circuits principles 與 modifications
- [原始設計](docs/symbolic-reasoning-mcp-design.md) - 完整架構與 API 設計（參考）

### 實例推導
- [Power Amp 交聯電容設計](docs/examples/power-amp-coupling-capacitor.md) - RC 高通濾波器的完整推導流程
  - 從理想公式到實際考慮（輸出阻抗、ESR、喇叭阻抗曲線）
  - 展示 NSForge "Principles + Modifications" 框架實際應用

### API 參考
- [API 參考](docs/api.md) - MCP 工具詳細說明（待補）

## 🛠️ MCP 工具

| 工具 | 用途 |
|------|------|
| `symbolic_calculate` | 符號數學計算 |
| `physics_formula` | 物理公式推導 |
| `chemistry_calculate` | 化學計算 |
| `algorithm_analyze` | 演算法分析 |
| `verify_derivation` | 推導驗證 |
| `unit_convert` | 單位換算 |

## 🏗️ 專案結構

本專案採用 **DDD (Domain-Driven Design)** 架構，Core 與 MCP 分離：

```
nsforge-mcp/
├── src/
│   ├── nsforge/               # 🔷 Core Domain (純邏輯，無 MCP 依賴)
│   │   ├── domain/            # Domain Layer
│   │   │   ├── entities.py    #   - 實體 (Expression, Derivation)
│   │   │   ├── value_objects.py #   - 值物件 (MathContext, Result)
│   │   │   └── services.py    #   - 領域服務介面
│   │   ├── application/       # Application Layer
│   │   │   └── use_cases.py   #   - 用例 (Calculate, Derive, Verify)
│   │   └── infrastructure/    # Infrastructure Layer
│   │       ├── sympy_engine.py #   - SymPy 引擎實作
│   │       └── verifier.py    #   - 驗證器實作
│   │
│   └── nsforge_mcp/           # 🔶 MCP Layer (Presentation)
│       ├── server.py          #   - FastMCP Server
│       └── tools/             #   - MCP 工具定義
│           ├── calculate.py   #     - 計算工具
│           ├── calculus.py    #     - 微積分工具
│           └── verify.py      #     - 驗證工具
│
├── tests/                     # 測試
├── docs/                      # 文檔
└── pyproject.toml             # 專案配置 (uv/hatch)
```

### 架構優勢

- **Core 可獨立測試**：不依賴 MCP，可單獨使用 `nsforge` 套件
- **MCP 可替換**：未來可支援其他協議（REST, gRPC）
- **依賴反轉**：Domain 定義介面，Infrastructure 實作

## 🧪 開發

```bash
# Clone
git clone https://github.com/u9401066/nsforge-mcp.git
cd nsforge-mcp

# 建立環境 (uv 會自動使用 Python 3.12+)
uv sync --all-extras

# 執行測試
uv run pytest

# 程式碼檢查
uv run ruff check src/
uv run mypy src/

# 啟動開發 Server
uv run nsforge-mcp
```

## 📋 Roadmap

- [x] 設計文檔
- [ ] MVP 實作
  - [ ] DSL Parser
  - [ ] Step Executor (SymPy)
  - [ ] Basic Verifier
  - [ ] MCP Wrapper
- [ ] 領域擴展
  - [ ] 物理公式庫
  - [ ] 化學計算
  - [ ] 演算法分析
- [ ] 進階功能
  - [ ] Lean4 形式驗證
  - [ ] 自動推導規劃

## 🤝 貢獻

歡迎貢獻！請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 授權

[Apache License 2.0](LICENSE)

---

<p align="center">
  <b>NSForge</b> — 讓 AI 的符號推理精確可靠<br>
  <i>Where Neural Meets Symbolic</i>
</p>
