# MCP Python SDK v2 遷移與工具翻新規格

> 日期：2026-08-31；基線：SDK 1.25.0；目標：SDK 2.1.1 stable、協定 2026-07-28。
> 狀態：v0.3.0 遷移記錄已完成；v0.4.0 trusted workflow 後續實作見第 9 節與
> [`mcp-tool-surface-v4.md`](mcp-tool-surface-v4.md)。

## 1. 版本決策

精確稱呼是「MCP Python SDK v2.1.1」與「MCP protocol revision
2026-07-28」；MCP 協定使用日期版號，不能把 JSON-RPC `"2.0"` 或 SDK major
誤稱為「MCP protocol 2.0」。

- 最新 stable SDK 是 `mcp 2.1.1`：[PyPI](https://pypi.org/project/mcp/2.1.1/)、
  [release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.1.1)、
  [latest](https://github.com/modelcontextprotocol/python-sdk/releases/latest)。
- 2.0.1 是舊支線的一次性 import-warning backport，不取代 2.1.1：
  [官方說明](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.1)。
- SDK 要求 Python `>=3.10`；NSForge 的 `>=3.12` 相容：
  [v2.1.1 pyproject](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/pyproject.toml)。
- current protocol 是 `2026-07-28`：
  [Versioning](https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning)、
  [Specification](https://modelcontextprotocol.io/specification/2026-07-28)。

v0.3 migration 原採 `mcp>=2.1.1,<3` 並由 lockfile 解析為 2.1.1；v0.4
release 已由後續決策改為精確 `mcp==2.1.1`，package／contract gates 同時驗證
實際安裝版本。不要獨立 pin `mcp-types`。SDK 內部雖改用 `httpx2`，NSForge
adapters 仍直接 import `httpx`，故保留自身 `httpx` dependency。依據：
[官方 migration guide](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/migration.md)。

## 2. 不可破壞的相容矩陣

| 表面 | 基線 | 完成條件 |
|---|---|---|
| 工具目錄 | 91 個 catalog tools | 同名 91 個，不刪除、合併或改名 |
| 預設面 | 82；music 9 個 opt-in | 預設 82；`NSFORGE_ENABLE_MUSIC=1` 後 91 |
| 輸入 | 現有名稱、型別、預設值 | 全保留；immutable v1 contract hash 不變，只可加不進 schema 的 injected `Context` |
| 成功輸出 | 每工具既有 JSON shape 與 `structuredContent` | keys、nesting、語意與雙 channel 全保留 |
| 預期失敗 | 既有 `{"success": false, ...}` | payload 原樣，MCP 層另標 `isError=true` |
| stdio | 預設 transport | 仍預設且 stdout 無 logging |
| HTTP | 未自動監聽 | 僅新增顯式 opt-in Streamable HTTP |
| state | 顯式 `session_id`／`result_id`，另有 legacy fallback | handle 不變；fallback 保留且加鎖 |
| provenance | 完整 birth certificate ledger | 欄位與 provenance gate 不得弱化 |
| manifest | catalog 91、default 82 | 與 live `tools/list` 完全一致 |

Resources、prompts 只能是 additive surface，不得取代工具。本次先保留異質
legacy payload 的寬鬆 object schema，避免 `outputSchema` 驗證誤拒既有合法 variant。

## 3. 機械遷移

```python
from mcp.server import MCPServer
from mcp.server.mcpserver import Context

mcp = MCPServer(
    name="nsforge",
    version=__version__,
    title="Neurosymbolic Forge",
    description="Turn concepts into verifiable, provenance-tracked entities.",
    instructions=...,
    website_url="https://github.com/u9401066/nsforge-mcp",
    lifespan=app_lifespan,
    cache_hints=cache_hints,
)
```

- `FastMCP` → `MCPServer`；`mcp.server.fastmcp.*` →
  `mcp.server.mcpserver.*`；公開物件名 `mcp` 保持不變。
- `ctx.fastmcp` → `ctx.mcp_server`；`get_context()` 已移除，改注入
  `ctx: Context`；`FastMCPError` → `MCPServerError`。
- Python model 欄位改 snake_case：`input_schema`、`output_schema`、
  `structured_content`、`is_error`、`next_cursor`、`mime_type`。自行輸出 wire
  JSON 使用 `model_dump(by_alias=True, mode="json")`；wire 仍是 camelCase。
- resource URI 視為 `str`；transport options 只傳 `run()`，不放 constructor。
- 明確設定 `version=__version__`，納入既有版本單一真相 self-check。
- 91 個同步 handler 在 v2 會跑 worker thread；這是併發語意變更，不只是 rename。
- 純 SymPy/CPU handler 保持 `def`；只有需 progress 或 async I/O 的邊界改
  `async def`，同步工作交給 thread/process。

## 4. 全工具 v2 契約

### Structured output

全部 91 個 catalog tools 以 `structured_output=True` 註冊；每個 `tools/list`
entry 必須有非空 `output_schema`，每次正常回傳同時具有給模型的 `content` 與給
application 的 `structured_content`。本次保留 `dict[str, Any]`，讓 SDK 發布 object
schema，而不對 heterogeneous legacy payload 強加新的 required fields。

機械遷移前先保存 91 個工具的 immutable contract hash（name、description、
`input_schema`、`output_schema`）；遷移後必須相同，證明既有 discovery contract
沒有漂移。title、icons、annotations 與 `_meta` 是本次允許加入的欄位，不納入 hash。
官方依據：
[Structured Output](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/structured-output.md)。

精確 per-tool `TypedDict`／Pydantic output models 是後續非 blocker：需先收集每個
工具所有成功、失敗、timeout 與 optional-field variants，再逐族群收緊並加 golden
tests；不得在本次升級中以 validation 強迫刪除既有欄位或合法 shape。

### Legacy error payload + `isError`

單純 return error dict 會被 MCP 視為成功。本次在註冊邊界轉成直接結果，而不把
protocol code 散到 91 個工具 body：

```python
CallToolResult(
    content=[TextContent(type="text", text=serialized_legacy_payload)],
    structured_content=legacy_payload,
    is_error=True,
)
```

註冊 wrapper 用 `functools.wraps` 保留原本 `dict[str, Any]` schema，執行時可直接回
`CallToolResult`。mapping 含 `error`，且 `success is False` 或 `verified is False` 時
視為預期 tool error，整份 payload 不變；單純驗證不成立仍是正常結果。真正 request
failure 才用 `MCPError`。未處理 exception 的完整 traceback 進 server log，對外
保留既有 error envelope 外形。依據：[Direct result](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/examples/snippets/servers/direct_call_tool_result.py)、
[Errors](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/handling-errors.md)。

### Metadata、annotations、icons

建立單一集中式 tool-profile policy，manifest/live gate 覆蓋精確 91 個 tool names。每工具須有
非空 `title`、description、namespaced `meta`、可解析 icon 與 `ToolAnnotations`：

- 純 parse/calculate/simplify/verify/read/list/status/codegen 設 read-only。
- session/saved-result mutation 非 read-only；刪除、回滾、覆寫與 abort 標 destructive。
- 非唯讀工具只有重複呼叫與一次相同時才 idempotent。
- 本機 deterministic catalog 為 closed world；Wikidata/BioModels 為 open world。
- annotations 是 UI/client hint，不是 ACL；不得存 secret 或使用者資料。

依據：[Tools](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/tools.md)、
[Media/icons](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/media.md)。

## 5. 新增的 stable server surfaces

### Resources 與 prompts

本次至少提供 `nsforge://manifest`、`nsforge://health`、`nsforge://north-star`，以及
`nsforge://derivations/{result_id}` resource template。不存在時拋
`ResourceNotFoundError`；saved derivation 提供 repository 已保存的 metadata 與
lineage 摘要（不是逐工具的完整 provenance ledger）。resource metadata 與
cache scope 不是授權，因此 HTTP 預設只允許 loopback。
manifest 與 north-star 必須隨 wheel 打包，不能只在 source checkout 可讀。

v0.4.0 在 tenant-scoped immutable store 建立後，另加入 run／event／artifact
resources、工具結果內的 `ResourceLink` 與 resource-updated 通知；
`nsforge://sessions/{session_id}` 只回傳在 session transaction 內擷取的 detached
legacy snapshot，不暴露可變物件本身。Metadata／subscription 不視為授權。

新增 `forge_verified_derivation` prompt；它只編排 deterministic tools，不在 prompt
內手算公式或宣稱未經工具驗證的結果。依據：
[Resources](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/resources.md)、
[Prompts](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/servers/prompts.md)。

### Cache、lifespan、progress

- `tools/list`、`prompts/list`、resource lists/templates、`server/discover` 是跨 caller
  相同的 discovery 資料，使用 5 分鐘 TTL/public；動態 `resources/read` 不設全域
  cache hint。cache hint 不是 access control。
- typed lifespan 一次建立 process-wide `Services`，shutdown 一次清理；不得另存
  第二套 singleton。spawned timeout worker 不攜帶不可 pickle 的 Context。
- v0.3 先回報 `task_run`、`task_explore` 開始／完成邊界；v0.4 改由真實
  phase events 驅動單調 progress、persistence 與 OTel events。無 callback 時 final
  result 保持相容。

依據：[Caching](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/client/caching.md)、
[Lifespan](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/handlers/lifespan.md)、
[Progress](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/handlers/progress.md)。

### stdio + opt-in Streamable HTTP

無設定時使用 stdio。僅 `NSFORGE_MCP_TRANSPORT=streamable-http` 時，才讀
`NSFORGE_MCP_HOST`（預設 `127.0.0.1`）、`NSFORGE_MCP_PORT`（8000）、
`NSFORGE_MCP_PATH`（`/mcp`）。`stateless_http` 與 `json_response` 預設皆 false，
分別只由 `NSFORGE_MCP_STATELESS_HTTP=1`、
`NSFORGE_MCP_HTTP_JSON_RESPONSE=1` 顯式開啟；Streamable HTTP response 使用串流
不等於已 deprecated 的獨立 SSE transport。

所有 HTTP bind 都傳入啟用 DNS-rebinding 防護的 `TransportSecuritySettings`。非
loopback bind 另須 `NSFORGE_MCP_ALLOW_REMOTE=1` 與非空
`NSFORGE_MCP_ALLOWED_HOSTS`（例如 `mcp.example.com,mcp.example.com:*`）；browser
client 再以 `NSFORGE_MCP_ALLOWED_ORIGINS` 列出精確 HTTPS origins。Origin allowlist
留空時允許沒有 Origin header 的非瀏覽器 client，並拒絕任何 supplied Origin。
Host／Origin allowlist 不是認證，外部仍須真正的 authentication、authorization
與 TLS boundary。保留 SDK body limit；process-wide sessions／repository 是單一
trust boundary，多 client 的每個 stateful call 都須用顯式 `session_id`，部署則每
tenant 一個 instance，不依 legacy fallback 或 sticky worker。v0.3.0 stateful
derivation 僅支援單 process／單 replica；多副本需 shared durable store 與
distributed locking，單靠 `NSFORGE_MCP_STATELESS_HTTP=1` 不會共享 domain state。

`NSFORGE_MCP_HTTP_JSON_RESPONSE=1` 只回傳該 request 的 final response，沒有
request-scoped notification 的 wire，因此不串流 `task_run`／`task_explore` progress；
需要 progress 時保留預設 false。依據：
[Running](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/run/index.md)、
[Deploy](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/run/deploy.md)。

## 6. 併發風險

v2 worker threads 會暴露 `_current_session`、單一 `DerivationSession` mutation、
repository dict/YAML save-update-delete 的 races。最低要求：

- 每個 session 用可回收 `RLock` 包住讀取、計算、append step、provenance 與保存；
  不同 session 仍可平行。
- legacy `_current_session` fallback 加鎖並保留，只作 single-client compatibility；
  HTTP/multi-client 的每個 stateful call 必須顯式傳 `session_id`。
- repository 操作使用一致 lock；寫檔採 temp + atomic replace；明定 lock order。
- 不用一把 global lock 序列化所有純 SymPy 工具。
- 測不同 session 平行、同 session mutation、fallback、repository race、timeout
  recovery。MCP/I/O 不得進入 `src/nsforge/domain/`。

## 7. 明確不採用

| 功能 | 狀態與理由 |
|---|---|
| MCP Tasks | 已移為 `io.modelcontextprotocol/tasks` extension，但 SDK 2.1.1 未實作；`task_run` 只是 domain tool。[Roadmap](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/ROADMAP.md) |
| SDK middleware | provisional，2.x minor 仍可破壞；核心 error/auth 不建在其上。[官方文件](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/advanced/middleware.md) |
| Roots、Sampling、Logging | 2026-07-28 deprecated；分別改用 params/resources/config、host/provider integration、stderr/OpenTelemetry。 |
| 獨立 HTTP+SSE | deprecated；只用 Streamable HTTP。 |
| 假 OAuth | 無 IdP、key、`TokenVerifier` 時不宣稱 auth；固定 token／永遠成功 verifier 不合格。[Authorization](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/run/authorization.md) |

官方 deprecated 依據：[Changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)、
[Registry](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)。直接
`ctx.elicit()` 只適用 legacy connection；本次不讓 elicitation 成為既有工具必要
前置，以免 client 功能退化。

## 8. 回歸驗收與 Git 邊界

自動 gate 覆蓋：SDK/import/version；82/91 names；全 91 個 profiles、非空 output
schemas 與 v1 immutable contract hashes；成功、handled error、negative verification
等代表性 family payload 的雙 channel／`is_error`；resource／template／prompt discovery，
manifest、health、north-star reads 與 cache scope；實際 progress callback；真實 stdio
subprocess wire；legacy mode initialize/list/call；HTTP app construction 與惡意 Host
拒絕；以及第 6 節的 session／repository／timeout focused tests。in-memory server tests
採官方 `Client(mcp, raise_exceptions=True)`；release 另執行 `uv build`、wheel inventory
與暫存環境安裝後的 stdio/resource smoke。未列出的每工具 payload 組合、完整 HTTP
部署或 lifespan side-effect 不冒充已逐一 gate：
[Testing](https://github.com/modelcontextprotocol/python-sdk/blob/v2.1.1/docs/get-started/testing.md)。

```bash
uv run python scripts/check.py --json
uv run python scripts/check.py
```

全 gates 必須 exit 0，不降低 mypy strict 或 provenance/harness gates。若工具註冊有
變化，執行 `uv run python scripts/gen_capabilities.py`；本次 tool name/count 應不變。
README、tools reference、manifest、Memory Bank 與版本資訊同步。

建議 commits：dependency/lock → MCPServer mechanical migration → structured contracts
與 metadata → error dual-track → resources/prompts/runtime → concurrency/tests →
docs/Memory Bank。每個 code commit 跑相應 gates，最終全量 green 後才 push；交付列出
commit hashes、gate 結果與 remote branch。

## 9. v0.4.0 trusted workflow 後續實作

v0.4.0 不回頭改寫上述 v0.3 migration contract，而是在相容面之外加上
可驗證執行面：

1. **Exact stable runtime**：v0.4 release 由寬範圍改為 `mcp==2.1.1`，package／
   contract smoke 同時驗證實際安裝版本；capability manifest 升為 schema v4。
2. **Fixed profiles**：`legacy=82`（預設）、`workflow=17`、
   `scientific=35`、`interactive=35`、`full=91`。未知 profile 啟動失敗；
   compact profiles 拒絕 unknown fields 並套用 enum／range constraints。
3. **No-eval expression boundary**：統一 allowlisted tokenizer／AST constructor，不再對
   caller text 使用 `parse_expr`／`sympify`，並保留複雜度 budget。
4. **Strict evidence gate**：驗證失敗、缺失／過期 evidence、caller assertion、
   wrong tenant／digest／revision／policy 或 incomplete provenance 皆不產出程式碼
   artifact。Legacy codegen payload 只為相容層，不會被升格為 trusted artifact。
5. **Immutable application kernel**：`RunStore` port 與 SQLite Unit of Work 原子寫入
   tenant-scoped run、ordered events、provenance nodes、verification evidence 與
   content-addressed artifacts；terminal revision 不可就地修改。
6. **MCP primitives**：`nsforge://runs/{run_id}`、`.../events`、
   `nsforge://sessions/{session_id}`、`nsforge://artifacts/{sha256}`，以及 tool result
   中的 `ResourceLink`、updated
   notification 與 phase progress。
7. **Observability**：SDK OpenTelemetry span 帶 tool／session／run correlation；phase event
   是 provenance、progress、persistence 與 trace event 的共同真相，不記錄完整
   expression、code 或 artifact bytes。
8. **Release gates**：harness 由 12 擴為 14：
   `lint, format, type, security, import, manifest, mcp, test, bench, generic,
   provenance, package, harness, diff`。

### 實際邊界

- Legacy `DerivationSession`／`DerivationRepository` 仍是 process globals + JSON／YAML
  相容層；strict SQLite 只是 trusted workflow 的權威狀態。
- `NSFORGE_TENANT_ID` 是 server scope，不是 caller identity。未接 IdP／token verifier
  時，一個 instance 只適合一個 tenant trust boundary。
- SQLite 與 process globals 都不是 cross-replica shared state；多副本需 shared DB、
  artifact backend、distributed coordination 與 trusted principal resolver。
- 取消 `asyncio.to_thread` 的 await 不會停止 worker，因此不誤報 Finished；
  hard timeout 仍透過可終止 process。
- MCP Python SDK 2.1.1 仍未實作 Tasks extension；NSForge 不宣稱支援。
