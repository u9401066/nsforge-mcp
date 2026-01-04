# NSForge 價值主張重新審視

> **Date**: 2026-01-01  
> **Trigger**: 用戶提出核心質疑 - "NSForge 到底要提供什麼？"

---

## 🤔 用戶的核心質疑

### 質疑 1：公式庫真的需要嗎？
**用戶觀點**：
- Agent (LLM) 已經受過物理、數學訓練
- 現有 Library 已經很完善（SymPy, SciPy, NumPy, lcapy）
- sympy-mcp 已經提供精確符號運算

**反思**：
- ✅ 基礎公式（F=ma, V=IR）Agent 確實都知道
- ✅ SymPy 已經有完整的數學函數庫
- ❓ 那還需要「公式庫」嗎？

### 質疑 2：推導由誰負責？
**用戶觀點**：
- Agent 可以推導（用自然語言規劃）
- sympy-mcp 執行精確計算
- 人類需要「看得懂」或「圖像理解」

**現況**：
```
目前工作流：
User: "計算 RC 濾波器截止頻率"
  ↓
Agent: 識別公式 f_c = 1/(2πRC)
  ↓
sympy-mcp: 執行符號運算
  ↓
Agent: 解釋結果給用戶
```

**問題**：NSForge 在這裡扮演什麼角色？

### 質疑 3：論文公式應該是外部注入
**用戶觀點**：
- 最新論文的公式 Agent 不知道
- 這應該是 RAG (檢索增強生成) 的問題
- 不需要專門的「公式庫」

**反思**：
- ✅ 正確！最新論文應該用 RAG
- ✅ 可以用 arXiv, Semantic Scholar API
- ❓ NSForge 在這裡的角色？

---

## 💡 重新定位：NSForge 的獨特價值

### ❌ 不是這些（已有現成解決方案）

| 功能 | 現有解決方案 | 不需要 NSForge |
|------|-------------|---------------|
| 基礎公式 | Agent 知識 + Wikipedia | ✅ |
| 符號運算 | sympy-mcp | ✅ |
| 數值計算 | NumPy, SciPy | ✅ |
| 電路模擬 | lcapy, PySpice | ✅ |
| 論文檢索 | RAG + arXiv API | ✅ |

### ✅ 可能的獨特價值

#### 1. **領域特定修正項庫** ⭐⭐⭐

**問題**：Agent 知道理想公式，但不知道實際修正項

**範例**：
```python
# Agent 知道：
V = I * R  # 歐姆定律

# 但 Agent 可能不知道：
- 電阻的溫度係數：R(T) = R₀(1 + α(T-T₀))
- 寄生電感：Z(ω) = R + jωL_parasitic
- 熱噪聲：V_noise = √(4kTRΔf)
```

**NSForge 的價值**：
- 提供「修正項模板」
- 告訴 Agent 「什麼情況下需要哪個修正」
- 給出典型數值範圍

**實作方式**：
```yaml
# formulas/modifications/parasitic_inductance.yaml
modification:
  id: parasitic_inductance
  applies_to: ["resistor", "capacitor"]
  term: "s * L_parasitic"
  typical_values:
    smd_resistor: "0.5-2 nH"
    through_hole: "5-20 nH"
  when_to_use:
    - frequency: "> 10 MHz"
    - scenario: "RF circuit design"
  reference: "Johnson & Graham, High Speed Digital Design (1993)"
```

#### 2. **推導策略編排** ⭐⭐

**問題**：Agent 可能用錯推導路徑

**範例**：分析 RLC 電路

```
❌ Agent 可能這樣做：
  直接寫微分方程 → 求解 → 複雜

✅ 更好的策略：
  用阻抗法 → Laplace 域 → 轉移函數 → 簡單
```

**NSForge 的價值**：
- 提供「推導策略模板」
- 指導 Agent 選擇最佳路徑

**但實話說**：這個功能有點弱，Agent 自己也能學會選策略。

#### 3. **人類可讀的推導步驟** ⭐⭐⭐

**問題**：Agent + sympy-mcp 能算出答案，但過程對人類不清楚

**現況**：
```
Agent: "答案是 32.8 公尺"
User: "為什麼？"
Agent: "我用了動能定理和功能原理"
User: "能看到完整步驟嗎？"
Agent: "呃..." (只能重新解釋一次)
```

**NSForge 的價值**：
- 生成結構化的推導文檔（像我們做的 power-amp 範例）
- 支援 LaTeX、圖表、註解
- 可追溯每一步的來源

**實作方式**：
```python
derivation = nsforge.derive(
    problem="braking distance on wet road",
    visualize=True,  # 生成圖表
    explain_level="detailed"  # 詳細解釋
)

# 輸出 Markdown + LaTeX + 圖表
derivation.export("braking_analysis.md")
```

#### 4. **專家經驗規則庫** ⭐⭐⭐⭐

**問題**：論文中的經驗公式、設計準則 Agent 不知道

**範例（電路設計）**：
```yaml
# 這些 Agent 不知道！
expert_rules:
  - id: bypass_cap_placement
    rule: "旁路電容應放在 IC 電源腳 < 1cm"
    reason: "減少寄生電感"
    reference: "Henry Ott, EMC Design (2009)"
    
  - id: trace_impedance
    rule: "50Ω microstrip: W/H ≈ 2 (FR4)"
    context: "控制阻抗設計"
    
  - id: opamp_stability
    rule: "閉迴路增益 > 10 for general-purpose opamps"
    reason: "避免振盪"
```

