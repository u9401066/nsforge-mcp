# Active Context

> 📌 此檔案記錄當前工作焦點，每次工作階段開始時檢視，結束時更新。

## 🎯 當前焦點

**修正推導工具的 Unicode 希臘字母輸入相容性，並同步補齊文件 / 測試。**

### 當前工作內容
- 修正 `derivation_record_step` / `derivation_import_from_sympy` 對 `β`, `λ`, `β₀` 等 Unicode 輸入的解析
- 避免 SymPy 將 `beta` / `gamma` 視為特殊函數，並避開 `lambda` Python 關鍵字
- 補上回歸測試與 README / API 文檔說明

### ToolUniverse 評估
- ✅ **高度互補**：現有 700+ 工具主要是資料檢索，缺符號推導
- ✅ **不會太重**：作為 local MCP tool，獨立運作
- ✅ **適合定位**：Computational Science Tools（計算科學）

## ✅ 本次完成 (2026-04-21)

### Unicode 推導輸入相容性

- 新增安全 placeholder 預處理流程，把含希臘字母的識別字綁定為 `Symbol`
- `N_0 * exp(-λ*t) + β`、`β₀ * exp(-λ*t)` 等輸入可正常進入推導記錄工具
- 同步更新 README / FORMULA_APIS / CHANGELOG 說明

## ✅ 先前完成 (2026-01-16)

### 🧪 生理學 Vd 模型推導

**核心公式：**
$$V_{d,ss} = V_{plasma} + K_{p,lean} \times V_{lean} + K_{p,fat} \times V_{fat}$$

**推導歷程：**

| 階段 | 發現 | 行動 |
|------|------|------|
| 初始公式 | 原公式乘 f_u 導致 40x 低估 | 改用 PBPK 標準方法 |
| 驗證 | 9 種藥物僅 1/9 符合 | 重新定位公式用途 |
| 定位 | logP 無法準確預測 Kp | 改為「體組成調整公式」|

**驗證結果 (9 種藥物)：**

| 藥物 | 計算 Vd | 文獻 Vd | 比率 | 判定 |
|------|---------|---------|------|------|
| Propofol | 3.83 | 2-10 | ✓ | 符合 |
| Diazepam | 0.48 | 0.7-2.6 | 54% | 低估 |
| Midazolam | 0.66 | 0.8-1.5 | 83% | 偏低 |
| Fentanyl | 0.80 | 3-8 | 20% | 低估 |
| ... | | | | |

### 📄 產出檔案

| 檔案 | 內容 | 行數 |
|------|------|------|
| `formulas/derivations/pharmacokinetics/physiological_vd_body_composition.md` | 完整推導文檔 | ~400 |
| `examples/physiological_vd_model.py` | Python 實作 (PhysiologicalVdModel) | ~300 |
| `formulas/derived/881df03b.yaml` | NSForge 推導記錄 | auto |

### 🎯 公式適用範圍

- ✅ **適用**：logP > 2、中性分子、被動擴散、脂肪組織為主要分布
- ❌ **不適用**：離子化藥物、主動轉運、特殊蛋白結合

## ✅ 上次完成 (2026-01-05)

### derivation_show() 工具

- 新增推導狀態顯示工具
- 更新所有 NSForge Skill 文檔
- 工具數量：76 NSForge + 32 SymPy = 108 總計

## 🔜 下一步

1. 使用 physiological_vd_model.py 進行臨床場景模擬
2. 擴展模型支援其他組織（腎、肝、腦）

---
*Last updated: 2026-01-16*
