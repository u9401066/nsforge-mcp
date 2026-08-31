# System Patterns

> 📌 此檔案記錄專案中使用的模式和慣例，新模式出現時更新。

## 🏗️ 架構模式

### DDD 分層架構
```
Presentation → Application → Domain ← Infrastructure
```
- Domain 層不依賴任何外層
- Repository Pattern 為唯一資料存取方式

### 憲法-子法層級
```
CONSTITUTION.md (最高原則)
  └── .github/bylaws/ (子法)
        └── .claude/skills/ (實施細則)
```

## 🛠️ 設計模式

### MCP v2 `ToolSpec` 註冊邊界

- `MCPServer` 是唯一 server runtime，SDK 精確 pin `mcp==2.1.1`。`EnvelopeMCP`
  在單一邊界為 91 個工具套用 title、icons、annotations／meta、
  structured output 與 `ResourceLink`。
- `ToolSpec` 是 profile membership、concise descriptions、deprecation、constraints、
  provenance mode 與 metadata 的單一真相。Server startup 凍結 legacy 82／workflow 17／
  scientific 35／interactive 35／full 91 之一；未知 profile fail closed。
- 既有工具仍回傳原 JSON payload；v2 成功結果同時產生 text／structured content，失敗 envelope 額外設 MCP `isError`。
- Resources 與 prompt 是加法式原語，不取代舊 tools；run／event／artifact
  resources 承擔 strict reads，`nsforge://sessions/{session_id}` 提供 detached legacy
  workflow snapshot，phase events 驅動 progress 與 updated notifications。

### Strict provenance + Unit of Work

- Domain 保持 immutable `Run`、`PhaseEvent`、`ProvenanceNode`、
  `VerificationEvidence`、`Artifact`；canonical SHA-256 將 parent／input／output／evidence
  綁定。
- Application `StrictRunService` 負責 lifecycle 與 fail-closed codegen eligibility；caller
  assertion 只能成為 untrusted evidence。
- `RunStore` / `RunUnitOfWork` 是 application port；SQLite adapter 以 WAL、foreign keys、
  optimistic revision 單一 transaction 寫 run／events／provenance／evidence／artifacts。
- Legacy process-global sessions 與 JSON／YAML repository 仍為相容層，不是 strict run
  authority。

### Expression 與 path 安全邊界

- Caller expression 統一以 allowlisted token transformations + AST walker 建立 SymPy
  objects；不執行 `eval`、`parse_expr`、`sympify` 所產生的 Python。除結構 budgets，
  eager literal exponent、組合／gamma-family special functions 整數參數另有限額；
  `polygamma` 採更嚴格的 128 上限。
- Repository category、artifact name 與 music output 均需 normalize、root containment
  與 symlink escape 檢查；music artifact root 在工具註冊時凍結，env drift 不可重導。

### 相容契約模式

- Capabilities manifest v4 是 agent 的機讀契約，同時描述 profiles、strict
  constraints、MCP primitives、transports 與每工具 metadata。
- `mcp` gate 驗證五個 exact profiles、legacy contracts、strict validation、dual channel／
  `isError`、resources／ResourceLink／progress／notifications。完整 harness 為 14 gates，
  另含 `security` 與 isolated `package` smoke。
- Default／full 工具 schema 以 golden SHA-256 鎖定，遷移時只允許加法式增強；任何工具消失或輸入／輸出 schema 漂移都會使 gate 失敗。

### Worker-thread 狀態安全

- MCP SDK v2 的 sync handler 會在 worker thread 執行；所有可變 session／repository 操作必須在鎖內完成 read-modify-write。
- 狀態持久化使用「同目錄暫存檔 → `os.replace`」的原子寫入，避免並發或中斷導致半份 YAML／JSON。

### Transport 安全邊界

