# Roadmap

專案發展路線圖與功能規劃。

## 🧭 北極星藍圖：泛公式探討

統一施工藍圖見 **[docs/general-formula-exploration-roadmap.md](docs/general-formula-exploration-roadmap.md)**：把「探索 → 提出 → 實體化 → 驗證 → 自我修正 → 存檔 → 評測」串成可驗證的探索迴圈（7 階段）。下方 v0.2.0 的「自動驗證器 / 推導建議器」對應該藍圖的階段 3–4。

- 現況：階段 0 ✅（87 工具 + 自駕基座 L0–L3 + 實體化階梯方向）
- 下一步：階段 1（接通 L3 引擎）→ 階段 2（推導評測 gate）

## 已完成 ✅

### v0.1.0+ (2025-12-15)
- [x] 專案初始化
- [x] Memory Bank 系統建立
- [x] Claude Skills 基礎架構
- [x] Git 文檔自動更新 Skill
- [x] 🎯 **NSForge Skills 系統** - 5 個專業推導工作流程
  - [x] `nsforge-derivation-workflow` - 完整推導工作流
  - [x] `nsforge-verification-suite` - 驗證工具組合
  - [x] `nsforge-formula-management` - 公式庫管理
  - [x] `nsforge-code-generation` - 程式碼/報告生成
  - [x] `nsforge-quick-calculate` - 快速計算
- [x] 📚 **完整文檔系統**
  - [x] `docs/nsforge-skills-guide.md` (588 行) - Agent 使用指南
  - [x] `.claude/skills/nsforge-verification-suite/SKILL.md` (522 行)
  - [x] Skills 觸發詞、工作流程圖、41 個工具清單
- [x] 🔬 **3 個高品質推導範例**
  - [x] NPO 抗生素效應（pH 依賴性吸收）
  - [x] 溫度校正 Michaelis-Menten（酵素動力學）
  - [x] Cisatracurium 多次給藥（水解型藥物累積）
- [x] 🐍 **Python 應用範例**
  - [x] `examples/npo_antibiotic_analysis.py` (251 行)
- [x] 🔄 **Handoff 機制** - NSForge ↔ SymPy-MCP 無縫整合
  - [x] `derivation_export_for_sympy()` - 導出狀態
  - [x] `derivation_import_from_sympy()` - 導入結果
  - [x] `derivation_handoff_status()` - 能力邊界查看
- [x] 📝 **步進式推導工作流**
  - [x] `derivation_record_step()` - 記錄計算 + 人類洞見
  - [x] `derivation_add_note()` - 加入臨床註記
- [x] ✅ **驗證工具增強** (6 個函數)

## 進行中 🚧

- [ ] 完善 Skills 觸發機制（部分完成 - NSForge Skills 已上線）
- [ ] 測試文檔自動更新流程（部分完成 - CHANGELOG/README 已測試）

## 計劃中 📋

### v0.2.0 - 🧠 主動推導助手（核心差異化）

> **定位轉變**：NSForge 不只是「記錄器」，而是「推導助手」
> 
> 這才是 NSForge 真正的價值 —— Agent 自己寫 SymPy 也能算，但無法做到：
> - 每步自動驗證
> - 智慧建議下一步
> - 符號語義追蹤
> - 錯誤模式預警

#### 🔍 自動驗證器 (Auto-Validator)

每步推導後**自動**執行品質檢查：

- [ ] **維度一致性檢查** - 自動偵測 `Ea/RT` 是否無量綱
- [ ] **邊界條件驗證** - 自動測試 `T→∞`, `t→0` 等極限
- [ ] **符號定義檢查** - 警告未定義或重複定義的符號
- [ ] **數值合理性** - 代入典型值檢查結果是否合理
- [ ] **單位傳播追蹤** - 追蹤每個符號的單位

#### 💡 推導建議器 (Derivation Advisor)

根據知識庫**主動建議**：

- [ ] **相關推導搜尋** - 「你之前做過類似的：temp_corrected_elimination」
- [ ] **下一步建議** - 「通常這裡會取穩態極限」
- [ ] **引用建議** - 「可以引用已驗證的 Arrhenius 公式」
- [ ] **警告提示** - 「注意：酵素在 >42°C 會變性」
- [ ] **組合發現** - 自動發現可組合的公式對

#### 🏷️ 符號語義追蹤 (Symbol Semantics)

知道每個符號**是什麼**，不只是名稱：

- [ ] **符號註冊表** - 記錄 `k` 是速率常數還是波茲曼常數
- [ ] **語義衝突檢測** - 「你用了兩個 `R`，一個是電阻一個是氣體常數」
- [ ] **上下文推斷** - 根據共現符號推斷意義
- [ ] **跨推導追蹤** - 同一符號在不同推導中的意義
- [ ] **單位推斷** - 從語義自動推斷物理單位

#### ⚠️ 錯誤模式檢測 (Error Pattern Detection)

檢測**常見錯誤**並預警：

- [ ] **量綱錯誤** - exp() 內必須無量綱
- [ ] **符號遺漏** - 結果中有未定義的符號
- [ ] **假設衝突** - 「你假設 x>0，但這裡 x 可能為負」
- [ ] **數值爆炸** - 結果趨向無窮大
- [ ] **常見代數錯誤** - 如 `(a+b)² ≠ a²+b²` 的誤用

### v0.2.1 - 進階數學能力 🧮 (已完成 ✅)

> **設計原則**：工具名稱保持**領域無關**，語義由用戶提供
> 
> 例：`calculate_limit()` 而非 `calculate_steady_state()`
> 藥學家稱「穩態濃度」，物理學家稱「平衡位置」，工具不預設領域

- [x] 🔄 **極限與級數** (3 個工具)
  - [x] `calculate_limit()` - 極限計算（含 ±∞、方向）
  - [x] `calculate_series()` - Taylor/Laurent/Fourier 展開
  - [x] `calculate_summation()` - 符號求和（有限/無窮）

- [x] 📐 **不等式求解** (2 個工具)
  - [x] `solve_inequality()` - 單變數不等式
  - [x] `solve_inequality_system()` - 不等式系統（區間交集）

- [x] 🎲 **統計分佈** (3 個工具)
  - [x] `define_distribution()` - 定義分佈（Normal, Exponential 等）
  - [x] `distribution_stats()` - 期望值、變異數、偏度等
  - [x] `distribution_probability()` - 機率計算 P(X < a)

- [x] ✓ **假設查詢** (2 個工具)
  - [x] `query_assumptions()` - 符號屬性查詢（positive, real 等）
  - [x] `refine_expression()` - 基於假設簡化（如 √x² → x）

### v0.3.0 - 程式碼生成增強 💻

- [ ] 多語言程式碼生成 (C, Fortran, JavaScript)
- [ ] 數值優化程式碼（NumPy vectorization）
- [ ] NONMEM/Monolix 格式輸出

### 短期目標

- [ ] 新增更多實用 Skills
- [ ] 建立專案模板系統
- [ ] 整合 CI/CD 流程

### 長期目標

- [ ] Skills 分享與匯入機制
- [ ] 多專案 Memory Bank 同步
- [ ] 自定義 Agent 建立
- [ ] 向 SymPy-MCP 上游貢獻通用功能
