# NSForge-USolver 協作 Skill

**ID**: `nsforge-usolver-collab`  
**Version**: 1.0.0  
**Trigger**: 優化, optimize, 最佳解, optimal, 約束求解, constraint solving, USolver

---

## 🎯 Skill 定位

**領域知識推導 × 數學優化 = 完整解決方案**

此 Skill 協調 NSForge 和 USolver 兩個 MCP Server 協同工作：
- **NSForge**: 推導領域專業的修正公式（考慮藥物交互作用、體質差異等）
- **USolver**: 在修正後的公式中找最優解（滿足約束的最佳參數值）

---

## ⚙️ 工作流程

```
用戶問題
   ↓
1️⃣ NSForge 推導修正公式
   derivation_start()
   derivation_load_formula()
   derivation_substitute() / derivation_add_note()
   derivation_complete()
   ↓
2️⃣ 準備優化輸入
   derivation_prepare_for_optimization()
   ↓
3️⃣ USolver 求最優解
   usolver.solve(...)
   ↓
4️⃣ 呈現結果
   整合推導步驟 + 最優解 + 解釋
```

---

## 📋 使用時機

### 適用場景

1. **藥物劑量優化**
   - 用戶：「65歲、體脂30%、併用midazolam，最佳Fentanyl劑量？」
   - NSForge：推導修正後的 PK 公式
   - USolver：找滿足治療窗的最優劑量

2. **電路參數優化**
   - 用戶：「考慮寄生電容和溫度漂移，濾波器最佳 R, C 值？」
   - NSForge：推導修正後的轉移函數
   - USolver：找符合規格的標準元件值

3. **資源配置優化**
   - 用戶：「考慮加班費和技能津貼，最低成本排班？」
   - NSForge：推導成本計算公式
   - USolver：找最優排班方案

### 不適用場景

- 純數學計算（直接用 SymPy-MCP）
- 不需優化的問題（直接用 NSForge）
- 沒有領域修正的優化（直接用 USolver）

---

## 🔧 工具鏈

### Phase 1: NSForge 推導

```python
# 1. 開始推導會話
derivation_start(
    name="temp_corrected_pk",
    description="Temperature-corrected pharmacokinetics"
)

# 2. 載入基礎公式
derivation_load_formula(
    source_type="library",
    identifier="pharmacokinetics/three_compartment"
)

# 3. 應用修正
derivation_substitute(
    "CL",
    "CL_base * temp_factor * age_factor * interaction_factor",
    notes="溫度 × 年齡 × 藥物交互作用修正"
)

# 4. 完成推導
derivation_complete()
```

### Phase 2: 準備優化

```python
# 取得優化器格式
result = derivation_prepare_for_optimization()

# 返回：
# {
#   "function_str": "dose/V1 * exp(-CL*t/V1)",
#   "variables": ["dose", "t"],
#   "parameters": {"CL": 0.476, "V1": 15.875},
#   "suggested_constraints": [
#     "dose >= 0.01",
#     "dose <= 0.10"
#   ],
#   "usolver_template": "..."
# }
```

### Phase 3: USolver 優化

```python
# 複製 USolver 模板到 USolver MCP
usolver.solve(
    problem_type="convex_optimization",
    objective="minimize (target - C(t, dose))**2",
    constraints=[
        "C(t=5, dose) >= 2.0",  # 治療下限
        "C(t=5, dose) <= 4.0",  # 毒性上限
        "dose >= 0.01",
        "dose <= 0.10"
    ],
    formula="dose/15.875 * exp(-0.476*5/15.875)"
)

# 返回：
# {
#   "optimal_dose": 0.035,
#   "objective_value": 0.04,
#   "C_at_t5": 2.8
# }
```

---

## 💡 完整範例

### 範例 1: 藥物劑量優化

**用戶請求**：
> "65歲患者，體脂30%，併用midazolam，計算Fentanyl最佳劑量，目標5分鐘達到2.5 ng/mL"

**Agent 執行**：

