# Project Brief

> 📌 此檔案描述專案的高層級目標和範圍，建立後很少更改。

## 🎯 專案目的

**Neurosymbolic Forge (NSForge)** — 一個 MCP Server，把「概念 → 實體」的每一階都工具化：讓 AI 只負責翻譯與編排，工具負責決定性地產出可驗證、可追溯的符號 / 推導 / 演算法。

核心不是「公式資料庫」，而是**推導工廠（Forge）**：以基礎公式為輸入，透過可驗證的步進式推導，CREATE 出帶完整溯源的新公式。

## 🧭 北極星判準

> 凡是出現在最終結果裡的符號 / 等式 / 數值 / 程式碼，都必須有一次工具調用作為它的「出生證明」(provenance)。AI 不得徒手生出任何一個。

成功 = AI 徒手算的東西趨近於零。詳見 `docs/reification-ladder-direction.md`。

## 👥 目標用戶

- 需要精確、可重現符號推導的研究者/工程師（藥動學、化學動力學、物理、電路…）
- 使用支援 MCP 的 AI 客戶端（VS Code + Copilot、Claude 等）進行「人＋AI 概念層協作」的使用者

## 🏆 成功指標

- [ ] 每個最終結果的實體都有工具產生的 provenance（可追溯）
- [ ] 相同輸入 = 相同輸出（推導可重現）
- [ ] 「用工具列出當前實體」隨時可查（符號/假設/單位/算式/推導樹）
- [ ] 概念 → 算式 → 推導 → pseudocode → code 五階皆可工具化實體化

## 🚫 範圍限制

- 不做基礎公式資料庫（Agent 已知的 F=ma、PV=nRT 等靠 Agent/sympy-mcp）
- 不自建符號運算引擎（計算交給 sympy-mcp 後端）
- 不做論文檢索（用 RAG / 外部 API）
- 不自建最佳化求解器（交給 USolver 協作）

## 📝 備註

- 生態系分工：sympy-mcp（計算）＋NSForge（推導/溯源/實體化）＋USolver（最佳化）
- 架構方向詳見 `docs/reification-ladder-direction.md`

---
*Created: 2025-12-15 · Realigned to NSForge: 2026-07-07*