- stdio 是預設；Streamable HTTP 需顯式 opt-in 且預設只綁定 loopback。
- 每個 HTTP bind 都傳入 `TransportSecuritySettings`；非 loopback 還需明確 allow flag、非空 Host allowlist 與真正的外部 auth/TLS。Browser Origin 必須精確 allow；空 Origin allowlist 拒絕所有 supplied Origin。
- Process-wide session fallback／repository 是單一 trust boundary；多 client 的 stateful call 必須明確傳 `session_id`，每 tenant 一個 instance。JSON-response mode 不串流 request-scoped progress。
- Transport allowlists 不是 authentication。MCP Tasks 尚未由 SDK 穩定實作，SSE 與其他 deprecated 路徑不納入。
- `NSFORGE_TENANT_ID` 是 server scope 而非 caller identity；未接 IdP 時一個 instance
  是一個 tenant boundary。SQLite 與 legacy state 皆不跨 replica 共享。
- 取消 `asyncio.to_thread` await 無法殺掉 worker；只在 worker 真正結束後回報
  Finished，hard timeout 用可 terminate process；隔離路徑保留同一批 canonical
  events，但 process 回傳後才重播 progress。

### Repository Pattern
- 介面在 Domain 層定義
- 實作在 Infrastructure 層

### Strategy Pattern
- 用於取代複雜條件判斷
- 實例：ShippingStrategy, PaymentStrategy

### Command Pattern (CQRS)
- Commands: 寫入操作
- Queries: 讀取操作

## 📝 命名慣例

| 類型 | 慣例 | 範例 |
|------|------|------|
| Entity | 名詞單數 | `User`, `Order` |
| Value Object | 描述性名詞 | `Email`, `Money` |
| Repository | `I{Entity}Repository` | `IUserRepository` |
| Use Case | 動詞 + 名詞 | `CreateOrder` |
| Domain Event | 過去式 | `OrderCreated` |

## 📚 程式碼慣例

### Python
- 使用 `snake_case` 命名
- 檔案名全小寫
- 類別使用 `PascalCase`
- 優先使用 type hints

### 測試
- 測試檔案以 `test_` 開頭
- 測試類別以 `Test` 開頭
- 使用 pytest markers 分類

---
*Last updated: 2026-08-31 12:37 UTC*

## MCP-to-MCP 協作模式

### 橋接工具模式（Bridge Tool Pattern）
NSForge 與 USolver 協作展示的新模式：

```
Source MCP (NSForge):
  └── 推導領域修正公式
  └── derivation_prepare_for_optimization()  ← 橋接工具
       ├─ 自動分類變數類型（優化 vs 參數）
       ├─ 提取參數值（從推導步驟）
       ├─ 生成領域約束（劑量、時間）
       └─ 輸出目標 MCP 範本
Target MCP (USolver):
  └── 接收標準化輸入
  └── 執行優化求解
  └── 返回最佳參數值
```

**關鍵設計元素**：
1. **自動適配**：源 MCP 了解目標 MCP 的輸入需求
2. **領域注入**：橋接工具加入領域知識（約束條件）
3. **範本生成**：提供完整使用範例
4. **雙向文檔**：Skill 檔案說明完整工作流

**適用場景**：
- 跨 MCP 組合複雜任務
- 需要領域知識轉換
- Agent 需要工作流指引

**實例**：
- NSForge → USolver: 推導 → 優化
- 未來可能: NSForge → Lean4: 驗證形式正確性

### 變數分類啟發式（Heuristic Classification）
橋接工具中的自動分類策略：

```python
# 優化變數（需要找到最佳值）
if "dose" in var.lower() or var in ["t", "x", "y"]:
    optimization_vars.append(var)

# 參數（從推導步驟提取固定值）
else:
    parameters[var] = extract_from_steps(var)
```

**權衡**：
- ✅ 自動化大多數常見情況
- ✅ 減少 Agent 手動工作
- ⚠️ 可能誤判（通過 USolver 手動覆蓋）

---

## Compact SKILL.md Design

Skills 檔案需精簡設計：因 SKILL.md 完整載入 context，必須最小化。保留：工具名+參數+1-2行範例。刪除：Agent 回應範例、ASCII 流程圖、JSON 返回格式、冗長場景。達成 80-92% 減量。

### Examples

- nsforge-quick-calculate: 794→65 lines (92%)
- nsforge-derivation-workflow: 400→80 lines (80%)
