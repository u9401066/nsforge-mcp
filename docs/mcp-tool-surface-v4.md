# MCP Tool Surface v4：安全、可驗證、可濃縮的執行面

> Date: 2026-08-31  
> Status: Implementing  
> Target: NSForge 0.4.0 / MCP Python SDK 2.1.x

## 1. 目的

NSForge 0.4.0 在不移除既有 91 項能力的前提下，將 MCP 面從「函式目錄」升級為「可信工作流介面」。本版優先修復會讓工具執行任意 Python、寫出工作目錄或在驗證失敗後仍產碼的邊界，再建立不可變 run／artifact／verification evidence、真實 phase events、精簡 tool profiles 與可觀測性。

Tasks extension 尚未由 Python SDK 2.1.1 實作，本版不自訂同名協議；長任務繼續使用 progress、run resources 與 phase events。

## 2. 不變量

1. **相容能力不消失**：`legacy` profile 保留 v0.3.0 預設 82 tools；`full` 保留 91 tools。既有工具名稱、必要參數與成功 payload 不因 profile 架構被刪除。
2. **不執行輸入文字**：所有外部 expression 必須經單一 allowlist parser；禁止 `eval`、任意 attribute、import、lambda、comprehension 與非允許函式。
3. **路徑不可逃逸**：repository category、artifact name 與 export path 經正規化及 containment 檢查；遠端 profile 只可寫 artifact root。
4. **驗證失敗不產碼**：codegen eligibility 同時要求 provenance 完整與可信 verification evidence 成功。`verified=false`、caller assertion 或過期 evidence 都不得產碼。
5. **出生證明不可偽造**：strict workflow 的 provenance entry、verification evidence、phase event、run 與 artifact 由 application kernel 產生，內容以 canonical SHA-256 串接；工具輸入不得直接把任意字串升格為 trusted evidence。
6. **讀取用 resource、動作用 tool**：manifest、health、run、artifact 與 session snapshot 優先透過 resources；tools 保留相容 alias，但 compact profiles 不重複暴露純讀取入口。
7. **固定 discovery surface**：profile 只在 server 建立時決定；同一連線內不動態增刪 tools。health 必須回報實際已註冊 surface。
8. **單一狀態提交**：strict workflow 以 application Unit of Work 寫入 SQLite revision store；event、run、evidence 與 artifact metadata 同 transaction 提交。
9. **租戶預設拒絕跨界**：每筆 strict state 帶 tenant id；resource lookup、subscription 與 artifact resolve 都必須使用相同 tenant scope。沒有可信 IdP 時，一個 server instance 仍視為單一 trust boundary。
10. **可觀測但不洩密**：tool／session／run correlation id 進入 OpenTelemetry span 與 structured logs；不記錄完整 expression、code、token 或 artifact bytes。

## 3. Tool profiles

Profiles 是固定的 server 啟動設定，不是呼叫端可任意切換的參數。

| Profile | 用途 | Surface 原則 |
|---|---|---|
| `legacy` | v0.3 相容，亦為 0.4 預設 | 原 82 個非 music tools，schema hash 必須維持 |
| `workflow` | agent 的建議精簡面 | 約 15–20 個 canonical workflow tools；讀取改走 resources |
| `scientific` | 無 session 的符號計算／驗證 | calculate、simplify、verify、expression 的嚴格核心 |
| `interactive` | 人機步進推導 | workflow 加 session 編輯、handoff 與人工輸入入口；人工輸入永遠 untrusted |
| `full` | discovery／除錯／完整相容 | 91 tools，包含 opt-in music 能力 |

`NSFORGE_TOOL_PROFILE` 選擇 profile。未設定時為 `legacy`；舊 `NSFORGE_ENABLE_MUSIC=1` 仍將 legacy surface 擴為 91，以保留既有行為。未知 profile 必須啟動失敗，不得靜默 fallback。

### Canonical workflow surface

compact profile 以以下意圖為核心，實際名稱由中央 `ToolSpec` registry 鎖定：

- 任務：plan、run、explore。
- 符號運算：parse／calculate、simplify、solve、limit、differentiate、integrate。
- 驗證：equality、boundary、dimensions。
- 推導：start、apply／record、snapshot、complete、abort。
- 產碼：只接受 verified run／artifact reference 的 pseudocode／code compile。

不得用一個 mega-tool 取代所有符號運算；保持單一決定性動作，讓 provenance 能精確指出出生工具。

## 4. ToolSpec 與契約

中央 `ToolSpec` 是 tool 名稱、profile membership、title、annotations、deprecation alias、輸入限制、輸出模型與 resource effect 的單一真相。manifest、runtime registration、health、測試與文件皆由同一 registry 產生或驗證。

