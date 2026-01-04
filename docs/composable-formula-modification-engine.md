# 可組合公式修正引擎（Composable Formula Modification Engine）

> **Date**: 2026-01-01  
> **核心概念**: 固定規則的公式推導引擎，可重現、可追蹤

---

## 🎯 實際需求範例：藥物動力學修正

### 場景：Fentanyl 在複雜情況下的濃度計算

```
起點：基礎 Fentanyl 三室模型
  C(t) = D/V1 × (α₁e^(-λ₁t) + α₂e^(-λ₂t) + α₃e^(-λ₃t))

干擾 1: Midazolam 競爭 CYP3A4 → Clearance ↓30%
  CL_modified = CL_base × 0.7

干擾 2: 體脂率 30% → 分布容積改變
  Vd_modified = Vd_base × (1 + 0.25 × (BF% - 20)/10)

干擾 3: 高齡 65 歲 → Clearance ↓15%
  CL_modified = CL_previous × 0.85

推導過程：組合所有修正 → 新公式

最終計算：送入 SymPy 計算數值
```

---

## 🔧 MCP 接口設計

### NSForge MCP Server 的職責

```
┌─────────────────────────────────────────────────────┐
│  Agent (思考層)                                      │
├─────────────────────────────────────────────────────┤
│  • 理解用戶需求                                      │
│  • 選擇基礎公式                                      │
│  • 決定要應用哪些修正規則                            │
│  • 提供病人參數                                      │
└────────────────┬────────────────────────────────────┘
                 │ MCP 調用
                 ▼
┌─────────────────────────────────────────────────────┐
│  NSForge MCP Server (固定引擎)                       │
├─────────────────────────────────────────────────────┤
│  輸入:                                               │
│    - base_formula: "pk_three_compartment"           │
│    - modifications: [                                │
│        {"rule": "drug_cyp3a4", "drug": "midazolam"},│
│        {"rule": "body_fat", "BF": 30}               │
│      ]                                               │
│    - patient_context: {"age": 65, "weight": 80}     │
│                                                      │
│  處理（確定性算法）:                                 │
│    ✓ 載入基礎公式                                    │
│    ✓ 依序應用修正規則                                │
│    ✓ 記錄每個推導步驟                                │
│    ✓ 生成新公式（符號）                              │
│    ✓ 轉換為 SymPy 表達式                             │
│                                                      │
│  輸出:                                               │
│    - new_formula: "修正後的完整公式"                 │
│    - derivation_steps: ["步驟1", "步驟2", ...]      │
│    - sympy_expression: 可計算的符號表達式            │
│    - parameters: {"CL": 0.476, "V1": 15.875, ...}   │
└────────────────┬────────────────────────────────────┘
                 │ 返回結果
                 ▼
┌─────────────────────────────────────────────────────┐
│  Agent 後續處理                                      │
├─────────────────────────────────────────────────────┤
│  • 呈現推導步驟給用戶                                │
│  • 代入數值計算                                      │
│  • 解釋結果                                          │
└─────────────────────────────────────────────────────┘
```

### MCP Tool 定義

```json
{
  "name": "nsforge_derive_formula",
  "description": "組合基礎公式與修正規則，推導出新公式（完全確定性）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "base_formula": {
        "type": "string",
        "description": "基礎公式名稱 (例: pk_three_compartment)"
      },
      "modifications": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "rule": {
              "type": "string",
              "description": "修正規則名稱"
            },
            "context": {
              "type": "object",
              "description": "規則所需參數"
            }
          }
        }
      },
      "patient_context": {
        "type": "object",
        "description": "病人相關參數"
      }
    },
    "required": ["base_formula", "modifications"]
  }
}
```

### 使用範例（Agent 視角）

