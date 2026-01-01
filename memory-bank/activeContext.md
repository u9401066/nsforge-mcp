# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

完成 NSForge 推導框架的第一個實際應用範例：Power Amp 交聯電容設計。展示了從理想 RC 高通濾波器公式開始，逐步加入修正項（輸出阻抗、電容ESR、喇叭阻抗曲線）的完整推導流程。

## Current Goals

- 準備 Git commit - 實例推導範例
- 下一步：創建藥物動力學領域規劃文檔

## 📝 進行中的變更

| 檔案 | 變更內容 |
|------|----------|
| `docs/symbolic-reasoning-mcp-design.md` | 完整設計文件（架構、DSL、範例、Gap 分析、MVP） |

## ⚠️ 待解決

- copilot-instructions.md 有 Unicode 編碼問題，無法合併 AGENTS.md

## 💡 重要決定

- 採用 Test-Driven Design 方法：先定義題目，再做 prototype
- 推導規劃由 Agent + 人協作，SymPy 執行計算
- MVP 暫不含 Lean4 形式驗證
- 詳見 decisionLog.md

## 📁 相關檔案

```
docs/
  symbolic-reasoning-mcp-design.md  # 主設計文件

參考：
  - Lean4 tactic 系統 (apply, rw, simp)
  - Scallop (provenance tracking)
  - DreamCoder (program synthesis)
```

## 🔜 下一步

1. 選擇 2-3 核心題目做 prototype（RC 濾波器、碰撞力學、藥動學）
2. 實作 DSL Parser + Step Executor
3. 建立 MCP Server 骨架

---
*Last updated: 2026-01-01*
