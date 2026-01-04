# 可重現符號推導工具調查

> **Date**: 2026-01-01  
> **Key Question**: 有沒有「可重現的符號推導引擎」（不依賴 Agent 思考）？

---

## 🎯 問題的精確定義

### 我們需要什麼？

```
┌─────────────────────────────────────────────┐
│  不是這個：Agent 決定推導策略               │
├─────────────────────────────────────────────┤
│  User: "證明 ∫x²dx = x³/3"                  │
│  Agent: 思考... 決定用冪次規則...           │
│  sympy-mcp: 執行計算                        │
│  → 問題：每次可能走不同路徑（不可重現）     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  而是這個：固定的推導引擎                   │
├─────────────────────────────────────────────┤
│  User: derive(∫x²dx, method="power_rule")   │
│  Engine: 應用冪次規則（固定算法）            │
│  Output: x³/3 + 詳細步驟                    │
│  → 每次相同輸入 = 相同輸出（可重現）        │
└─────────────────────────────────────────────┘
```

### 核心需求

```yaml
ideal_derivation_engine:
  input:
    expression: "∫x²dx"
    goal: "求積分"
    method: "power_rule"  # 或自動選擇
    
  process:
    - 識別表達式類型
    - 應用固定規則庫
    - 生成推導步驟
    - 驗證結果
    
  output:
    result: "x³/3 + C"
    steps:
      - "識別為多項式積分"
      - "應用冪次規則: ∫xⁿdx = xⁿ⁺¹/(n+1)"
      - "n=2, 得 x³/3"
      - "加積分常數 C"
    traceable: true
    reproducible: true  # 關鍵！
    
  不需要:
    - Agent 思考
    - 啟發式搜索
    - 機器學習
```

---

## 🔧 現有工具調查

### 類別 1: 定理證明助手（最接近理想）

#### 1.1 Lean4 ⭐⭐⭐⭐⭐

```lean4
-- Lean4 可以做到完全可重現的推導
theorem integrate_x_squared :
  ∫ x^2 = x^3/3 + C := by
  rw [integral_pow]  -- 應用冪次規則
  norm_num          -- 簡化數值
  
-- 特點：
-- ✅ 每個步驟都是確定性的 tactic
-- ✅ 完全可重現
-- ✅ 可以生成證明樹
-- ❌ 但需要手動寫證明
-- ❌ 不是「自動推導引擎」
```

**評估**：
- **可重現性**: ⭐⭐⭐⭐⭐ (完美)
- **自動化程度**: ⭐⭐ (需要手動證明)
- **適用性**: 適合驗證已知推導，不適合探索
- **學習曲線**: 陡峭

**是否符合需求**：
- ✅ 可重現
- ❌ 不是自動推導引擎
- 用途：驗證 NSForge 的推導是否正確

#### 1.2 Coq / Isabelle

類似 Lean4，都是定理證明助手。

---

### 類別 2: 商業符號系統（有推導能力）

#### 2.1 Mathematica / Wolfram Language ⭐⭐⭐⭐

```mathematica
(* Mathematica 有 step-by-step 推導 *)
Integrate[x^2, x, GenerateConditions -> False]
(* 輸出: x^3/3 *)

(* 但也可以用 Rubi (Rule-based Integrator) *)
Int[x^2, x]
(* 返回推導步驟 *)

(* 特點： *)
(* ✅ 有規則庫（Rule-based） *)
(* ✅ 可以追蹤步驟 *)
(* ✅ 確定性算法 *)
(* ❌ 商業軟體（昂貴） *)
(* ❌ 封閉原始碼 *)
```

**Rubi (Rule-based Integration)**：
- Mathematica 的積分引擎
- 基於 **6000+ 規則**
- 完全確定性（相同輸入 = 相同輸出）
- 可以導出推導步驟

**評估**：
- **可重現性**: ⭐⭐⭐⭐⭐
- **自動化程度**: ⭐⭐⭐⭐⭐
- **適用性**: 廣（微積分、代數、微分方程）
- **缺點**: 商業軟體，$$$

**是否符合需求**：
- ✅ 可重現
- ✅ 自動推導
- ✅ 有推導步驟
- ❌ 昂貴，不開源

#### 2.2 Maple ⭐⭐⭐⭐

類似 Mathematica，也有規則基推導。

---

### 類別 3: 開源符號系統

