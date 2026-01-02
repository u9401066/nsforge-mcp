# 🔥 Neurosymbolic Forge (NSForge)

> **"Forge" = 透過驗證式推導來創造新公式**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

🌐 [English](README.md) | **繁體中文**

## 🔨 核心概念：「Forge（鍛造）」

**NSForge 不是公式資料庫** — 而是一個**推導工廠**，用來創造新公式。

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   🔨 FORGE = 透過推導創造新公式                                              │
│                                                                             │
│   輸入：基礎公式                輸出：新的推導公式                            │
│   ┌─────────────────────┐       ┌─────────────────────────────────────┐    │
│   │ • 一室模型          │       │ 溫度修正消除率模型                   │    │
│   │ • Arrhenius 方程    │  ──→  │ 體脂調整分布容積                     │    │
│   │ • Fick 擴散定律     │       │ 腎功能劑量調整                       │    │
│   │ • ...               │       │ 自訂 PK/PD 模型                      │    │
│   └─────────────────────┘       └─────────────────────────────────────┘    │
│         (來自 sympy-mcp)                    (存放於 NSForge)               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ 三大核心能力

| 能力 | 說明 | 工具 |
| ---- | ---- | ---- |
| **推導 (DERIVE)** | 組合基礎公式創造新公式 | `substitute`, `simplify`, `differentiate`, `integrate` |
| **驗證 (VERIFY)** | 多種方法確保正確性 | `check_dimensions`, `verify_derivative`, `symbolic_equal` |
| **存儲 (STORE)** | 保存推導公式與完整溯源 | `formulas/derivations/` 儲存庫 |

---

## � 生態系：不重複造輪子

NSForge 與其他 MCP 伺服器協作，而非競爭：

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP 公式生態系                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  sympy-mcp                                                                  │
│  └── 基礎公式：F=ma、PV=nRT、Arrhenius...                                   │
│  └── 物理常數：c、G、h、R...（SciPy CODATA）                                │
│  └── 符號運算引擎                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  medical-calc-mcp（75+ 工具）                                                │
│  └── 臨床評分：APACHE、SOFA、GCS、MELD、qSOFA...                            │
│  └── 醫學計算：eGFR、IBW、BSA、MEWS...                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  nsforge-mcp ← 你在這裡                                                      │
│  └── 🔨 推導框架：組合、驗證、生成程式碼                                     │
│  └── 📁 推導成果庫：存放創造的公式與溯源資訊                                 │
│  └── ✅ 驗證層：維度分析、逆向驗證                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### NSForge 存放什麼？

| ✅ 屬於 NSForge | ❌ 不屬於（請用其他工具） |
| --------------- | ------------------------ |
| 溫度修正藥物消除率 | 基礎物理公式（sympy-mcp） |
| 體脂調整分布容積 | 物理常數（sympy-mcp） |
| 腎功能劑量調整 | 臨床評分（medical-calc-mcp） |
| 自訂複合 PK/PD 模型 | 教科書公式（參考資料） |

---

