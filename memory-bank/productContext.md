# Product Context

> 📌 此檔案描述專案的技術架構和產品定位，專案初期建立後較少更新。

## 📋 專案概述

**專案名稱**：Neurosymbolic Forge (NSForge) — `nsforge-mcp`

**一句話描述**：把「概念 → 實體」每一階工具化的 MCP Server；AI 編排、工具實體化，產出可驗證可追溯的符號/推導/演算法。

**目標用戶**：使用支援 MCP 的 AI 客戶端進行精確符號推導的研究者與工程師。

## 🏗️ 架構

實體化階梯（Reification Ladder）：

```
概念層（人＋AI 對話）
  ↓ reify
算式實體化層（符號/假設/單位/算式）
  ↓ derive
公式推導層（決定性工具、溯源、可回滾）
  ↓ compile
演算法層（pseudocode → code，綁回溯源）
```

### 分層架構 (DDD)

```
Presentation → Application → Domain ← Infrastructure
```
- 實體化狀態模型 / Concept / Provenance 入 Domain
- 工具編排入 Application
- sympy-mcp 計算後端、檔案存取入 Infrastructure

## ✨ 核心功能

- 🔨 步進式推導框架（每步可注入人類知識 + 溯源）
- 🔤 算式實體化（符號註冊表 + 假設 + 單位）
- ✅ 驗證層（維度分析、反向驗證、符號等價）
- 📜 程式碼/報告生成（從已驗證步驟組裝，非 AI 徒手生成）
- 🌐 外部公式搜尋（Wikidata、BioModels、SciPy 常數）
- 🔗 生態橋接（sympy-mcp handoff、USolver 最佳化）

## 🔧 技術棧

| 類別 | 技術 |
|------|------|
| 語言 | Python 3.12+ |
| 套件管理 | uv（優先） |
| 符號計算 | SymPy / sympy-mcp（後端） |
| 協定 | MCP (Model Context Protocol) |
| Linting | Ruff, ty |
| 測試 | pytest |

## 📦 生態系分工

| MCP | 職責 |
|-----|------|
| sympy-mcp (32 工具) | 基礎公式、常數、符號計算引擎（ODE/PDE/矩陣） |
| **nsforge-mcp (76 工具)** | 推導框架、溯源存檔、驗證、實體化、外部搜尋、橋接 |
| usolver-mcp（選配） | 為 NSForge 推導的公式找最佳參數值 |

---
*Last updated: 2025-12-15 · Realigned to NSForge: 2026-07-07*