#### 3.1 SymPy (Python) ⭐⭐⭐

```python
from sympy import *
x = symbols('x')

# 基本積分
integrate(x**2, x)
# 輸出: x**3/3

# 但推導步驟有限
from sympy.integrals.manualintegrate import manualintegrate
manualintegrate(x**2, x)
# 可以返回一些步驟，但不完整

# SymPy 的 rewrite 系統
expr = sin(x)**2 + cos(x)**2
expr.rewrite(cos)
# 可以重寫表達式，但不是完整推導
```

**評估**：
- **可重現性**: ⭐⭐⭐⭐ (算法確定)
- **自動化程度**: ⭐⭐⭐⭐
- **推導步驟**: ⭐⭐ (有限)
- **適用性**: 廣

**是否符合需求**：
- ✅ 可重現
- ✅ 自動化
- ⚠️ 推導步驟不夠詳細
- ✅ 開源，免費

**可能的解決方案**：
```python
# 擴展 SymPy 的 manualintegrate
from sympy.integrals.manualintegrate import (
    manualintegrate,
    integral_steps
)

# integral_steps 會返回推導樹
steps = integral_steps(x**2, x)
print(steps)
# 這可能是最接近的開源方案
```

#### 3.2 SageMath ⭐⭐⭐

整合多種符號系統（Maxima, SymPy, Singular...），但推導能力類似 SymPy。

#### 3.3 Maxima ⭐⭐⭐

```lisp
/* Maxima 有一些推導追蹤 */
integrate(x^2, x);
/* x^3/3 */

/* 可以設定 trace */
trace(integrate);
integrate(x^2, x);
/* 會顯示內部調用 */
```

**評估**：
- 老牌系統，穩定
- 推導步驟有限
- Lisp 語法（學習曲線）

---

### 類別 4: 專門推導工具

#### 4.1 Symbolab / Wolfram Alpha ⭐⭐⭐⭐

```
Wolfram Alpha:
  Query: "integrate x^2 step by step"
  Output: 完整推導步驟
  
  ✅ 詳細步驟
  ✅ 易用
  ❌ 需要訂閱（Pro）
  ❌ 不能作為 API（有限制）
  ❌ 不能整合到系統
```

**評估**：
- 對人類很好
- 但不適合作為後端引擎

#### 4.2 Sympy.integrals.manualintegrate (開源) ⭐⭐⭐⭐

```python
from sympy import *
from sympy.integrals.manualintegrate import manualintegrate, integral_steps

x = symbols('x')

# 手動積分（返回步驟）
result = manualintegrate(x**2, x)
print(result)  # x**3/3

# 取得推導步驟
steps = integral_steps(x**2, x)
print(steps)

# 輸出類似：
# IntegralInfo(
#   integrand=x**2,
#   variable=x,
#   context=...,
#   parts=[
#     ConstantTimesRule(constant=1, other=x**2, substep=...),
#     PowerRule(base=x, exp=2)
#   ]
# )
```

**這可能是最接近的開源方案！**

**評估**：
- **可重現性**: ⭐⭐⭐⭐⭐
- **自動化程度**: ⭐⭐⭐⭐
- **推導步驟**: ⭐⭐⭐⭐
- **適用性**: 中（主要針對積分）
- **開源**: ✅

---

### 類別 5: Term Rewriting 系統

#### 5.1 egg (Rust) - E-graphs ⭐⭐⭐⭐

```rust
// egg: Equality Saturation
// 用於自動推導和優化

use egg::*;

define_language! {
    enum SimpleLanguage {
        Num(i32),
        "+" = Add([Id; 2]),
        "*" = Mul([Id; 2]),
        Symbol(Symbol),
    }
}

// 定義重寫規則
let rules: &[Rewrite<SimpleLanguage, ()>] = &[
    rewrite!("commute-add"; "(+ ?a ?b)" => "(+ ?b ?a)"),
    rewrite!("commute-mul"; "(* ?a ?b)" => "(* ?b ?a)"),
    rewrite!("add-zero"; "(+ ?a 0)" => "?a"),
    rewrite!("mul-one"; "(* ?a 1)" => "?a"),
    // ... more rules
];

// 應用規則推導
let runner = Runner::default()
    .with_expr(&"(+ x 0)".parse().unwrap())
    .run(rules);

// 結果：x
```

