# Phase 1 工具快速參考

## 🔥 最常用 (Top 5)

| 工具 | 用途 | 範例 |
|------|------|------|
| **expand_expression** | 展開 | `(x+1)²` → `x²+2x+1` |
| **factor_expression** | 因式分解 | `x²-1` → `(x-1)(x+1)` |
| **apart_expression** | 部分分式 | `1/(x²-1)` → `1/(2(x-1)) - 1/(2(x+1))` |
| **cancel_expression** | 約分 | `(x²-1)/(x-1)` → `x+1` |
| **trigsimp_expression** | 三角化簡 | `sin²+cos²` → `1` |

---

## 📦 完整列表

### P0 - 基礎代數 (7 工具)

```python
# 1. 展開
expand_expression("(x + a)**2")
→ "x**2 + 2*a*x + a**2"

# 2. 因式分解
factor_expression("x**2 - 1")
→ "(x - 1)*(x + 1)"

# 3. 收集同類項
collect_expression("x*y + x - 3 + 2*x**2", "x")
→ "2*x**2 + x*(y + 1) - 3"

# 4. 三角化簡
trigsimp_expression("sin(x)**2 + cos(x)**2")
→ "1"

# 5. 冪次化簡
powsimp_expression("x**2 * x**3")
→ "x**5"

# 6. 根式化簡
radsimp_expression("1/(sqrt(3) + sqrt(2))")
→ "-sqrt(2) + sqrt(3)"

# 7. 組合化簡
combsimp_expression("factorial(n)/factorial(n - 2)")
→ "n*(n - 1)"
```

### P1 - 有理函數 (3 工具)

```python
# 8. 部分分式 (關鍵！)
apart_expression("1/(x**2 - 1)", "x")
→ "1/(2*(x - 1)) - 1/(2*(x + 1))"

# 9. 約分
cancel_expression("(x**2 - 1)/(x - 1)")
→ "x + 1"

# 10. 合併分式
together_expression("1/x + 1/y")
→ "(x + y)/(x*y)"
```

---

## 🩺 藥動學常見場景

### 場景 1：多隔室模型反 Laplace

```python
# 傳遞函數
C_s = "dose * k12 / ((s + λ1) * (s + λ2))"

# 部分分式（必需！）
apart_expression(C_s, "s")
→ "A/(s + λ1) + B/(s + λ2)"

# 反 Laplace 後：
# C(t) = A*exp(-λ1*t) + B*exp(-λ2*t)
```

### 場景 2：Michaelis-Menten 展開

```python
# 展開分子
expand_expression("(V_max*S + V_max*I)/(K_m + S)")
→ "V_max*S/(K_m + S) + V_max*I/(K_m + S)"
```

### 場景 3：清除率合併

```python
# 多清除率相加
together_expression("CL_renal/V + CL_hepatic/V")
→ "(CL_renal + CL_hepatic)/V"
```

### 場景 4：特徵方程求根

```python
# 隔室模型特徵方程
factor_expression("s**2 + (k12 + k21 + k10)*s + k21*k10")
→ "(s + λ1)*(s + λ2)"
# 特徵根：s = -λ1, -λ2
```

---

## 🔧 進階選項

### expand_expression 選項

```python
expand_expression(
    "(x+1)**2", 
    deep=True,           # 遞歸展開
    power_base=True,     # (xy)^n → x^n*y^n
    power_exp=True,      # x^(a+b) → x^a*x^b
    log=True,            # log(xy) → log(x)+log(y)
    multinomial=True     # 多項式展開
)
```

### factor_expression 選項

```python
factor_expression(
    "x**2 - 1",
    deep=False,          # 不遞歸分解
    modulus=None         # 有限域分解
)
```

### trigsimp_expression 選項

```python
trigsimp_expression(
    "sin(x)**2 + cos(x)**2",
    method="matching"    # "matching", "groebner", "combined"
)
```

---

## ⚠️ 常見錯誤

### 錯誤 1：變數未指定

```python
# ❌ 錯誤：apart 需要指定變數（多變數情況）
apart_expression("1/((x-1)*(y-1))")  # 錯誤！

# ✅ 正確
apart_expression("1/((x-1)*(y-1))", "x")  # 正確
```

### 錯誤 2：期望自動反 Laplace

```python
# ❌ apart 只做部分分式，不做反變換
apart_expression("1/(s+1)", "s")
→ "1/(s+1)"  # 不變（已是最簡）

# ✅ 需要手動反 Laplace
# 1/(s+1) → exp(-t)
```

### 錯誤 3：混淆 expand 和 simplify

```python
# simplify 是啟發式（不確定）
simplify("(x+1)**2")  # 可能展開或不展開

# expand 是確定性（一定展開）
expand_expression("(x+1)**2")  # 一定是 x**2+2*x+1
```

---

## 📚 與其他工具配合

### 配合推導追蹤

```python
# Step 1: 展開
result = expand_expression("(x + a)**2")

# Step 2: 記錄到推導
derivation_record_step(
    expression=result["result"],
    description="Expanded (x+a)²",
    notes="Preparing for coefficient extraction"
)
```

### 配合驗證

```python
# 展開
expanded = expand_expression("(x+1)**2")

# 驗證展開正確
symbolic_equal(
    "(x+1)**2",
    expanded["result"]
)  # → True
```

---

## 🎯 選擇指南

| 想要... | 用哪個工具 |
|---------|-----------|
| 展開乘積 | `expand_expression` |
| 因式分解 | `factor_expression` |
| 收集 x 的係數 | `collect_expression` |
| 三角化簡 | `trigsimp_expression` |
| 合併指數 | `powsimp_expression` |
| 根式有理化 | `radsimp_expression` |
| 階乘化簡 | `combsimp_expression` |
| 準備反 Laplace | `apart_expression` ⭐ |
| 約分 | `cancel_expression` |
| 合併分式 | `together_expression` |

---

*Quick Reference Card for Phase 1 Tools*  
*NSForge v0.2.4 (候選)*