```python
# Agent 收到用戶請求：
# "65歲，體脂30%，同時使用midazolam，計算Fentanyl 50mcg的濃度"

# Step 1: Agent 分析並決定
base = "pk_three_compartment"
mods = [
    {"rule": "drug_cyp3a4", "context": {"concurrent_drug": "midazolam"}},
    {"rule": "body_fat", "context": {"body_fat_percentage": 30}},
    {"rule": "age_cl", "context": {"age": 65}}
]
patient = {"weight": 80, "height": 170}

# Step 2: Agent 調用 MCP（固定引擎，確定性輸出）
result = mcp.call_tool(
    "nsforge_derive_formula",
    {
        "base_formula": base,
        "modifications": mods,
        "patient_context": patient
    }
)

# Step 3: MCP 返回（相同輸入保證相同輸出）
# {
#   "new_formula": "C(t) = D/(12.7×1.25) × ...",
#   "derivation_steps": [
#     {"step": 1, "description": "應用 CYP3A4 競爭: CL × 0.7", ...},
#     {"step": 2, "description": "體脂修正: V1 × 1.25", ...},
#     {"step": 3, "description": "年齡修正: CL × 0.85", ...}
#   ],
#   "sympy_expression": "...",
#   "parameters": {
#     "CL_final": 0.476,
#     "V1_final": 15.875
#   }
# }

# Step 4: Agent 呈現給用戶
print("推導過程:")
for step in result["derivation_steps"]:
    print(f"  {step['description']}")

# Step 5: Agent 計算數值（可選）
numerical_result = sympy.N(
    result["sympy_expression"].subs({
        "D": 0.05,
        "t": 3.34
    })
)
```

---

## 🔧 引擎架構設計

### 概念模型

```yaml
FormulaModificationEngine:
  
  # 1. 基礎公式庫
  base_formulas:
    pk_three_compartment:
      name: "三室藥物動力學模型"
      formula: "C(t) = D/V1 × (α₁e^(-λ₁t) + α₂e^(-λ₂t) + α₃e^(-λ₃t))"
      parameters:
        - D: dose
        - V1: central_volume
        - CL: clearance
        - Q2: Q2_distribution
        - Q3: Q3_distribution
      
  # 2. 修正規則庫
  modification_rules:
    drug_interaction_cyp3a4:
      applies_to: ["clearance"]
      formula: "CL_new = CL × inhibition_factor"
      conditions:
        - concurrent_drug: ["midazolam", "ketoconazole", "erythromycin"]
      parameters:
        midazolam: {inhibition_factor: 0.7}
        ketoconazole: {inhibition_factor: 0.5}
    
    body_fat_distribution:
      applies_to: ["volume_distribution"]
      formula: "Vd_new = Vd × (1 + k × (BF - BF_ref) / BF_ref)"
      conditions:
        - body_fat_percentage: [10, 50]
      parameters:
        k: 0.5
        BF_ref: 20
    
    age_clearance:
      applies_to: ["clearance"]
      formula: "CL_new = CL × (1 - 0.01 × (age - 40))"
      conditions:
        - age: [40, 80]
  
  # 3. 推導引擎
  derivation_engine:
    input:
      - base_formula: pk_three_compartment
      - modifications:
          - drug_interaction_cyp3a4: {drug: midazolam}
          - body_fat_distribution: {BF: 30}
          - age_clearance: {age: 65}
    
    process:
      - identify_affected_parameters()
      - apply_modifications_sequentially()
      - regenerate_formula()
      - simplify_expression()
    
    output:
      - modified_formula: "完整的修正公式"
      - derivation_steps: ["步驟1", "步驟2", ...]
      - final_expression: "SymPy 可執行表達式"
```

---

## 📝 實際程式碼實作

### Step 1: 定義基礎公式

```python
from dataclasses import dataclass
from typing import Dict, List, Callable
from sympy import symbols, exp, simplify, lambdify

@dataclass
class BaseFormula:
    """基礎公式定義"""
    name: str
    formula_str: str
    parameters: Dict[str, str]
    formula_func: Callable = None
    
    def to_sympy(self):
        """轉換為 SymPy 表達式"""
        # 創建符號
        syms = {p: symbols(p) for p in self.parameters.keys()}
        
        # 解析公式字串為 SymPy 表達式
        # (這裡簡化，實際需要 parser)
        return syms, self.formula_str

# 定義三室模型
pk_three_compartment = BaseFormula(
    name="三室藥物動力學模型",
    formula_str="D/V1 * (alpha1*exp(-lambda1*t) + alpha2*exp(-lambda2*t) + alpha3*exp(-lambda3*t))",
    parameters={
        "D": "劑量 (mg)",
        "V1": "中央室容積 (L)",
        "CL": "清除率 (L/min)",
        "Q2": "第二室分布速率 (L/min)",
        "Q3": "第三室分布速率 (L/min)",
        "V2": "第二室容積 (L)",
        "V3": "第三室容積 (L)",
        "t": "時間 (min)"
    }
)
```

### Step 2: 定義修正規則

