# NSForge 公式獲取 API 完整指南

## 概述

NSForge 提供多個層級的公式獲取 API，分為三個主要部分：

1. **Domain Layer** - 核心公式接口和服務
2. **Infrastructure Layer** - 實際的公式存儲和檢索實現
3. **MCP Tools Layer** - 面向用戶的推導和計算工具

---

## 1. Domain Layer - 核心接口

位置: `src/nsforge/domain/`

### 1.1 FormulaRepository 抽象接口

**文件**: `src/nsforge/domain/services.py`

```python
class FormulaRepository(ABC):
    """公式知識庫的抽象接口"""
    
    @abstractmethod
    def find_formula(
        self, 
        name: str, 
        domain: str | None = None
    ) -> dict[str, Any] | None:
        """根據名稱查找公式"""
        ...
    
    @abstractmethod
    def list_formulas(
        self, 
        domain: str | None = None, 
        tags: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """列出所有可用公式"""
        ...
    
    @abstractmethod
    def get_derivation(
        self, 
        formula_name: str
    ) -> Derivation | None:
        """獲取公式的完整推導過程"""
        ...
```

**方法詳細說明**:

| 方法 | 參數 | 返回值 | 說明 |
|------|------|--------|------|
| `find_formula` | name, domain | dict 或 None | 精確查找單個公式 |
| `list_formulas` | domain, tags | 字典列表 | 篩選查詢多個公式 |
| `get_derivation` | formula_name | Derivation 或 None | 獲取公式的完整推導過程 |

### 1.2 Formula 標準實體

**文件**: `src/nsforge/domain/formula.py`

```python
@dataclass
class Formula:
    """標準公式介面 - 統一表示所有格式的公式"""
    
    # 核心內容
    id: str                              # 公式 ID
    expression: sp.Expr | sp.Equality   # SymPy 表達式
    variables: dict[str, Variable]      # 公式中的變數
    
    # 來源追蹤（學術溯源）
    source: FormulaSource               # 來源標記
    source_detail: str                  # 詳細來源資訊
    original_input: str                 # 原始輸入字串
    input_format: FormulaFormat         # 輸入格式
    
    # 元資料
    name: str                           # 公式名稱
    description: str                    # 描述
    category: str                       # 分類
    tags: list[str]                     # 標籤
    references: list[str]               # 參考文獻
    created_at: str                     # 創建時間
    
    # 重要屬性
    @property
    def sympy_str(self) -> str:
        """SymPy 字串表示"""
    
    @property
    def latex(self) -> str:
        """LaTeX 表示"""
    
    @property
    def symbol_names(self) -> set[str]:
        """所有符號名稱"""
    
    def to_dict(self) -> dict[str, Any]:
        """序列化為字典"""
```

#### 公式來源標記 (FormulaSource)

```python
class FormulaSource(Enum):
    USER_INPUT = "user_input"      # 用戶直接輸入
    TEXTBOOK = "textbook"          # 教科書公式
    SYMPY_BUILTIN = "sympy_builtin"  # SymPy 內建
    DERIVED = "derived"            # NSForge 推導產生
    EXTERNAL_MCP = "external_mcp"  # 來自其他 MCP（如 sympy-mcp）
```

#### 支援的輸入格式 (FormulaFormat)

```python
class FormulaFormat(Enum):
    SYMPY = "sympy"        # SymPy 字串: "C_0 * exp(-k*t)"
    LATEX = "latex"        # LaTeX: "C_0 e^{-kt}"
    PYTHON = "python"      # Python 表達式: "C_0 * math.exp(-k*t)"
    NATURAL = "natural"    # 自然語言（未來支援）
    DICT = "dict"          # 字典格式
```

### 1.3 FormulaParser - 多格式解析

**文件**: `src/nsforge/domain/formula.py`

```python
class FormulaParser:
    """多格式公式解析器"""
    
    @classmethod
    def parse(
        cls,
        input_data: str | dict[str, Any],
        formula_id: str,
        source: FormulaSource = FormulaSource.USER_INPUT,
        source_detail: str = "",
        **metadata: Any,
    ) -> Formula | ParseError:
        """
        解析公式輸入，自動檢測格式
        
        支援格式:
        - SymPy: "C_0 * exp(-k*t)"
        - LaTeX: "C_0 e^{-kt}"
        - 字典: {"expression": "...", "variables": {...}}
        """
```

---

## 2. Infrastructure Layer - 實現層

位置: `src/nsforge/infrastructure/`

### 2.1 DerivationRepository - 推導存儲

**文件**: `src/nsforge/infrastructure/derivation_repository.py`

