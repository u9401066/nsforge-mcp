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
*Last updated: 2026-01-04*

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
