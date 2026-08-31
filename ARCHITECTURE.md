# Architecture

NSForge MCP 架構文件（v0.3.0）

## 系統概覽

NSForge 是一個 Domain-Driven Design（DDD）的神經符號推導系統。AI 負責理解與編排；domain 與 infrastructure 中的確定性元件負責建立、變換、驗證及保存公式。`nsforge` 核心不依賴 MCP，`nsforge_mcp` 是協議邊界。

```mermaid
flowchart TB
    HOST["MCP host / agent"]
    MCP["MCPServer 2.1.1<br/>protocol 2026-07-28"]
    CONTRACT["91-tool catalog<br/>82 default + 9 music opt-in"]
    PRIMITIVES["resources · resource template · prompt"]
    APP["Application<br/>orchestrator · explorer · use cases"]
    DOMAIN["Domain<br/>sessions · formulas · provenance · codegen"]
    INFRA["Infrastructure<br/>SymPy · verification · repositories · adapters"]
    STORE[("YAML / JSON")]
    SOURCES["Wikidata · BioModels · SciPy"]

    HOST --> MCP
    MCP --> CONTRACT
    MCP --> PRIMITIVES
    CONTRACT --> APP
    PRIMITIVES --> APP
    APP --> DOMAIN
    APP --> INFRA
    INFRA --> DOMAIN
    INFRA --> STORE
    INFRA --> SOURCES
```

## 分層與依賴方向

### Domain（`src/nsforge/domain/`）

純業務規則與值物件，不做 I/O，也不依賴 MCP 或 infrastructure。

| 元件 | 責任 |
| --- | --- |
| `derivation_session.py` | 推導會話、步驟、回滾與 session 持久化模型 |
| `formula.py` / `entities.py` / `value_objects.py` | 公式、實體與值物件 |
| `task_spec.py` | 宣告式 Derivation Task Spec（DTS） |
| `provenance.py` | 工具出生證明帳本與完整性不變量 |
| `codegen.py` | 從已驗證、溯源完整的推導實體化程式碼 |
| `suggester.py` | 候選下一步的確定性排序 |
| `services.py` / `safe_parse.py` | domain 服務介面與安全解析 |

### Application（`src/nsforge/application/`）

協調 domain 與 infrastructure，不承擔傳輸細節。

| 元件 | 責任 |
| --- | --- |
| `task_orchestrator.py` | DTS 的 concept → symbol → derivation → verify → code 流程與 critic-retry |
| `explorer.py` | base 與 alternatives 分支探索、驗證與排序 |
| `use_cases.py` | 推導與公式管理用例 |

### Infrastructure（`src/nsforge/infrastructure/`）

可替換的計算、資料來源及持久化 adapter。

| 元件 | 責任 |
| --- | --- |
| `sympy_engine.py` / `verifier.py` | 符號運算與驗證 |
| `derivation_repository.py` | 已存推導的 thread-safe repository 與 atomic YAML 寫入 |
| `timeout.py` | 可終止失控推導的 process timeout |
| `dimensional.py` / `parsing.py` | 維度單一真相與解析 adapter |
| `adapters/` | Wikidata、BioModels、SciPy 等開放來源 |

### MCP boundary（`src/nsforge_mcp/`）

MCP Python SDK 2.1.1 的薄協議層。

| 元件 | 責任 |
| --- | --- |
| `server.py` | `MCPServer` factory、lifespan、cache hints 與 transport 啟動 |
| `composition.py` | process-wide `Services` 組合根 |
| `config.py` | optional module 與 transport 安全設定 |
| `envelope.py` | 全工具的結構化輸出、相容錯誤 envelope 與 protocol `isError` |
| `tool_contract.py` | title、icon、annotations、namespaced `_meta` 的單一真相 |
| `introspection.py` | capability manifest 與 health payload |
| `primitives.py` | resources、resource template 與 prompt |
| `tools/` | 11 個模組、91 個工具的 adapter；預設註冊 82 個 |

依賴方向保持為：

```text
MCP boundary → Application → Domain ← Infrastructure
```

## MCP 2.1 協議契約

NSForge 0.3.0 採用 `mcp>=2.1.1,<3`，對應協議修訂版 `2026-07-28`。升級是加法式的：v0.2.4 的工具名稱、輸入 schema、輸出 schema 與既有回應字典受到 `mcp` gate 的 hash／payload 回歸測試保護。

每個工具在註冊邊界統一取得：

- `title` 與 NSForge icon；
- `readOnlyHint`、`destructiveHint`、`idempotentHint`、`openWorldHint`；
- `org.nsforge/*` namespaced `_meta`；
- 明確設定 `structured_output=True`；保留 SDK 1.25 已提供的 output schema 與 dual-channel 結果。

SDK 1.25 已讓成功結果同時提供文字內容與 `structuredContent`；升級後兩個 channel 的 body／hash 維持不變。既有 handled error 與未處理例外也維持原本 JSON body，本次另以 MCP `isError=true` 提供明確的失敗 semantic signal；數學驗證結果為 false、但沒有 `error` 欄位時仍是正常工具結果。

`task_run` 與 `task_explore` 接受 MCP `Context`，在工作開始與結束回報 progress。同步工具由 SDK 的 worker thread 執行，因此可變狀態不能假設單執行緒。

## Discovery primitives

Tools 仍是主要寫入／計算介面；MCP 2.1 primitives 以加法方式提供 discovery-first UX。

