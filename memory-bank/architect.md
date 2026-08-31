# System Architect

> 📌 此檔案記錄 NSForge 的現行架構與重大架構決策；架構變更時同步更新。

## 現行架構（2026-08-31）

```mermaid
flowchart LR
    H["MCP host / client"] -->|"stdio（default）或 Streamable HTTP（opt-in）"| M["MCPServer 2.1.1\nprotocol 2026-07-28"]
    M --> E["Envelope + tool contracts\n91 catalog / 82 default"]
    M --> P["Resources / prompt / cache / progress"]
    E --> A["Application\nTaskOrchestrator / Explorer"]
    E --> D["Domain\nDerivationSession / Formula / Provenance"]
    A --> D
    D --> I["Infrastructure\nSymPy / formula adapters / repository"]
    I --> F["Atomic JSON / YAML persistence"]
```

依賴方向保持為：

```text
MCP boundary → Application → Domain ← Infrastructure
```

- `src/nsforge/domain/` 不做 I/O，也不依賴 MCP 或 infrastructure。
- `src/nsforge_mcp/composition.py` 是 process-wide object graph 的唯一組裝點。
- `src/nsforge_mcp/server.py` 只處理 MCP metadata、lifespan 與 transport wiring。
- `EnvelopeMCP` 在單一註冊邊界為所有工具加 error semantics、title、icons、
  annotations、`_meta` 與明確 structured output，不複製 91 個 handler contract。
- Capability manifest v3 與 `mcp` gate 鎖定 live discovery、legacy payload、resources、
  prompt、progress、stdio framing，以及 default／full tool surface。

## ADR-004：MCP 2.1 boundary、transport 與並行模型

**日期**：2026-08-31
**狀態**：Accepted

### 背景

MCP Python SDK 2.x 以 `MCPServer` 取代 `FastMCP`，同步 handlers 可能在 worker
threads 並行執行。NSForge 同時有 process-wide session registry、legacy current
session fallback、saved-result repository 與磁碟持久化；若只做 import 遷移，會暴露
lost update、torn read、半寫檔案與跨 client state 誤用。

### 決定

1. 使用 stable MCP SDK 2.1.1（dependency 支援 `>=2.1.1,<3`，lock 與 release gate
   固定驗證 2.1.1）及 protocol revision `2026-07-28`。
2. stdio 保持預設；Streamable HTTP 只在明確 opt-in 時啟動，預設綁 loopback。
3. 所有 HTTP bind 都傳入 `TransportSecuritySettings` 驗證 Host／Origin，防 DNS
   rebinding。Non-loopback 另要求 remote acknowledgement、非空 Host allowlist，並在
   server 外提供真正的 authentication、authorization 與 TLS。
4. Process-wide sessions、legacy fallback 與 repository 是單一 trust boundary。
   Multi-client 的每個 stateful derivation call 必須傳 explicit `session_id`；每 tenant
   部署獨立 instance。Legacy fallback 僅供 single-client 相容，不是 caller isolation。
5. `SessionManager`、每個 `DerivationSession` 與 `DerivationRepository` 使用 re-entrant
   locks；mutation／compound transaction 序列化，compound reads 與 completion 回傳
   detached point-in-time snapshots。JSON／YAML 使用同目錄 temp file + `os.replace`。
6. 不把 SDK 尚未實作的 MCP Tasks、deprecated SSE／Roots／Sampling／Logging，或沒有
   IdP 的假 OAuth 包裝成已支援功能。

### 結果與限制

- 不同 sessions 可並行；同一 session 的 mutation 不交錯，讀取只看到單一快照。
- 鎖與 atomic replace 保證單 process 一致性，不是跨 process distributed lock。
- Resource metadata／public cache hints 不是授權。Saved-derivation resource 只提供已
  儲存的 metadata 與 lineage 摘要，不宣稱完整 provenance ledger。
- `NSFORGE_MCP_HTTP_JSON_RESPONSE=1` 沒有 request-scoped notification wire，因此不
  串流 `task_run`／`task_explore` progress；需要進度時維持預設 streaming mode。

## 主要元件責任

| 元件 | 責任 |
| --- | --- |
| MCPServer / primitives | Protocol negotiation、discovery、resources、prompt、transport |
| Envelope / tool contract | 91 工具的統一 metadata、structured dual channel、`isError` |
| TaskOrchestrator / Explorer | L2/L3 編排、驗證、自我修正、候選探索 |
| DerivationSession | Stateful derivation、steps、point-in-time snapshots、JSON persistence |
| ProvenanceLedger | 工具來源 birth certificates；完整性是 codegen 前置條件 |
| DerivationRepository | Saved-result index、metadata/lineage snapshot、atomic YAML persistence |
| SymPy / adapters | Deterministic symbolic computation 與 open-world formula retrieval |
| Harness | 12 gates：程式品質、推導正確性、provenance、自描述與 MCP wire contract |

## 歷史決策摘要

- **ADR-001（2025-12-15）**：憲法／子法／Skills 規則層級；仍作 agent governance。
- **ADR-002（2025-12-15）**：採 DDD 邊界，domain 不依賴 I/O adapter；現行程式維持。
- **ADR-003（2025-12-15）**：uv 優先套件與 lockfile；現行 release／gate 維持。
- Lean4／Principles Library 是長期可選方向，不是 NSForge 0.3.0 runtime dependency。

---

*Last updated: 2026-08-31*