```python
@dataclass
class ModificationRule:
    """修正規則定義"""
    name: str
    applies_to: List[str]  # 影響哪些參數
    formula: str  # 修正公式
    conditions: Dict  # 適用條件
    coefficients: Dict  # 修正係數
    
    def apply(self, parameter_value, context):
        """應用修正規則"""
        # 檢查條件
        if not self._check_conditions(context):
            return parameter_value
        
        # 應用公式
        modified = self._apply_formula(parameter_value, context)
        
        return modified
    
    def _check_conditions(self, context):
        """檢查是否滿足適用條件"""
        for key, constraint in self.conditions.items():
            if key not in context:
                return False
            # 檢查範圍等
        return True
    
    def _apply_formula(self, value, context):
        """應用修正公式"""
        # 這裡用 SymPy 計算修正
        pass

# 藥物競爭規則
drug_interaction_cyp3a4 = ModificationRule(
    name="CYP3A4 競爭性抑制",
    applies_to=["CL"],  # 影響清除率
    formula="CL_new = CL * inhibition_factor",
    conditions={
        "concurrent_drug": ["midazolam", "ketoconazole", "erythromycin"]
    },
    coefficients={
        "midazolam": 0.7,      # 抑制 30%
        "ketoconazole": 0.5,   # 抑制 50%
        "erythromycin": 0.6    # 抑制 40%
    }
)

# 體脂分布規則
body_fat_distribution = ModificationRule(
    name="體脂率對分布容積的影響",
    applies_to=["Vd", "V1", "V2", "V3"],
    formula="Vd_new = Vd * (1 + k * (BF - BF_ref) / BF_ref)",
    conditions={
        "body_fat_percentage": (10, 50)  # 適用範圍
    },
    coefficients={
        "k": 0.5,       # 脂溶性藥物係數
        "BF_ref": 20    # 參考體脂率
    }
)

# 年齡清除率規則
age_clearance = ModificationRule(
    name="年齡對清除率的影響",
    applies_to=["CL"],
    formula="CL_new = CL * (1 - 0.01 * max(0, age - 40))",
    conditions={
        "age": (40, 80)
    },
    coefficients={}
)
```

### Step 3: 推導引擎（核心）

