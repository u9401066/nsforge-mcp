# Progress (Updated: 2026-01-07)

## Done

- 安裝 SymPy-MCP 到 vendor 目錄（2026-01-07）
  - 來源：https://github.com/sdiehl/sympy-mcp (48 stars)
  - 位置：vendor/sympy-mcp/
  - 工具數量：32 個
- 修復 .vscode/mcp.json 配置
- 啟用 NSForge (76 工具) + SymPy-MCP (32 工具) = 108 工具
- 🧭 方向收斂：新增 `docs/reification-ladder-direction.md`（實體化階梯）（2026-07-07）
- 🛠️ Agent 自駕基座 L0+L1（2026-07-07）
  - `scripts/check.py`：單一 ground-truth 驗證 harness（lint/format/type/import/manifest/test/diff）
  - `scripts/gen_capabilities.py` + `docs/agent/capabilities.json`：機器可讀能力清單（76 工具自描述）
  - `.github/workflows/ci.yml`：補上原本缺失的 CI
  - 修復繼承自 asset-aware-mcp 的假 harness（`full-check` 指向不存在路徑）
  - lint/format 基線轉綠；harness 揪出 41 個 mypy strict 型別債（7 檔案）
- 🚀 YOLO 三任務完成（2026-07-07）→ harness 7/7 全綠、78 工具
  - Task 1：修完 41 個 mypy strict 型別債（含 formula.py 過濾 None 真 bug）
  - Task 2：清除 agent harness 的 asset-aware 污染（刪 7 檔、重寫 5 核心為 NSForge）
  - Task 3：L2 DTS（domain/task_spec.py）+ L3 編排器骨架（application/task_orchestrator.py）+ task_plan/task_run 工具 + 測試 + 範例 JSON

## Doing

- （無）

## Next

- L3 編排器接上真實 derivation 引擎（目前 derivation/algorithm 階段為 PLANNED）
- 依 reification-ladder P1 實體檢視器 / P2 provenance ledger 推進