```python
class DerivationRepository:
    """管理公式推導的持久化存儲"""
    
    def __init__(self, formulas_dir: Path | None = None):
        """初始化推導存儲
        
        Args:
            formulas_dir: 存儲公式的目錄（預設: ./formulas）
        """
    
    def get_repository(
        formulas_dir: Path | None = None
    ) -> DerivationRepository:
        """獲取全域儲存庫實例"""
```

**關鍵資料結構**:

```python
@dataclass
class DerivationResult:
    """推導結果 - 可序列化格式"""
    id: str
    name: str
    description: str
    author: str
    final_expression: str
    derivation_steps: list[DerivationStep]
    formulas_used: list[str]  # 基礎公式列表
    created_at: str
    completed_at: str
    tags: list[str]
    references: list[str]
```

### 2.2 ScipyConstantsAdapter - 物理常數

**文件**: `src/nsforge/infrastructure/adapters/scipy_constants.py`

提供對 CODATA 2018 物理常數的訪問。

```python
class ScipyConstantsAdapter(BaseAdapter):
    """SciPy 物理常數的適配器"""
    
    def list_formulas(self, category: str | None = None) -> list[str]:
        """列出常數（作為公式處理）
        
        Args:
            category: 分類（如 "fundamental", "electromagnetic", "atomic"）
        
        Returns:
            常數 ID 列表
        """
    
    def get_formula(self, formula_id: str) -> FormulaInfo | None:
        """獲取單個常數
        
        Args:
            formula_id: 常數 ID（如 "speed_of_light"）
        
        Returns:
            FormulaInfo 物件或 None
        """
    
    def search(self, query: str) -> list[FormulaInfo]:
        """搜尋常數
        
        Args:
            query: 搜尋關鍵字
        
        Returns:
            匹配的常數列表
        """
```

**可用常數分類**:

| 分類 | 常數示例 | API ID |
|------|---------|--------|
| fundamental | 光速、普朗克常數、引力常數 | `speed_of_light`, `planck`, `gravitational_constant` |
| electromagnetic | 基本電荷、真空電容率、真空磁導率 | `elementary_charge`, `epsilon_0`, `mu_0` |
| atomic | 電子質量、質子質量、玻爾半徑 | `electron_mass`, `proton_mass`, `bohr_radius` |
| conversion | eV、卡路里、大氣壓、埃 | `electron_volt`, `calorie`, `atmosphere` |

---

## 3. MCP Tools Layer - 用戶接口

位置: `src/nsforge_mcp/tools/`

### 3.1 推導會話相關 API

**文件**: `src/nsforge_mcp/tools/derivation.py`

#### 會話管理

```
derivation_start(name, description, author)
│
├─ 啟動新的推導會話
├─ 返回 session_id
└─ 自動持久化

derivation_resume(session_id)
│
├─ 恢復暫停的會話
├─ 會話狀態（步驟數、公式數、當前表達式）
└─ 繼續工作

derivation_list_sessions()
│
├─ 列出所有推導會話
├─ 包含會話 ID、名稱、狀態、進度
└─ 用於選擇恢復的會話

derivation_status()
│
├─ 查詢當前活躍會話的狀態
├─ 步驟數、公式、當前表達式
└─ 操作可用性檢查

derivation_abort()
└─ 中止當前會話
```

#### 公式載入

```
derivation_load_formula(formula_input, formula_id, **metadata)
│
├─ 輸入格式：SymPy、LaTeX、字典
├─ 自動格式檢測
├─ 變數自動提取
└─ 返回解析結果

用法示例：
derivation_load_formula("C_0 * exp(-k*t)", formula_id="one_compartment")
derivation_load_formula("\\frac{dC}{dt} = -k \\cdot C")
derivation_load_formula({
    "expression": "E = mc^2",
    "variables": {
        "E": {"description": "能量", "unit": "J"},
        "m": {"description": "質量", "unit": "kg"},
        "c": {"description": "光速", "unit": "m/s"}
    }
})
```

#### 推導操作

```
derivation_substitute(substitutions)
│
├─ 代入數值或其他表達式
├─ 支援多個同時代入
└─ 自動步驟記錄

derivation_simplify(strategy)
│
├─ 化簡當前表達式
├─ 策略選項：standard, rational, trigonometric, full
└─ 返回化簡後表達式

derivation_solve_for(variable, hints)
│
├─ 解指定變數
├─ 支援提供求解提示
└─ 返回所有解

derivation_differentiate(variable, order)
│
├─ 對變數求導
├─ 支援高階導數
└─ 自動符號簡化

derivation_integrate(variable, lower, upper)
│
├─ 不定積分或定積分
├─ 支援複雜被積函數
└─ 符號結果
```