**評估**：
- **可重現性**: ⭐⭐⭐⭐⭐
- **靈活性**: ⭐⭐⭐⭐⭐
- **推導步驟**: ⭐⭐⭐⭐ (可追蹤 e-graph)
- **適用性**: 需要手動定義規則
- **語言**: Rust (有 Python binding)

**非常接近理想！**

#### 5.2 Maude (Rewriting Logic)

```
Maude 也是 term rewriting 系統，類似 egg
但語法更學術化
```

---

## 🎯 最佳方案推薦

### 方案 A: SymPy manualintegrate + 擴展 ⭐⭐⭐⭐

**優點**：
- ✅ 開源、免費
- ✅ Python 生態
- ✅ 已有推導步驟功能
- ✅ 可擴展

**缺點**：
- ⚠️ 主要針對積分（微分較少）
- ⚠️ 需要擴展其他領域

**實作方式**：

```python
from sympy.integrals.manualintegrate import integral_steps
from sympy import *

class DerivationEngine:
    """可重現的推導引擎"""
    
    def integrate_with_steps(self, expr, var):
        """積分並返回完整步驟"""
        steps = integral_steps(expr, var)
        return {
            "result": integrate(expr, var),
            "method": self._extract_method(steps),
            "steps": self._format_steps(steps),
            "traceable": True,
            "reproducible": True
        }
    
    def _format_steps(self, steps):
        """格式化推導步驟為人類可讀"""
        # 遞迴解析 IntegralInfo
        if hasattr(steps, 'parts'):
            return [self._format_step(part) for part in steps.parts]
        return []
    
    def _format_step(self, step):
        """格式化單一步驟"""
        if step.__class__.__name__ == 'PowerRule':
            return f"應用冪次規則: ∫x^{step.exp}dx = x^{step.exp+1}/{step.exp+1}"
        elif step.__class__.__name__ == 'ConstantTimesRule':
            return f"提出常數: {step.constant}"
        # ... more rules
        
# 使用
engine = DerivationEngine()
result = engine.integrate_with_steps(x**2, x)

print(result)
# {
#   "result": x**3/3,
#   "method": "PowerRule",
#   "steps": [
#     "應用冪次規則: ∫x²dx = x³/(2+1)",
#     "簡化: x³/3"
#   ],
#   "reproducible": True
# }
```

**擴展到其他領域**：
```python
# 需要自己實作類似的 manual* 系統
class DerivationEngine:
    def differentiate_with_steps(self, expr, var):
        # 目前 SymPy 沒有 manual_differentiate
        # 需要自己實作規則庫
        pass
    
    def solve_with_steps(self, eq, var):
        # 需要實作代數解步驟
        pass
```

---

### 方案 B: egg (E-graphs) + Python binding ⭐⭐⭐⭐⭐

**優點**：
- ✅ 完全可重現
- ✅ 非常靈活（自定義規則）
- ✅ 效率高（e-graph 算法）
- ✅ 可追蹤推導路徑

**缺點**：
- ❌ 需要手動定義所有規則
- ❌ Rust（有 Python binding 但較新）
- ❌ 學習曲線較陡

**實作方式**：

```python
# 使用 egglog (egg 的 Python binding)
from egglog import *

# 定義語言
@dataclass
class Expr:
    pass

@dataclass
class Const(Expr):
    val: int

@dataclass
class Var(Expr):
    name: str

@dataclass
class Add(Expr):
    a: Expr
    b: Expr

@dataclass
class Mul(Expr):
    a: Expr
    b: Expr

# 定義規則
egraph = EGraph()

# 交換律
egraph.register(rewrite(Add(x, y)).to(Add(y, x)))
egraph.register(rewrite(Mul(x, y)).to(Mul(y, x)))

# 單位元
egraph.register(rewrite(Add(x, Const(0))).to(x))
egraph.register(rewrite(Mul(x, Const(1))).to(x))

# 分配律
egraph.register(rewrite(Mul(x, Add(y, z))).to(Add(Mul(x, y), Mul(x, z))))

# 執行推導
expr = Add(Var("x"), Const(0))
result = egraph.simplify(expr)
# 結果: Var("x")

# 可以追蹤推導路徑
path = egraph.extract_path(expr, result)
print(path)
# ["Apply add-zero rule: (+ x 0) -> x"]
```

**這是最理想的方案，但需要大量前期工作**。

---

### 方案 C: 混合方案（實用）⭐⭐⭐⭐