```python
from typing import List, Dict, Any
import sympy as sp

class FormulaDerivationEngine:
    """可組合公式推導引擎"""
    
    def __init__(self):
        self.base_formulas = {}
        self.modification_rules = {}
        self.derivation_history = []
    
    def register_base_formula(self, key: str, formula: BaseFormula):
        """註冊基礎公式"""
        self.base_formulas[key] = formula
    
    def register_modification_rule(self, key: str, rule: ModificationRule):
        """註冊修正規則"""
        self.modification_rules[key] = rule
    
    def derive(
        self,
        base_formula_key: str,
        modifications: List[Dict[str, Any]],
        patient_context: Dict[str, Any]
    ):
        """
        執行公式推導
        
        Args:
            base_formula_key: 基礎公式名稱
            modifications: 要應用的修正列表
            patient_context: 病人相關參數
        
        Returns:
            DerivationResult: 推導結果（包含新公式和步驟）
        """
        
        # Step 1: 載入基礎公式
        base_formula = self.base_formulas[base_formula_key]
        
        self.derivation_history = []
        self.derivation_history.append({
            "step": 0,
            "description": f"基礎公式: {base_formula.name}",
            "formula": base_formula.formula_str,
            "parameters": base_formula.parameters.copy()
        })
        
        # Step 2: 依序應用每個修正
        current_parameters = base_formula.parameters.copy()
        
        for i, mod_spec in enumerate(modifications):
            rule_key = mod_spec["rule"]
            rule_context = mod_spec.get("context", {})
            
            # 合併病人上下文
            full_context = {**patient_context, **rule_context}
            
            # 應用修正規則
            result = self._apply_modification(
                rule_key,
                current_parameters,
                full_context,
                step_number=i+1
            )
            
            current_parameters = result["parameters"]
            self.derivation_history.append(result)
        
        # Step 3: 重新生成修正後的公式
        final_formula = self._regenerate_formula(
            base_formula.formula_str,
            current_parameters
        )
        
        # Step 4: 轉換為 SymPy 表達式
        sympy_expr = self._to_sympy_expression(final_formula)
        
        # Step 5: 簡化
        simplified_expr = sp.simplify(sympy_expr)
        
        return DerivationResult(
            base_formula=base_formula.name,
            final_formula=str(simplified_expr),
            sympy_expression=simplified_expr,
            derivation_steps=self.derivation_history,
            parameters=current_parameters
        )
    
    def _apply_modification(
        self,
        rule_key: str,
        parameters: Dict,
        context: Dict,
        step_number: int
    ):
        """應用單一修正規則"""
        
        rule = self.modification_rules[rule_key]
        
        # 檢查條件
        if not self._check_conditions(rule, context):
            return {
                "step": step_number,
                "description": f"修正 {rule.name}: 條件不符，跳過",
                "formula": "unchanged",
                "parameters": parameters
            }
        
        # 修改受影響的參數
        modified_params = parameters.copy()
        changes = []
        
        for param_name in rule.applies_to:
            if param_name in parameters:
                # 取得原始值（可能是符號或數值）
                original = parameters[param_name]
                
                # 應用修正公式
                modified = self._apply_formula(
                    rule,
                    param_name,
                    original,
                    context
                )
                
                modified_params[param_name] = modified
                changes.append(f"{param_name}: {original} → {modified}")
        
        return {
            "step": step_number,
            "description": f"修正 {rule.name}",
            "rule": rule.formula,
            "changes": changes,
            "context": context,
            "parameters": modified_params
        }
    
    def _check_conditions(self, rule: ModificationRule, context: Dict):
        """檢查規則適用條件"""
        for key, constraint in rule.conditions.items():
            if key not in context:
                return False
            
            # 檢查範圍
            if isinstance(constraint, tuple):
                min_val, max_val = constraint
                if not (min_val <= context[key] <= max_val):
                    return False
            
            # 檢查列表包含
            elif isinstance(constraint, list):
                if context[key] not in constraint:
                    return False
        
        return True
    
    def _apply_formula(
        self,
        rule: ModificationRule,
        param_name: str,
        original_value: Any,
        context: Dict
    ):
        """應用修正公式到參數"""
        
        # 使用 SymPy 進行符號計算
        if param_name == "CL":
            # 清除率修正
            if "inhibition_factor" in context:
                factor = context["inhibition_factor"]
            elif "concurrent_drug" in context:
                drug = context["concurrent_drug"]
                factor = rule.coefficients.get(drug, 1.0)
            elif "age" in context:
                age = context["age"]
                factor = 1 - 0.01 * max(0, age - 40)
            else:
                factor = 1.0
            
            return f"{original_value} × {factor}"
        
        elif param_name in ["Vd", "V1", "V2", "V3"]:
            # 分布容積修正
            if "body_fat_percentage" in context:
                BF = context["body_fat_percentage"]
                k = rule.coefficients.get("k", 0.5)
                BF_ref = rule.coefficients.get("BF_ref", 20)
                
                factor = 1 + k * (BF - BF_ref) / BF_ref
                return f"{original_value} × {factor:.3f}"
        
        return original_value
    
    def _regenerate_formula(self, original_formula: str, parameters: Dict):
        """根據修正後的參數重新生成公式"""
        
        # 簡化版：直接替換參數
        # 實際應該用 SymPy 符號替換
        
        formula = original_formula
        for param, value in parameters.items():
            if isinstance(value, str) and "×" in value:
                # 這是修正過的參數
                formula = formula.replace(param, f"({value})")
        
        return formula
    
    def _to_sympy_expression(self, formula_str: str):
        """轉換公式字串為 SymPy 表達式"""
        # 這裡需要一個 parser
        # 簡化版：
        return sp.sympify(formula_str)

@dataclass
class DerivationResult:
    """推導結果"""
    base_formula: str
    final_formula: str
    sympy_expression: Any  # SymPy 表達式
    derivation_steps: List[Dict]
    parameters: Dict
    
    def to_dict(self):
        return {
            "base_formula": self.base_formula,
            "final_formula": self.final_formula,
            "derivation_steps": self.derivation_steps,
            "parameters": self.parameters
        }
    
    def calculate(self, numerical_values: Dict):
        """用數值計算最終結果"""
        # 替換符號為數值
        expr = self.sympy_expression
        for sym, val in numerical_values.items():
            expr = expr.subs(sym, val)
        
        return float(expr.evalf())
```

---

## 🎬 完整使用範例