#### 步驟管理

```
derivation_record_step(expression, description, notes)
│
├─ 手動記錄推導步驟
├─ 包含表達式、描述、備註
├─ 用於非自動推導
└─ 支援知識註解

derivation_add_note(note, note_type)
│
├─ 為當前步驟添加附加信息
├─ 類型：explanation, correction, reference, insight
└─ 幫助理解推導邏輯

derivation_get_steps()
│
├─ 獲取所有推導步驟
├─ 包含各步表達式和註解
└─ 用於審查

derivation_get_step(step_number)
│
├─ 獲取特定步驟細節
└─ 包含所有元資料

derivation_update_step(step_number, updates)
│
├─ 修改已記錄的步驟
├─ 支援部分更新
└─ 保留歷史

derivation_delete_step(step_number)
│
├─ 刪除步驟並自動重新排序
└─ 影響後續推導

derivation_rollback(to_step)
│
├─ 回滾到指定步驟
├─ 清除後續操作
└─ 用於嘗試不同路徑

derivation_insert_note(step_number, note, note_type)
└─ 為過去的步驟添加註解
```

#### 完成與儲存

```
derivation_complete(tags, references)
│
├─ 完成推導會話
├─ 添加元資料標籤和參考
├─ 自動序列化和存儲
└─ 返回完成的推導 ID

derivation_list_saved(limit, offset)
│
├─ 列出已保存的推導
├─ 支援分頁
└─ 包含簡略資訊

derivation_get_saved(result_id)
│
├─ 獲取完整的已保存推導
└─ 包含所有步驟和元資料

derivation_search_saved(query, field)
│
├─ 搜尋已保存推導
├─ 支援按名稱、描述、標籤搜尋
└─ 返回匹配推導列表

derivation_update_saved(result_id, updates)
│
├─ 更新已保存推導的元資料
└─ 不更改推導內容

derivation_delete_saved(result_id)
└─ 刪除已保存推導

derivation_repository_stats()
└─ 統計儲存庫信息
```

#### Handoff 機制（與 SymPy-MCP 互操作）

```
derivation_export_for_sympy()
│
├─ 導出當前狀態給 SymPy-MCP
├─ 返回初始化命令和表達式
└─ 用於無法處理的複雜運算

derivation_import_from_sympy(expression, operation, sympy_tool, notes, assumptions, limitations)
│
├─ 從 SymPy-MCP 導入計算結果
├─ 記錄操作類型和工具
├─ 包含假設和限制
└─ 繼續推導

derivation_handoff_status()
└─ 查看工作流程和能力邊界
```

### 3.2 計算和公式管理 API

**文件**: `src/nsforge_mcp/tools/calculate.py`

NSForge 特有的計算工具（SymPy-MCP 沒有的功能）：

```
極限計算
├─ calculate_limit(expression, variable, point, direction)
│  └─ 計算極限（包括 ±∞）
│
級數展開
├─ calculate_series(expression, variable, point, n_terms, series_type)
│  └─ Taylor、Laurent、Fourier 級數展開
│
求和
├─ calculate_summation(expression, variable, lower, upper, simplify)
│  └─ 符號求和（有限和無限）
│
不等式求解
├─ solve_inequality(inequality, variable)
│  └─ 單個不等式求解
│
不等式系統
├─ solve_inequality_system(inequalities, variables)
│  └─ 不等式組求解
│
概率分佈
├─ define_distribution(dist_type, params, var_name)
│  └─ 定義概率分佈
│  │  支援: normal, exponential, uniform, binomial, poisson
│  │
├─ distribution_stats(distribution)
│  └─ 計算均值、方差、標準差
│  │
└─ distribution_probability(distribution, condition)
   └─ 計算概率 P(X < a)、P(a < X < b)
│
假設系統
├─ query_assumptions(symbol, assumption_type)
│  └─ 查詢符號屬性（positive, real, integer 等）
│  │
└─ refine_expression(expression, assumptions)
   └─ 使用假設簡化表達式
│
基本工具
├─ evaluate_numeric(expression, substitutions, precision)
│  └─ 數值計算評估
│
└─ symbolic_equal(expr1, expr2)
   └─ 符號等價性檢查
```

### 3.3 程式碼生成 API

**文件**: `src/nsforge_mcp/tools/codegen.py`

```
程式碼生成
├─ generate_python_function(expression, variables, function_name)
│  └─ 從公式生成 Python 函數
│
├─ generate_cpp_function(expression, variables, function_name)
│  └─ 生成 C++ 程式碼
│
├─ generate_latex_report(derivation_id)
│  └─ 生成 LaTeX 報告文件
│
└─ generate_markdown_report(derivation_id)
   └─ 生成 Markdown 文件
```