**NSForge 的價值**：
- 封裝領域專家知識
- Agent 可以查詢並應用
- 附帶參考文獻，可驗證

#### 5. **互動式工具/視覺化** ⭐⭐

**問題**：用戶想「玩弄參數」看效果

**現有方案**：
- Desmos (數學)
- Falstad Circuit Simulator (電路)
- GeoGebra (幾何)

**NSForge 的價值**：
- 整合推導 + 視覺化
- 參數調整後自動重新推導

**但實話說**：已有很多專門工具，這個優先度低。

---

## 🎯 重新定位後的結論

### NSForge 應該做什麼？

**核心定位**：**領域專家知識的 MCP Server**

```
┌─────────────────────────────────────────────────┐
│  NSForge = 專家經驗規則 + 修正項庫 + 推導模板   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ✅ 提供：                                      │
│   - 修正項庫（Agent 不知道的實際因素）         │
│   - 專家設計準則（論文/經驗）                   │
│   - 結構化推導輸出（人類可讀）                  │
│                                                 │
│  ❌ 不提供：                                    │
│   - 基礎公式（Agent 已知）                      │
│   - 符號運算引擎（sympy-mcp 已有）              │
│   - 論文檢索（用 RAG）                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 使用場景範例

#### 場景 1：電路設計
```
User: "設計 100MHz 的 LC 濾波器"

Agent 查詢 NSForge:
  - get_modifications(domain="rf_circuits", freq="100MHz")
    → 返回：寄生電容、Q 值損耗、PCB 效應
  
  - get_expert_rules(topic="rf_filter_design")
    → 返回：元件選型指南、佈局注意事項

Agent 結合 sympy-mcp 計算 → 給出完整設計
```

#### 場景 2：藥物劑量計算
```
User: "兒童 amoxicillin 劑量"

Agent 查詢 NSForge:
  - get_modifications(domain="pediatric_pharmacology")
    → 返回：體重修正、腎功能修正
  
  - get_dosing_guidelines(drug="amoxicillin", age="pediatric")
    → 返回：FDA 指南、常見劑量範圍

Agent 計算 + 警告 → 安全劑量建議
```

---

## 🔄 與現有工具的協作

```
User Question
     ↓
┌─────────────────────────────────────────┐
│  Agent (LLM)                            │
│  - 理解問題                              │
│  - 規劃推導策略                          │
└─────────────────────────────────────────┘
     ↓ 需要專家知識？
┌─────────────────────────────────────────┐
│  NSForge MCP                            │
│  - 提供修正項                            │
│  - 提供設計準則                          │
│  - 提供推導模板                          │
└─────────────────────────────────────────┘
     ↓ 需要計算？
┌─────────────────────────────────────────┐
│  sympy-mcp                              │
│  - 精確符號運算                          │
│  - 解方程、積分、微分                    │
└─────────────────────────────────────────┘
     ↓ 需要論文？
┌─────────────────────────────────────────┐
│  RAG (arXiv/PubMed)                     │
│  - 檢索相關論文                          │
│  - 提取公式和數據                        │
└─────────────────────────────────────────┘
     ↓
  Complete Answer
```

---

## 💭 誠實的評估

### 優勢
- ✅ 填補「專家經驗」這個空白
- ✅ 提供結構化、可追溯的推導
- ✅ 特定領域（音響、藥動）有價值

### 劣勢
- ❌ 需要大量人工整理專家知識
- ❌ 維護成本高（要跟上論文更新）
- ❌ 可能覆蓋面有限（不如 LLM 廣）

### 替代方案
如果不做 NSForge，用戶可以：
1. **直接問 Agent + sympy-mcp**（已經很好）
2. **RAG + 論文**（最新知識）
3. **專門工具**（Falstad, LTSpice, Desmos）

---

## 🎲 決策點

### 選項 A：繼續開發 NSForge（縮小範圍）
- 聚焦 1-2 個領域（音響電路、藥動）
- 只做「修正項庫 + 專家規則」
- 不做通用推導引擎

### 選項 B：轉型為「專家知識 RAG」
- 不做 MCP Server
- 改做「領域專家 Prompt Library」
- 整理成 System Prompt 供 Agent 使用

### 選項 C：整合到現有工具
- 為 sympy-mcp 貢獻「領域擴展」
- 不獨立做一個專案
- 以插件形式存在

### 選項 D：暫停開發
- 承認目前沒有足夠獨特價值
- 等待更清晰的需求場景
- 先用現有工具（Agent + sympy-mcp）

---

## 🗣️ 用戶的決定？

**請用戶選擇**：
1. 你覺得 NSForge 最有價值的是哪一部分？
2. 是否值得為「修正項庫 + 專家規則」建一個 MCP Server？
3. 還是直接用 Agent + sympy-mcp + RAG 就夠了？

**我的建議**：
- 如果你真的需要在音響電路/藥動這兩個領域深入，做選項 A
- 如果只是偶爾用用，選項 D（暫停，用現有工具）更實際

---

**Status**: Awaiting User Decision  
**Next Steps**: 根據用戶選擇調整專案方向
