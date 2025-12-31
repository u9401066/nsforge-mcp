# Progress (Updated: 2026-01-01)

## Done

- ✅ Neural-Symbolic AI 概念討論與架構設計
- ✅ 設計文件建立：`docs/symbolic-reasoning-mcp-design.md`
  - 3.3 多步推導架構（Formula Knowledge Graph, Step Executor）
  - 3.4 推導 DSL 語法設計（YAML-based）
  - 3.5 Audio Amplifier 電路分析範例
  - 6.5 車輛碰撞與安全帶張力計算範例
  - 6.6 藥動學（Pharmacokinetics）推導範例
- ✅ Gap 分析：識別「推導規劃」為核心缺口
- ✅ MVP 定義：DSL Parser + Step Executor + Basic Verifier
- ✅ 研究 Lean4 tactic 系統（apply, rw, simp, intro, exact）
- ✅ 研究相關 DSL：Scallop, DreamCoder, SymPy strategies

## Doing

- 🔄 Test-Driven Design：定義核心測試題目

## Next

- 選擇 2-3 核心題目開始 prototype
  - 候選：RC 濾波器（Level 3）、碰撞力學（Level 3）、藥動學（Level 3.5）
- 實作 DSL Parser（解析 YAML 推導腳本）
- 實作 Step Executor（SymPy wrapper）
- 建立 MCP Server 骨架
- 合併 AGENTS.md 到 copilot-instructions.md（需解決編碼問題）