### 3.4 表達式工具 API

**文件**: `src/nsforge_mcp/tools/expression.py`

```
表達式操作
├─ introduce_expression(expression, variable_name, value)
│  └─ 引入新的表達式
│
├─ substitute_expression(expression, substitutions)
│  └─ 進行代入
│
└─ print_latex_expression(expression)
   └─ 打印 LaTeX 形式供用戶確認
```

### 3.5 驗證 API

**文件**: `src/nsforge_mcp/tools/verify.py`

```
驗證工具
├─ verify_step(step_input, step_output, operation)
│  └─ 驗證單個推導步驟
│
├─ verify_derivation(derivation_id)
│  └─ 驗證完整推導過程
│
├─ check_dimensions(expression, expected_dimension)
│  └─ 檢查量綱一致性
│
├─ check_units(expression)
│  └─ 檢查單位一致性
│
└─ symbolic_equal(expr1, expr2)
   └─ 符號等價性驗證
```

---

## 4. 快速參考表

### 按用途分類的 API

| 用途 | API | 位置 |
|------|-----|------|
| **基本公式查詢** | | |
| 查找公式 | `FormulaRepository.find_formula()` | Domain |
| 列出所有公式 | `FormulaRepository.list_formulas()` | Domain |
| 獲取推導 | `FormulaRepository.get_derivation()` | Domain |
| **物理常數** | | |
| 列出常數 | `ScipyConstantsAdapter.list_formulas()` | Infrastructure |
| 獲取常數 | `ScipyConstantsAdapter.get_formula()` | Infrastructure |
| 搜尋常數 | `ScipyConstantsAdapter.search()` | Infrastructure |
| **推導操作** | | |
| 啟動會話 | `derivation_start()` | MCP Tools |
| 載入公式 | `derivation_load_formula()` | MCP Tools |
| 執行推導 | `derivation_*` (substitute, simplify, solve...) | MCP Tools |
| 保存推導 | `derivation_complete()` | MCP Tools |
| **高級計算** | | |
| 極限 | `calculate_limit()` | MCP Tools |
| 級數 | `calculate_series()` | MCP Tools |
| 求和 | `calculate_summation()` | MCP Tools |
| 不等式 | `solve_inequality()` | MCP Tools |
| **程式碼生成** | | |
| Python 程式碼 | `generate_python_function()` | MCP Tools |
| LaTeX 報告 | `generate_latex_report()` | MCP Tools |

### 常見工作流程

#### 1. 查詢已存在的公式

```
FormulaRepository.find_formula("Arrhenius")
  ↓
Formula 物件或 None
  ↓
Formula.to_dict() → JSON 序列化
```

#### 2. 推導新公式

```
derivation_start()
  ↓ 
derivation_load_formula()
  ↓
derivation_substitute() → derivation_simplify() → ...
  ↓
derivation_record_step() [重複多次]
  ↓
derivation_complete()
  ↓
DerivationResult 已保存
```

#### 3. 處理複雜計算

```
derivation_start()
  ↓
derivation_load_formula()
  ↓
derivation_export_for_sympy()
  ↓
[SymPy-MCP 計算]
  ↓
derivation_import_from_sympy()
  ↓
derivation_complete()
```

---

## 5. 數據序列化格式

### Formula.to_dict()

```json
{
  "id": "formula_123",
  "expression": "C_0 * exp(-k*t)",
  "latex": "C_{0} e^{- k t}",
  "variables": {
    "C_0": {
      "name": "C_0",
      "description": "初始濃度",
      "unit": "mg/L",
      "constraints": "positive",
      "value": null
    },
    "k": {
      "name": "k",
      "description": "消除速率常數",
      "unit": "1/h",
      "constraints": "positive",
      "value": null
    }
  },
  "source": "derived",
  "source_detail": "NSForge derivation session",
  "original_input": "C_0 * exp(-k*t)",
  "input_format": "sympy",
  "name": "一房室動力學",
  "description": "藥物一房室開放模型",
  "category": "pharmacokinetics",
  "tags": ["exponential", "decay"],
  "references": ["Gibaldi & Perrier (1982)"],
  "created_at": "2025-01-04T14:50:28Z"
}
```

### DerivationResult