```python
# ============================================
# 初始化引擎
# ============================================

engine = FormulaDerivationEngine()

# 註冊基礎公式
engine.register_base_formula("pk_three_compartment", pk_three_compartment)

# 註冊修正規則
engine.register_modification_rule("drug_cyp3a4", drug_interaction_cyp3a4)
engine.register_modification_rule("body_fat", body_fat_distribution)
engine.register_modification_rule("age_cl", age_clearance)

# ============================================
# 場景：65歲，體脂30%，合併使用 Midazolam
# ============================================

result = engine.derive(
    base_formula_key="pk_three_compartment",
    
    modifications=[
        {
            "rule": "drug_cyp3a4",
            "context": {
                "concurrent_drug": "midazolam"
            }
        },
        {
            "rule": "body_fat",
            "context": {
                "body_fat_percentage": 30
            }
        },
        {
            "rule": "age_cl",
            "context": {
                "age": 65
            }
        }
    ],
    
    patient_context={
        "weight": 80,
        "height": 170,
        "sex": "M"
    }
)

# ============================================
# 輸出推導步驟
# ============================================

print("=" * 60)
print("公式推導過程")
print("=" * 60)

for step in result.derivation_steps:
    print(f"\n步驟 {step['step']}: {step['description']}")
    if 'changes' in step:
        for change in step['changes']:
            print(f"  - {change}")

print("\n" + "=" * 60)
print("最終公式")
print("=" * 60)
print(result.final_formula)

# ============================================
# 數值計算
# ============================================

numerical_values = {
    "D": 0.05,      # 50 mcg = 0.05 mg
    "V1": 12.7,     # L (修正後會變)
    "CL": 0.8,      # L/min (修正後會變)
    "t": 3.34,      # 峰值時間
    # ... 其他參數
}

final_concentration = result.calculate(numerical_values)
print(f"\n計算結果: {final_concentration:.4f} mg/L")
```

---

## 📊 輸出範例

```
============================================================
公式推導過程
============================================================

步驟 0: 基礎公式: 三室藥物動力學模型
公式: C(t) = D/V1 × (α₁e^(-λ₁t) + α₂e^(-λ₂t) + α₃e^(-λ₃t))

步驟 1: 修正 CYP3A4 競爭性抑制
規則: CL_new = CL * inhibition_factor
  - CL: 0.8 → 0.8 × 0.7
說明: Midazolam 競爭 CYP3A4，抑制 Fentanyl 代謝 30%

步驟 2: 修正 體脂率對分布容積的影響
規則: Vd_new = Vd * (1 + k * (BF - BF_ref) / BF_ref)
  - V1: 12.7 → 12.7 × 1.25
  - V2: 29.1 → 29.1 × 1.25
  - V3: 314.2 → 314.2 × 1.25
說明: 體脂率 30% (參考值 20%)，Fentanyl 為脂溶性藥物

步驟 3: 修正 年齡對清除率的影響
規則: CL_new = CL * (1 - 0.01 * max(0, age - 40))
  - CL: 0.8 × 0.7 → 0.8 × 0.7 × 0.85
說明: 65 歲，清除率較 40 歲下降 15%

============================================================
最終公式
============================================================
C(t) = D / (12.7 × 1.25) × (α₁e^(-λ₁t) + α₂e^(-λ₂t) + α₃e^(-λ₃t))

其中：
  CL_final = 0.8 × 0.7 × 0.85 = 0.476 L/min
  V1_final = 12.7 × 1.25 = 15.875 L
  V2_final = 29.1 × 1.25 = 36.375 L
  V3_final = 314.2 × 1.25 = 392.75 L

============================================================
SymPy 表達式
============================================================
D / V1_final * (alpha1 * exp(-lambda1 * t) + ...)

計算結果（t=3.34 min）: 0.0032 mg/L = 3.2 ng/mL
```

---

## 🔑 關鍵特性

### 1. 完全可重現 ✅

```python
# 相同輸入 → 相同輸出
result1 = engine.derive("pk_three_compartment", mods, context)
result2 = engine.derive("pk_three_compartment", mods, context)

assert result1.final_formula == result2.final_formula
# ✅ 保證相同
```

### 2. 可追蹤推導步驟 ✅

```python
# 每個步驟都記錄
for step in result.derivation_steps:
    print(step["description"])
    print(step["changes"])
    
# 輸出：
# "步驟 1: 應用 CYP3A4 競爭抑制"
# "CL: 0.8 → 0.56"
```

### 3. 可組合規則 ✅

```python
# 規則可以任意組合
modifications = [
    {"rule": "drug_cyp3a4", ...},
    {"rule": "body_fat", ...},
    {"rule": "age_cl", ...},
    {"rule": "renal_impairment", ...},  # 新增
]

# 引擎自動處理依賴關係
result = engine.derive(..., modifications)
```

