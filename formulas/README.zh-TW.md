# � NSForge 公式庫

> **不是公式資料庫 - 是推導成果庫**

🌐 [English](README.md) | **繁體中文**

## 🎯 目的

此目錄存放**推導成果** - 透過 NSForge 驗證式符號推導流程所創建的公式。

### 這裡不存放什麼

| ❌ 不是這個 | ✅ 請使用 |
| ----------- | --------- |
| 基礎物理公式 | [sympy-mcp](https://github.com/space-cadet/sympy-mcp) (SymPy 物理) |
| 物理常數 | [sympy-mcp](https://github.com/space-cadet/sympy-mcp) (SciPy 常數) |
| 臨床評分工具 | [medical-calc-mcp](https://github.com/hsieh-cy/medical-calc-mcp) |
| 教科書公式 | 標準參考資料 |

### 這裡存放什麼

- **推導公式**：結合基礎公式所創建的新公式
- **驗證結果**：每個公式都有驗證狀態
- **溯源追蹤**：知道每個公式從哪裡來
- **臨床情境**：真實世界應用指引

## 📁 結構

```text
formulas/
├── README.md              ← 你在這裡
└── derivations/           ← 所有推導公式
    ├── README.md          ← 詳細文件
    └── pharmacokinetics/  ← 藥動學模型推導
        ├── temp_corrected_elimination.md
        └── fat_adjusted_vd.md
```

## 🔗 生態系

```text
┌─────────────────────────────────────────────────────────────┐
│                   MCP 公式生態系                             │
├─────────────────────────────────────────────────────────────┤
│  sympy-mcp                                                   │
│  └── 基礎公式：F=ma、PV=nRT、Arrhenius...                   │
│  └── 物理常數：c、G、h、R...                                │
│  └── 符號運算引擎                                            │
├─────────────────────────────────────────────────────────────┤
│  medical-calc-mcp（75+ 工具）                                │
│  └── 臨床評分：APACHE、SOFA、GCS、MELD...                   │
│  └── 醫學計算：eGFR、IBW、BSA...                            │
├─────────────────────────────────────────────────────────────┤
│  nsforge-mcp                                                 │
│  └── 推導框架：驗證、代入、簡化                              │
│  └── 程式碼生成：從公式產生 Python 函數                      │
│  └── 此庫：存放驗證過的推導結果                              │
└─────────────────────────────────────────────────────────────┘
```

## 📖 另見

- [derivations/README.md](derivations/README.md) - 完整文件
- [範例：溫度修正消除率](derivations/pharmacokinetics/temp_corrected_elimination.md)
- [範例：體脂調整分布容積](derivations/pharmacokinetics/fat_adjusted_vd.md)
