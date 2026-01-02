---
name: nsforge-formula-management
description: 公式庫管理：查詢、取得、更新、刪除已存檔的推導結果。觸發詞：找公式, list, 列出, 有哪些, 更新公式, 刪除公式, 公式庫。
---

# NSForge 公式庫管理 Skill

## 觸發條件

當用戶說：
- 「找公式」「search formula」「搜尋」
- 「列出」「list」「有哪些公式」
- 「公式庫」「formula library」「repository」
- 「更新公式」「修改公式」「標記為」
- 「刪除公式」「移除」「remove」
- 「統計」「stats」「多少條」

## 必備工具

這個 Skill 使用 `nsforge-mcp` 的以下工具：

| 操作 | 工具 | 說明 |
|------|------|------|
| 列出 | `derivation_list_saved` | 列出所有已存檔的推導 |
| 搜尋 | `derivation_search_saved` | 關鍵字搜尋 |
| 取得 | `derivation_get_saved` | 取得單一推導詳情 |
| 更新 | `derivation_update_saved` | 更新元資料 |
| 刪除 | `derivation_delete_saved` | 刪除推導（需確認）|
| 統計 | `derivation_repository_stats` | 公式庫統計資訊 |

## 執行流程

```
┌─────────────────────────────────────────────────────────────┐
│                 公式庫管理 (Formula Management)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用戶需求分析：                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 「找 X」     → derivation_search_saved(query="X")   │   │
│  │ 「列出全部」 → derivation_list_saved()              │   │
│  │ 「詳細資訊」 → derivation_get_saved(result_id)      │   │
│  │ 「更新 X」   → derivation_update_saved(...)         │   │
│  │ 「刪除 X」   → derivation_delete_saved(...) ⚠️      │   │
│  │ 「統計」     → derivation_repository_stats()        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 詳細工具說明

### derivation_list_saved

**目的**：列出所有已存檔的推導結果

**參數**：
- `category` (可選): 按分類篩選，如 `"pharmacokinetics"`

**使用方式**：
```python
# 列出所有
derivation_list_saved()

# 按分類列出
derivation_list_saved(category="pharmacokinetics")
```

**回傳格式**：
```json
{
  "success": true,
  "results": [
    {
      "id": "temp_corrected_elimination_20260102",
      "name": "temp_corrected_elimination",
      "description": "Temperature-corrected drug elimination",
      "created_at": "2026-01-02T10:30:00",
      "tags": ["pharmacokinetics", "temperature"]
    }
  ],
  "count": 1
}
```

**Agent 應該**：
- 以表格或清單形式呈現給用戶
- 顯示 name、description、tags

---

### derivation_search_saved

**目的**：用關鍵字搜尋公式

**參數**：
- `query` (必須): 搜尋關鍵字

**搜尋範圍**：
- 公式名稱
- 描述
- 標籤
- 臨床情境

**使用方式**：
```python
# 搜尋溫度相關
derivation_search_saved(query="temperature")

# 搜尋藥動學
derivation_search_saved(query="pharmacokinetics")