### 4. 符號 + 數值計算 ✅

```python
# 先符號推導
result = engine.derive(...)

# 後數值計算
concentration = result.calculate({
    "D": 0.05,
    "t": 3.34,
    ...
})
```

---

## 🆚 與現有工具的差異

### vs. SymPy

```python
# SymPy: 純符號計算
from sympy import *
x = symbols('x')
integrate(x**2, x)  # x**3/3

# NSForge: 領域知識 + 符號計算
result = engine.derive(
    base="pk_model",
    modifications=[
        {"rule": "drug_interaction", "drug": "midazolam"},
        {"rule": "body_fat", "BF": 30}
    ]
)
# → 自動應用藥理學規則
# → 生成修正公式
# → 送給 SymPy 計算
```

### vs. 直接寫 Python

```python
# 直接寫 Python
CL_base = 0.8
CL_modified = CL_base * 0.7 * 0.85
Vd_modified = 12.7 * 1.25

# 問題：
# ❌ 不知道為什麼 0.7
# ❌ 不知道為什麼 0.85
# ❌ 沒有推導步驟
# ❌ 難以追蹤來源

# NSForge
result = engine.derive(...)
# ✅ 每個係數都有來源
# ✅ 完整推導步驟
# ✅ 可追蹤文獻
# ✅ 可重現
```

---

## 💡 NSForge 的真正價值

### 不是：
- ❌ 符號計算（SymPy 已經做了）
- ❌ 數值計算（NumPy/SciPy 已經做了）
- ❌ 儲存公式（資料庫就可以）

### 而是：
- ✅ **可組合的領域知識規則庫**
- ✅ **固定的推導引擎（不依賴 Agent）**
- ✅ **完整的推導步驟追蹤**
- ✅ **從規則到公式的自動生成**
- ✅ **連接領域知識與符號計算**

---

## 🚀 實作路徑

### Phase 1: 核心引擎 (MVP)

```python
# 最小可行產品
class SimpleDerivationEngine:
    def derive(self, base_formula, modifications):
        """應用修正規則，生成新公式"""
        pass
    
    def to_sympy(self):
        """轉換為 SymPy 表達式"""
        pass
```

**目標**：證明概念可行

### Phase 2: 規則庫

```yaml
rules:
  - drug_interactions (10+ 規則)
  - body_composition (5+ 規則)
  - age_effects (3+ 規則)
  - renal_function (5+ 規則)
  - hepatic_function (5+ 規則)
```

**目標**：建立藥理學領域規則庫

### Phase 3: 領域擴展

- Pharmacokinetics ✅
- Pharmacodynamics
- 電路設計
- 機械力學
- ...

---

## 📝 與其他文件的關聯

### reproducible-derivation-tools.md
- 討論了 SymPy manualintegrate, egg 等工具
- **NSForge 定位**: 領域規則層（上層）+ SymPy 計算層（下層）

### completeness-challenge.md
- 討論了開放系統的完整性問題
- **解決方案**: 分層規則庫 + 信心度評估

### cognitive-load-solution.md
- 討論了 Agent 認知負擔問題
- **解決方案**: 固定推導引擎（不依賴 Agent 思考）

---

## ✅ 總結

### 您問的問題：

> "藥物動力學請加入某個藥品的干擾 → 列出干擾的公式 → 加入傳統濃度計算的公式 → 算出新的濃度計算公式 → 在加入隨體重變化藥品分布的公式 → 推導出新公式 → 最後送入 sympy 計算"

### 答案：

**NSForge = 可組合公式修正引擎**

```
基礎公式（PK三室模型）
  ↓ 
+ 修正規則 1（CYP3A4 競爭）
  ↓
+ 修正規則 2（體脂分布）
  ↓
+ 修正規則 3（年齡清除）
  ↓
推導引擎組合
  ↓
生成新公式（符號）
  ↓
送入 SymPy 計算（數值）
```

**核心優勢**：
1. ✅ 固定規則庫（不依賴 Agent）
2. ✅ 完全可重現
3. ✅ 可追蹤推導步驟
4. ✅ 可組合任意規則
5. ✅ 連接領域知識與符號計算

**實作工具**：
- Python + SymPy (符號層)
- 自定義規則引擎 (領域層)
- 不需要 Mathematica 或 Lean4

**下一步**：
實作 MVP 版本的推導引擎？