**結合多種工具**：

```python
class NSForgeEngine:
    """可重現推導引擎"""
    
    def __init__(self):
        # 使用 SymPy 作為後端
        self.sympy_engine = SymPyEngine()
        
        # 自定義規則庫
        self.rules = self._load_rules()
    
    def derive(self, expr, goal, method=None):
        """
        可重現推導
        
        Args:
            expr: 起始表達式
            goal: 目標（"integrate", "differentiate", "solve"）
            method: 可選的方法（確保可重現）
        """
        
        if goal == "integrate":
            # 使用 SymPy manualintegrate
            return self.sympy_engine.integrate_with_steps(expr)
        
        elif goal == "differentiate":
            # 自定義微分推導
            return self._differentiate_with_steps(expr)
        
        elif goal == "solve":
            # 自定義代數求解推導
            return self._solve_with_steps(expr)
    
    def _differentiate_with_steps(self, expr):
        """
        微分推導（自定義實作）
        使用固定規則庫
        """
        steps = []
        
        # 識別表達式類型
        if expr.is_Add:
            steps.append("應用和的微分: (u+v)' = u' + v'")
            # ...
        elif expr.is_Mul:
            steps.append("應用乘積法則: (uv)' = u'v + uv'")
            # ...
        elif expr.is_Pow:
            steps.append(f"應用冪次法則: (x^n)' = n*x^(n-1)")
            # ...
        
        return {
            "result": diff(expr),
            "steps": steps,
            "reproducible": True
        }
```

**評估**：
- ✅ 實用（結合現有工具）
- ✅ 漸進式改進（逐步添加規則）
- ✅ 可重現
- ⚠️ 需要持續開發

---

## 📊 工具對比總結

| 工具 | 可重現性 | 自動化 | 推導步驟 | 開源 | 易用性 | 推薦度 |
|------|---------|--------|---------|------|--------|--------|
| **Lean4** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐ | ⭐⭐⭐ |
| **Mathematica** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **SymPy manual** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **egg (E-graphs)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Wolfram Alpha** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎯 NSForge 的實踐建議

### 短期方案：基於 SymPy manualintegrate

```python
# NSForge 推導引擎 v0.1
from sympy.integrals.manualintegrate import integral_steps
from sympy import *

class NSForgeEngine:
    def derive(self, expr_str, operation):
        """固定的推導引擎"""
        expr = sympify(expr_str)
        
        if operation == "integrate":
            x = symbols('x')
            steps = integral_steps(expr, x)
            return self._format_result(steps)
    
    def _format_result(self, steps):
        return {
            "result": str(integrate(expr, x)),
            "steps": self._extract_steps(steps),
            "method": steps.__class__.__name__,
            "reproducible": True,
            "engine": "SymPy.manualintegrate"
        }
```

**優點**：
- ✅ 立即可用
- ✅ 開源免費
- ✅ Python 生態

**局限**：
- ⚠️ 目前只有積分
- ⚠️ 需要擴展其他操作

### 中期方案：擴展規則庫

逐步添加：
- 微分推導
- 代數求解推導
- 三角恆等式推導
- 極限推導

### 長期方案：考慮 egg (E-graphs)

如果需要更靈活的推導系統。

---

## 💡 回答您的問題

### Q: 有沒有現成的可重現符號推導工具？

**A: 有，但需要組合**

1. **立即可用**：
   - `sympy.integrals.manualintegrate` ✅
   - 提供積分的完整推導步驟
   - 完全可重現

2. **商業方案**：
   - Mathematica/Rubi ✅
   - 非常完整，但昂貴

3. **研究級**：
   - egg (E-graphs) ✅
   - 最靈活，但需要大量開發

### Q: NSForge 應該用哪個？

**推薦：從 SymPy manualintegrate 開始**

```python
# 這就是您需要的「固定引擎」
from sympy.integrals.manualintegrate import integral_steps

# 相同輸入 → 相同輸出（可重現）
steps = integral_steps(x**2, x)

# 返回詳細推導樹
# 不依賴 Agent 思考
# 完全確定性
```

**然後逐步擴展到其他操作**。

---

**Status**: 工具調查完成  
**Recommendation**: 使用 SymPy manualintegrate 作為起點，逐步擴展  
**Key Insight**: 可重現推導 ≠ 需要 AI，規則基系統就可以做到