# 搜尋 Arrhenius
derivation_search_saved(query="arrhenius")
```

**回傳格式**：
```json
{
  "success": true,
  "query": "temperature",
  "results": [...],
  "count": 2
}
```

**Agent 應該**：
- 用自然語言描述搜尋結果
- 如果沒找到，建議相關搜尋詞

---

### derivation_get_saved

**目的**：取得單一推導的完整詳情

**參數**：
- `result_id` (必須): 推導結果的 ID

**使用方式**：
```python
derivation_get_saved(result_id="temp_corrected_elimination_20260102")
```

**回傳格式**：
```json
{
  "success": true,
  "result": {
    "id": "temp_corrected_elimination_20260102",
    "name": "temp_corrected_elimination",
    "final_expression": "C_0*k_ref*exp(E_a*(T - T_ref)/(R*T*T_ref) - k_ref*t*exp(E_a*(T - T_ref)/(R*T*T_ref)))",
    "description": "Temperature-corrected drug elimination rate...",
    "clinical_context": "Use when adjusting drug dosing for febrile patients",
    "assumptions": ["First-order kinetics", "Arrhenius behavior"],
    "limitations": ["Valid for 32-42°C"],
    "steps": [
      {"step": 1, "operation": "load", "expression": "C_0*exp(-k*t)"},
      {"step": 2, "operation": "substitute", "expression": "..."}
    ],
    "source_formulas": [
      {"id": "one_compartment", "source": "textbook"},
      {"id": "arrhenius", "source": "textbook"}
    ],
    "references": ["Goodman & Gilman's Pharmacology"],
    "tags": ["pharmacokinetics", "temperature"],
    "created_at": "2026-01-02T10:30:00",
    "updated_at": "2026-01-02T10:35:00"
  }
}
```

**Agent 應該**：
- 格式化呈現公式（可用 LaTeX）
- 說明假設和限制
- 提及來源公式的溯源

---

### derivation_update_saved

**目的**：更新已存檔推導的元資料

**參數**：
- `result_id` (必須): 推導結果的 ID
- 以下為可更新欄位（皆為可選）：
  - `description`: 更新描述
  - `clinical_context`: 更新臨床情境
  - `assumptions`: 更新假設列表
  - `limitations`: 更新限制列表
  - `references`: 更新參考文獻
  - `tags`: 更新標籤
  - `verified`: 標記驗證狀態 (boolean)
  - `verification_notes`: 驗證備註

**使用方式**：
```python
# 標記為已驗證
derivation_update_saved(
    result_id="temp_corrected_elimination_20260102",
    verified=True,
    verification_notes="Dimensional analysis passed"
)

# 補充臨床情境
derivation_update_saved(
    result_id="temp_corrected_elimination_20260102",
    clinical_context="Use when adjusting aminoglycoside dosing for febrile patients. Particularly important for drugs with narrow therapeutic index."
)

# 添加標籤
derivation_update_saved(
    result_id="temp_corrected_elimination_20260102",
    tags=["pharmacokinetics", "temperature", "aminoglycoside", "fever"]
)
```

**回傳格式**：
```json
{
  "success": true,
  "message": "Updated successfully",
  "updated_fields": ["verified", "verification_notes"],
  "result_id": "temp_corrected_elimination_20260102"
}
```

**Agent 應該**：
- 確認更新成功後告知用戶
- 說明哪些欄位被更新

---

### derivation_delete_saved

**目的**：刪除已存檔的推導結果

**⚠️ 重要**：這是破壞性操作，Agent 應該先確認！

**參數**：
- `result_id` (必須): 推導結果的 ID
- `confirm` (必須): 必須為 `True` 才會執行

**使用方式**：
```python
# ⚠️ 必須先向用戶確認
derivation_delete_saved(
    result_id="temp_corrected_elimination_20260102",
    confirm=True
)
```

**回傳格式**：
```json
{
  "success": true,
  "message": "Deleted successfully",
  "deleted_id": "temp_corrected_elimination_20260102"
}
```

**Agent 必須**：
1. 先呼叫 `derivation_get_saved` 顯示要刪除的內容
2. 明確詢問用戶「確定要刪除嗎？」
3. 用戶確認後才執行刪除
4. 告知用戶刪除無法復原

---

### derivation_repository_stats

**目的**：取得公式庫統計資訊

**參數**：無

**使用方式**：
```python
derivation_repository_stats()
```

**回傳格式**：
```json
{
  "success": true,
  "stats": {
    "total_derivations": 15,
    "by_category": {
      "pharmacokinetics": 8,
      "physics": 4,
      "chemistry": 3
    },
    "verified_count": 10,
    "unverified_count": 5,
    "recent_activity": [
      {"id": "...", "action": "created", "date": "2026-01-02"}
    ],
    "most_used_tags": [
      {"tag": "pharmacokinetics", "count": 8},
      {"tag": "temperature", "count": 3}
    ]
  }
}
```

**Agent 應該**：
- 以摘要形式呈現統計
- 可視情況用簡單圖表（如 ASCII）

---

## 常見使用場景

### 場景 1：「有哪些藥動學公式？」

```python
# 方法 1：用分類篩選
derivation_list_saved(category="pharmacokinetics")

