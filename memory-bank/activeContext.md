# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

設計「公式知識庫」架構 - 讓推導出的公式可以儲存、重用、增長。

**關鍵發現**：sympy-mcp 已經可以執行藥動學推導（ODE 求解、代入、簡化），
不需要額外的推導引擎！NSForge 的價值在於「知識管理」而非「計算」。

## Current Goals

- 建立 formulas/ 知識庫結構
- 設計公式 YAML 格式（含狀態追蹤、文獻引用）
- 實作公式儲存/查詢 MCP 工具

## 📝 今日變更

| 檔案 | 變更內容 |
|------|----------|
| `.github/copilot-instructions.md` | 整合 AGENTS.md 內容 |
| `.vscode/mcp.json` | 修正 MCP 配置，使用 ${workspaceFolder} |
| `src/nsforge_mcp/server.py` | 修正 FastMCP 參數 |
| `AGENTS.md` | 已刪除（整合進 copilot-instructions） |
| `vendor/sympy-mcp/` | 新增 sympy-mcp 依賴 |

## ⚠️ 待解決

（已解決：copilot-instructions.md 編碼問題）

## 💡 重要決定

- **公式知識庫三層架構**：
  - principles/ - 基礎物理定律（不變）
  - domain/ - 領域公式（有文獻）
  - derived/ - 推導公式（可增長，分 proposed/verified）
- **sympy-mcp 足以執行推導**，NSForge 專注知識管理
- 公式有生命週期：proposed → verified → deprecated
- 詳見 decisionLog.md

## 📁 相關檔案

```
.vscode/mcp.json           # MCP 配置
vendor/sympy-mcp/          # sympy-mcp 依賴
formulas/                  # 🆕 公式知識庫（待建立）
  ├── principles/          # 基礎原理
  ├── domain/              # 領域公式
  └── derived/             # 推導公式
      ├── proposed/        # 待檢驗
      └── verified/        # 已檢驗
```

## 🔜 下一步

1. 建立 formulas/ 目錄結構
2. 建立第一批基礎原理 YAML
3. 實作 save_derived_formula() MCP 工具
4. 儲存今天推導的溫度校正藥動學模型

---
*Last updated: 2026-01-02*