```markdown
## Step 1: NSForge 推導修正公式

基礎三室模型需考慮：
- 藥物交互作用（CYP3A4競爭）
- 體脂率影響分布容積
- 年齡影響清除率

derivation_start("fentanyl_individualized", "Individualized Fentanyl PK")
derivation_load_formula("library", "pharmacokinetics/three_compartment")
derivation_substitute("CL", "0.8 * 0.7 * 0.85", notes="Midazolam (-30%) × Age 65 (-15%)")
derivation_substitute("V1", "12.7 * 1.25", notes="Body fat 30% → +25% Vd")
derivation_complete()

修正後公式：
C(t, dose) = dose / 15.875 × exp(-0.476×t / 15.875)

## Step 2: 準備優化

derivation_prepare_for_optimization()

建議約束：
- 治療窗：C(5min) ∈ [2.0, 4.0] ng/mL
- 安全餘裕：C(30min) ≥ 1.5 ng/mL
- 劑量範圍：dose ∈ [0.01, 0.10] mg

## Step 3: USolver 求最優解

Use usolver to find optimal dose:
- Objective: C(t=5, dose) = 2.5 ng/mL
- Constraints: [上述約束]

USolver 結果：
- optimal_dose = 0.0354 mg (35.4 mcg)
- C(t=5) = 2.51 ng/mL ✓
- C(t=30) = 1.62 ng/mL ✓
- Safety margin = 37%

## 臨床建議

✅ **推薦劑量**: 35 mcg (慢推 >30秒)
✅ **預期效果**: 5分鐘達峰，濃度2.5 ng/mL
✅ **持續時間**: 30分鐘仍有治療效果
⚠️ **監測**: 呼吸抑制風險（midazolam協同效應）
```

---

## 🎓 關鍵概念

### NSForge vs USolver

| 特性 | NSForge | USolver |
|------|---------|---------|
| **輸入** | 基礎公式 + 修正規則 | 目標函數 + 約束條件 |
| **處理** | 符號推導 | 數值優化 |
| **輸出** | 修正後公式 | 最優參數值 |
| **專業** | 領域知識 | 數學優化 |

### 為何需要兩者？

1. **NSForge 單獨**：
   - ✅ 推導正確公式
   - ❌ 不知道最佳參數值

2. **USolver 單獨**：
   - ✅ 找最優解
   - ❌ 不知道領域修正規則

3. **NSForge + USolver**：
   - ✅ 正確的公式 + 最優的參數
   - = **領域智慧 × 數學精準**

---

## ⚠️ 注意事項

### 1. 檢查變數分類

`derivation_prepare_for_optimization()` 會自動分類變數：
- **優化變數**（如 dose, time）：需要求解
- **參數**（如 CL, V1）：已從推導確定

**如果分類錯誤**，手動指定：
```python
# 在 USolver 中明確指定
variables_to_optimize = ["dose"]
fixed_parameters = {"CL": 0.476, "V1": 15.875}
```

### 2. 約束條件要具體

**不好**：
```python
constraints = ["dose > 0", "concentration is therapeutic"]
```

**好**：
```python
constraints = [
    "dose >= 0.01",
    "dose <= 0.10",
    "C(t=5, dose) >= 2.0",  # 明確數值
    "C(t=5, dose) <= 4.0"
]
```

### 3. 選擇正確的求解器

| 問題類型 | USolver 求解器 |
|----------|----------------|
| 線性/凸優化 | CVXPY, HiGHS |
| 整數規劃 | OR-Tools, Z3 |
| 組合優化 | OR-Tools |
| 複雜約束 | Z3 SMT |

---

## 📚 相關文件

- **工具實作**: `src/nsforge_mcp/tools/derivation.py` (derivation_prepare_for_optimization)
- **NSForge 核心**: `docs/composable-formula-modification-engine.md`
- **USolver 介紹**: https://github.com/sdiehl/usolver
- **協作分析**: `docs/nsforge-usolver-collaboration.md` (若未來創建)

---

## ✅ Checklist

執行此 Skill 時確認：

- [ ] 用戶問題需要**優化**（找最佳值）
- [ ] 有**領域修正規則**需要應用（體質、交互作用等）
- [ ] NSForge 推導**已完成**（有 current_expression）
- [ ] 約束條件**明確且數值化**
- [ ] 知道使用哪個 **USolver 求解器**
- [ ] 結果需要**解釋和臨床建議**（不只數字）

---

**Skill Status**: ✅ Active  
**Last Updated**: 2026-01-04  
**Maintainer**: NSForge Team