```json
{
  "id": "deriv_abc123",
  "name": "溫度修正消除率",
  "description": "推導溫度修正的消除速率常數公式",
  "author": "User Name",
  "final_expression": "k_corrected = k_0 * exp((E_a/R) * (1/T_ref - 1/T))",
  "derivation_steps": [
    {
      "step_number": 1,
      "expression": "k = A * exp(-E_a / (R*T))",
      "description": "Arrhenius 方程",
      "operation": "load_formula",
      "timestamp": "2025-01-04T14:50:28Z"
    },
    {
      "step_number": 2,
      "expression": "k_ref / k = exp(E_a/R * (1/T - 1/T_ref))",
      "description": "兩溫度下的比率",
      "operation": "divide",
      "timestamp": "2025-01-04T14:50:35Z"
    }
  ],
  "formulas_used": ["Arrhenius equation"],
  "created_at": "2025-01-04T14:50:28Z",
  "completed_at": "2025-01-04T14:52:15Z",
  "tags": ["Arrhenius", "temperature", "kinetics"],
  "references": ["Journal of Chemical Engineering"]
}
```

---

## 6. 錯誤處理

### ParseError

```python
@dataclass
class ParseError:
    error_type: str          # "syntax", "latex", "variable", "dimension"
    message: str             # 詳細錯誤信息
    position: int | None     # 錯誤位置
    suggestion: str | None   # 修復建議
    original_input: str      # 原始輸入
    
    def to_dict(self) -> dict[str, Any]:
        """轉換為字典用於 API 響應"""
```

**常見錯誤類型**:

| 類型 | 原因 | 建議 |
|------|------|------|
| syntax | SymPy 語法錯誤 | 檢查運算符使用，使用 * 乘法、** 乘方 |
| latex | LaTeX 語法錯誤 | 檢查括號匹配、使用 \frac{a}{b} |
| variable | 變數命名問題 | 避免使用 Python 保留詞 |
| dimension | 量綱不一致 | 檢查各項單位 |

---

## 7. 完整示例

### 例 1: 查詢物理常數

```python
from nsforge.infrastructure.adapters.scipy_constants import ScipyConstantsAdapter

adapter = ScipyConstantsAdapter()

# 列出所有基礎常數
constants = adapter.list_formulas(category="fundamental")
# 返回: ["speed_of_light", "planck", "gravitational_constant", ...]

# 獲取光速
c_info = adapter.get_formula("speed_of_light")
print(c_info.variables["c"]["value"])  # 299792458.0

# 搜尋相關常數
results = adapter.search("electron")
# 返回包含 "electron" 的所有常數
```

### 例 2: 推導新公式

```python
# 使用 MCP 工具（推薦的用戶面向方式）

# 1. 啟動推導會話
session = derivation_start(
    name="drug_elimination",
    description="推導溫度修正的消除速率"
)
session_id = session["session_id"]

# 2. 載入 Arrhenius 方程
derivation_load_formula(
    "k = A * exp(-E_a / (R*T))",
    formula_id="arrhenius",
    name="Arrhenius 方程",
    category="kinetics"
)

# 3. 代入參考溫度
derivation_substitute({
    "T": "T_ref"
})

# 4. 推導比率
derivation_record_step(
    "k_ref = A * exp(-E_a / (R*T_ref))",
    "參考溫度下的速率常數"
)

# 5. 簡化
derivation_simplify("standard")

# 6. 完成推導
result = derivation_complete(
    tags=["Arrhenius", "kinetics"],
    references=["Gibaldi & Perrier (1982)"]
)
```

### 例 3: 多格式公式解析

```python
from nsforge.domain.formula import FormulaParser, FormulaSource

# SymPy 格式
formula1 = FormulaParser.parse(
    "E = m * c**2",
    formula_id="einstein_mass_energy",
    source=FormulaSource.TEXTBOOK,
    name="質能轉換公式"
)

# LaTeX 格式
formula2 = FormulaParser.parse(
    "E = m c^2",  # 自動檢測為 LaTeX
    formula_id="einstein_mass_energy_latex"
)

# 字典格式
formula3 = FormulaParser.parse({
    "expression": "E = m * c**2",
    "variables": {
        "E": {"description": "能量", "unit": "J"},
        "m": {"description": "質量", "unit": "kg"},
        "c": {"description": "光速", "unit": "m/s", "value": 299792458}
    },
    "name": "質能轉換"
}, formula_id="einstein_comprehensive")

# 轉換為字典用於序列化
print(formula1.to_dict())
```

---

## 8. 相關文件

- **架構**: `ARCHITECTURE.md`
- **數學黃金法則**: `memory-bank/` 目錄
- **Skills 指南**: `docs/nsforge-skills-guide.md`
- **Python 環境**: `.github/bylaws/python-environment.md`
- **DDD 架構**: `.github/bylaws/ddd-architecture.md`