- legacy handlers 保留寬鬆輸出，以 golden payload 防退化。
- workflow／scientific strict surface 對未知欄位 `forbid`，對 enum、數值範圍、identifier 與 URI 套明確限制。
- 統一新增 `execution_status`、`verification_status`、`run_id`、`correlation_id` 與 `resources`；既有 `success`／`verified` 欄位在 legacy payload 保留。
- 錯誤分為 validation、execution、verification、policy、timeout、cancelled；handled failure 仍保留 structured payload 並正確設 `isError`。
- descriptions 只保留選擇工具所需資訊；長範例與教學移到 docs／prompt，input field 本身必須有 description 與限制。

## 5. Strict provenance kernel

### 5.1 物件

- `Run`: tenant、profile、status、input digest、revision、開始／完成時間。
- `PhaseEvent`: 單調 sequence、phase、status、tool、parent digest、payload digest、timestamp。
- `ProvenanceNode`: entity digest、producer、canonical input/output digests、parent digests。
- `VerificationEvidence`: verifier、subject digest、policy、outcome、details digest、created revision。
- `Artifact`: immutable SHA-256 id、media type、size、producer run、verification evidence id、storage locator。

所有 id 由 server 產生。Caller 可提交候選 expression／manual step，但只能得到 `untrusted-input` 節點；只有 kernel 執行的 deterministic tool 與 verifier 能產生 trusted node／evidence。

### 5.2 Codegen gate

codegen eligibility 必須滿足：

1. run 尚未被取代或取消；
2. final subject digest 等於 evidence subject digest；
3. evidence outcome 為 pass，且 verifier policy 符合工具要求；
4. provenance DAG 從 final subject 到全部 roots 完整且無 caller-trusted 節點；
5. artifact 由同 tenant 的 active revision 產生。

任何條件不符皆回 `verification_status=blocked`，不得產出 code bytes。

## 6. State、lifecycle 與執行

正式 lifecycle：`draft → running → verifying → verified | rejected → materialized → completed`，另可進入 `cancelled`／`failed`。completed／cancelled revision 不可再 mutation；修改須 fork 新 revision。

application service 負責 transaction 與狀態轉移；domain model 不自行讀寫檔案。0.4 的 strict kernel 使用 SQLite（WAL、foreign keys、tenant key、樂觀 revision）儲存；舊 JSON session／YAML formula repository 保留為 legacy adapter，不再是 strict run 的權威來源。

計算在有 deadline 的 bounded runner 中執行。Cancellation 只在 worker 真正結束後發 terminal event；若無法中止 thread，不得提前宣告 Finished。需要硬逾時的工作使用可終止 process。

## 7. MCP 2 primitives

- `nsforge://runs/{run_id}`：immutable run snapshot，tenant-scoped。
- `nsforge://runs/{run_id}/events`：ordered phase events。
- `nsforge://artifacts/{sha256}`：immutable artifact bytes／text，帶 MIME 與 immutable cache hint。
- 完成／產碼 tools 在既有 structured payload 外附 `ResourceLink`，不把大型 artifact 重複塞進上下文。
- phase event 同時驅動 provenance、MCP progress、持久化與 OTel event，避免四套各自漂移的 callback。
- resources 建立後可發 updated notification；subscriptions 只有在 tenant ownership 與 ACL 已建立時啟用。
- Resolve 用於注入 tenant、correlation、store、clock 與 event sink；不得把 client 可控字串當可信 principal。

## 8. 相容與發布 gate

0.4 必須新增以下回歸：

- legacy 82／full 91 的 name、description、input/output schema golden；既有 representative payload golden。
- malicious parser corpus、所有 MCP expression 入口與 timeout/resource-limit。
- category／artifact／music export traversal、symlink escape 與遠端寫入政策。
- failed verification never codegens；caller assertion、stale evidence、wrong tenant、wrong digest 均被拒。
- ToolSpec fail-closed coverage、每個 profile exact names、unknown profile／unknown strict field 拒絕。
- SQLite UoW rollback、revision conflict、immutable artifact、tenant isolation、event ordering。
- ResourceLink 可 resolve、wrong tenant 404、subscription update 不跨 tenant。
- stdio 與 Streamable HTTP 官方 Client smoke、Host／Origin regression。
- OTel span 的 tool/session/run correlation，且 sensitive payload 不進 attributes。
- sdist／wheel build、隔離安裝後 82／91 與 workflow smoke。

## 9. 發布與遷移

0.4.0 預設仍為 `legacy`，避免現有 client 因 discovery surface 突然改變。文件與 health 會推薦 agent 使用 `workflow`。待至少一個 minor cycle 的互通資料後，才另行決定是否在下一 major 將 compact profile 設為預設。

被 canonical tool 取代的 legacy 名稱只標 deprecated／replacement，不在 0.4 刪除。MCP Tasks、內建 OAuth 與跨 replica state 不做虛假宣稱；多副本部署需 shared store、artifact backend、distributed coordination 與可信 principal resolver。