## �🎬 工作流程圖

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   用戶問題                        NSForge 處理流程                          │
│   ════════                        ════════════════                          │
│                                                                            │
│   "藥物在 38°C 發燒病人           1️⃣ 查詢公式知識庫                          │
│    體內的濃度變化？"         ──→     ├─ 一室藥動學模型: C(t) = C₀·e^(-kₑt)   │
│                                     └─ Arrhenius 方程: k(T) = A·e^(-Ea/RT)  │
│                                                                            │
│                                  2️⃣ 組合推導                                │
│                                     ├─ 代入 k(T) 到藥動學模型               │
│                                     └─ 得到溫度修正公式                     │
│                                                                            │
│                                  3️⃣ 符號計算 (SymPy)                        │
│                                     └─ C(t,T) = C₀·exp(-kₑ,ref·t·exp(...)) │
│                                                                            │
│                                  4️⃣ 驗證結果                                │
│                                     ├─ T=37°C 時退化為標準模型 ✓            │
│                                     └─ 維度檢查通過 ✓                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 為什麼需要 NSForge？

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   問題：LLM 直接做數學推導                                                   │
│   ══════════════════════════                                                │
│                                                                             │
│   ❌ 可能算錯（幻覺）      ❌ 每次答案不同      ❌ 無法驗證正確性            │
│                                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│   解決：LLM + NSForge                                                       │
│   ═══════════════════                                                       │
│                                                                             │
│   LLM 負責：                        NSForge 負責：                          │
│   ┌─────────────────────┐          ┌─────────────────────┐                 │
│   │ • 理解用戶問題      │          │ • 存儲驗證過的公式  │                 │
│   │ • 規劃推導策略      │    ──→   │ • 精確符號計算      │                 │
│   │ • 解釋結果          │          │ • 追蹤推導來源      │                 │
│   └─────────────────────┘          │ • 驗證結果正確性    │                 │
│      「理解與規劃」                 └─────────────────────┘                 │
│                                       「計算與驗證」                        │
│                                                                             │
│   ✅ 計算保證正確      ✅ 結果可重現      ✅ 推導可追溯                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 推導成果庫架構

NSForge 存儲**推導公式**，並追蹤完整溯源：

```text
formulas/
└── derivations/                    ← 所有推導公式存放於此
    ├── README.md                   ← 文件
    └── pharmacokinetics/           ← 藥動學模型推導
        ├── temp_corrected_elimination.md   ← 溫度修正消除率
        └── fat_adjusted_vd.md              ← 肥胖調整分布容積
```

### 每個推導成果包含

- LaTeX 數學表達式
- SymPy 可計算形式  
- **推導來源**：組合了哪些基礎公式
- **推導步驟**：實際的推導過程
- **驗證狀態**：維度分析、極限情況驗證
- 臨床情境與使用指引
- YAML 元資料供程式化存取

### 範例：溫度修正藥物消除率

```yaml
id: temp_corrected_elimination
name: 溫度修正藥物消除率
expression: k_ref * exp((E_a / R) * (1/T_ref - 1/T))
derived_from:
  - one_compartment_model      # 來自 sympy-mcp
  - arrhenius_equation         # 來自 sympy-mcp
verified: true
verification_method: dimensional_analysis
```

---

## ✨ 功能特色

| 類別 | 功能 |
| ---- | ---- |
| 🔢 **符號計算** | 微積分、代數、線性代數、ODE/PDE |
| 📖 **公式管理** | 存儲、查詢、版本控制、來源追蹤 |
| 🔄 **推導組合** | 多公式組合、變數替換、條件修改 |
| ✅ **結果驗證** | 維度檢查、邊界條件、逆向驗證 |
| 🐍 **程式碼生成** | 從符號公式生成 Python 計算函數 |

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

```text
用戶：計算 ∫(x² + 3x)dx 並驗證結果

Agent 呼叫 NSForge：
→ 結果：x³/3 + 3x²/2 + C
→ 驗證：d/dx(x³/3 + 3x²/2) = x² + 3x ✓
→ 步驟：分解積分 → 冪次規則 → 合併
```

**物理推導**：

```text
用戶：理想氣體等溫膨脹做的功？

Agent 呼叫 NSForge：
→ W = nRT ln(V₂/V₁)
→ 推導：PV=nRT → P=nRT/V → W=∫PdV → 積分
```

**演算法分析**：

```text
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
| ---- | ---- |
| `symbolic_calculate` | 符號數學計算 |
| `physics_formula` | 物理公式推導 |
| `chemistry_calculate` | 化學計算 |
| `algorithm_analyze` | 演算法分析 |
| `verify_derivation` | 推導驗證 |
| `unit_convert` | 單位換算 |

## 🏗️ 專案結構

本專案採用 **DDD (Domain-Driven Design)** 架構，Core 與 MCP 分離：

```text
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

**NSForge** — 透過驗證式推導鍛造新公式 | *Where Neural Meets Symbolic*