# 方法 2：用關鍵字搜尋
derivation_search_saved(query="pharmacokinetics")
```

**Agent 回應範例**：
> 找到 3 個藥動學相關公式：
> 1. **temp_corrected_elimination** - 溫度校正消除率
> 2. **fat_adjusted_vd** - 肥胖調整分布容積
> 3. **renal_clearance_model** - 腎清除率模型
>
> 要查看哪一個的詳細內容？

---

### 場景 2：「這個公式的假設是什麼？」

```python
# 先搜尋或列出找到 ID
derivation_search_saved(query="temperature")

# 取得詳情
derivation_get_saved(result_id="temp_corrected_elimination_20260102")
```

**Agent 回應範例**：
> **temp_corrected_elimination** 的假設條件：
> 1. 一級消除動力學
> 2. Arrhenius 溫度依賴性
> 3. 單一消除途徑
>
> **限制**：
> - 僅適用於 32-42°C 體溫範圍
> - 未考慮溫度對蛋白結合的影響

---

### 場景 3：「把這個公式標記為已驗證」

```python
derivation_update_saved(
    result_id="temp_corrected_elimination_20260102",
    verified=True,
    verification_notes="Dimensional analysis passed on 2026-01-02"
)
```

**Agent 回應範例**：
> ✅ 已將 **temp_corrected_elimination** 標記為已驗證。
> 備註：Dimensional analysis passed on 2026-01-02

---

### 場景 4：「刪除這個公式」

```python
# Step 1: 先顯示要刪除的內容
derivation_get_saved(result_id="old_formula_20250101")

# Step 2: 向用戶確認
# Agent: 「確定要刪除 old_formula 嗎？這個操作無法復原。」

# Step 3: 用戶確認後執行
derivation_delete_saved(
    result_id="old_formula_20250101",
    confirm=True
)
```

**Agent 回應範例**：
> ⚠️ 您要刪除的公式：
> - 名稱：old_formula
> - 描述：...
> - 建立日期：2025-01-01
>
> **確定要刪除嗎？這個操作無法復原。**

---

### 場景 5：「公式庫有多少條目？」

```python
derivation_repository_stats()
```

**Agent 回應範例**：
> 📊 **公式庫統計**
> - 總計：15 個推導結果
> - 已驗證：10 個 ✅
> - 待驗證：5 個 ⏳
>
> **分類分布**：
> - 藥動學：8 個
> - 物理：4 個
> - 化學：3 個
>
> **熱門標籤**：pharmacokinetics (8), temperature (3), elimination (2)

---

## 錯誤處理

### 找不到公式
```json
{
  "success": false,
  "error": "Result not found",
  "result_id": "nonexistent_id"
}
```

**Agent 應該**：
- 建議用戶用 `derivation_list_saved()` 查看所有可用公式
- 或用 `derivation_search_saved()` 搜尋

### 更新失敗
```json
{
  "success": false,
  "error": "Invalid field: xyz"
}
```

**Agent 應該**：
- 說明哪些欄位可以更新
- 檢查 result_id 是否正確

### 刪除未確認
```json
{
  "success": false,
  "error": "Deletion requires confirm=True"
}
```

**Agent 應該**：
- 不要自動加上 confirm=True
- 必須先獲得用戶明確同意

---

## 最佳實踐

1. **搜尋前先了解範圍**：先用 `derivation_repository_stats()` 了解公式庫大小
2. **組合使用**：先 list/search 找到 ID，再 get 取得詳情
3. **謹慎刪除**：永遠先 get 再 delete，並獲得用戶確認
4. **保持標籤一致**：更新時參考現有標籤，避免重複或不一致

---

## 相關 Skills

- `nsforge-derivation-workflow`: 建立新的推導
- `nsforge-verification-suite`: 驗證公式正確性
- `nsforge-code-generation`: 從公式生成程式碼