| 類型 | 名稱 | 用途 |
| --- | --- | --- |
| Resource | `nsforge://manifest` | 工具、模組、gate 與 MCP 契約 |
| Resource | `nsforge://health` | runtime、SDK、協議、引擎與 active tool inventory |
| Resource | `nsforge://north-star` | provenance 北極星不變量 |
| Resource template | `nsforge://derivations/{result_id}` | 依 ID 讀取已存公式 metadata 與 lineage 摘要 |
| Prompt | `forge_verified_derivation` | 產生 provenance-first 的驗證推導工作流 |

`tools/list`、resource／template／prompt list 及 server discovery 使用五分鐘 public cache hint；`health` 等動態 resource read 不套用這個 cache。

## Tool surface

| 模組 | 數量 | 說明 |
| --- | :---: | --- |
| Derivation | 31 | Stateful session、推導步驟、repository、handoff |
| Calculate | 12 | 極限、級數、求和、不等式、機率、數值 |
| Simplify | 14 | 進階代數與 Laplace／Fourier 變換 |
| Verify | 6 | 等價、導數、積分、解、維度與反向驗證 |
| Formula | 6 | Wikidata、BioModels、SciPy 等公式來源 |
| Codegen | 4 | Python、LaTeX、Markdown、SymPy script |
| Expression | 3 | parse、validate、extract symbols |
| Task | 3 | plan、run、explore |
| Suggest | 1 | retrieval-augmented next-step ranking |
| Meta | 2 | health 與 manifest tools |
| Music（opt-in） | 9 | symbolic audio demo；`NSFORGE_ENABLE_MUSIC=1` |

總目錄 91；預設 82。完整名稱與 metadata 以 [`docs/tools-reference.md`](docs/tools-reference.md) 與 [`docs/agent/capabilities.json`](docs/agent/capabilities.json) 為準。

## Transport 與部署邊界

stdio 是預設 transport，也是本機 host 整合的建議值。Streamable HTTP 必須明確設定 `NSFORGE_MCP_TRANSPORT=streamable-http`；預設只綁定 `127.0.0.1:8000/mcp`。

所有 HTTP bind 都明確傳入 MCP 2.1 `TransportSecuritySettings`，以 Host／Origin allowlist 防範 DNS rebinding。非 loopback 位址還必須設 `NSFORGE_MCP_ALLOW_REMOTE=1` 與非空的 `NSFORGE_MCP_ALLOWED_HOSTS`；瀏覽器 caller 另設精確的 `NSFORGE_MCP_ALLOWED_ORIGINS`。Origin allowlist 留空只允許沒有 Origin header 的非瀏覽器 client，任何 supplied Origin 都會被拒絕。這些設定只是 transport 防護，不是驗證機制；對外服務仍需由 reverse proxy／gateway 提供真實的 authentication、authorization 與 TLS。

Session registry、legacy current-session fallback 與 saved-result repository 都是 process-wide，共同構成單一 trust boundary。多 client 必須在每個 stateful derivation call 傳入明確 `session_id`，且部署時每 tenant 使用獨立 instance；legacy fallback 僅供單 client 相容，不提供 caller isolation。v0.3.0 的 stateful derivation 是單 process／單 replica；未加入 shared durable store 與 distributed locking 前，不支援在 load balancer 後直接水平擴展。若開啟 `NSFORGE_MCP_HTTP_JSON_RESPONSE=1`，request-scoped progress 沒有串流通道，因此需要 `task_run`／`task_explore` progress 時應保留預設 false。

## 狀態與並行安全

MCP 2.x 可能讓多個工具同時進入同一 process。NSForge 因此在三個層次保護狀態：

1. `SessionManager` 鎖保護 session registry。
2. 每個 `DerivationSession` 以 re-entrant lock 序列化 mutation 與複合 transaction；compound read 取得 detached point-in-time snapshot。
3. `DerivationRepository` 以 re-entrant lock 保護索引，並用同目錄暫存檔與 atomic replace 寫入 YAML。

不同 session 仍可並行；同一 session 的 mutation 不會交錯，compound read 只看見單一時間點，持久化也不會向 reader 暴露半寫檔案。這是 process 內資料一致性，不取代 explicit `session_id` 或 tenant isolation。

## 典型資料流

```mermaid
sequenceDiagram
    participant H as MCP host
    participant M as MCPServer
    participant T as Tool adapter
    participant A as Application
    participant D as Domain
    participant I as Infrastructure

    H->>M: tools/call
    M->>T: validated inputs + Context
    T->>A: use case / orchestration
    A->>D: deterministic state transition
    A->>I: compute / verify / persist
    I-->>A: result + evidence
    A-->>T: legacy-compatible dict
    T-->>M: structuredContent + text
    M-->>H: result (isError only for application error)
```

## 驗證契約

`python scripts/check.py` 是單一 ground truth，共 12 個 gate：

```text
lint · format · type · import · manifest · mcp · test · bench · generic · provenance · harness · diff
```

其中 `mcp` gate 以 official in-memory client 檢查預設 82／完整 91 工具、v0.2.4 schema 與 payload 相容、全工具 metadata、structured output、application-error `isError`、resources、prompt、cache hints 及 legacy-client mode。

## 相關文件

- [README.md](README.md) — 安裝、使用與部署設定
- [MCP v2 migration](docs/mcp-v2-migration.md) — 升級設計與相容性矩陣
- [Tool reference](docs/tools-reference.md) — 完整工具與 primitives 參考
- [Reification ladder](docs/reification-ladder-direction.md) — 北極星與長期方向
- [CONSTITUTION.md](CONSTITUTION.md) — 開發原則
