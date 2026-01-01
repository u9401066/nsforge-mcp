# 推導模板系統設計文檔

## 1. 核心理念

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  模板 ≠ 答案                                                                │
│  模板 = 推導的「骨架」+ 「提示」                                            │
│                                                                             │
│  • Agent 負責：選擇模板、填入參數、與 User 討論                             │
│  • 模板提供：推導步驟、需要的公式、參數檢查清單                             │
│  • sympy-mcp 負責：精確執行每一步符號運算                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 模板格式設計 (YAML)

### 2.1 基本結構

```yaml
# template_schema.yaml
template:
  id: string           # 唯一識別碼
  name: string         # 人類可讀名稱
  domain: string       # 領域：mechanics, circuits, pharmacokinetics, etc.
  tags: [string]       # 標籤，用於搜尋
  description: string  # 描述這個模板解決什麼問題
  
  # 參數定義
  parameters:
    required:          # 必要參數
      - name: string
        symbol: string
        type: string   # positive_real, real, integer, etc.
        unit: string   # SI 單位
        description: string
    optional:          # 可選參數（有預設值）
      - name: string
        symbol: string
        default: value
        unit: string
        description: string
  
  # 推導步驟
  steps:
    - id: number
      name: string
      description: string
      action: string   # solve, substitute, simplify, integrate, etc.
      
      # 這一步的輸入輸出
      inputs: [symbol]
      outputs: [symbol]
      
      # 提示 Agent 用什麼公式/方法
      hint:
        formula: string        # 公式名稱或表達式
        sympy_mcp_tool: string # 建議使用的 sympy-mcp 工具
        explanation: string    # 解釋這一步在做什麼
      
      # 驗證條件
      verification:
        dimension_check: boolean
        expected_form: string   # 預期結果的形式
  
  # 最終輸出
  outputs:
    - symbol: string
      name: string
      unit: string
      description: string
  
  # 程式碼生成模板
  code_template:
    python: string     # Jinja2 模板
    docstring: string
```

### 2.2 完整範例：安全帶張力分析

```yaml
template:
  id: seatbelt_tension_analysis
  name: "安全帶張力分析"
  domain: mechanics
  tags: [collision, safety, spring, energy_conservation]
  description: |
    分析車輛碰撞時安全帶的最大張力。
    結合動量守恆（碰撞）和能量守恆（安全帶伸長）。
  
  parameters:
    required:
      - name: vehicle_1_mass
        symbol: M1
        type: positive_real
        unit: kg
        description: 車輛 1 的質量
      
      - name: vehicle_2_mass
        symbol: M2
        type: positive_real
        unit: kg
        description: 車輛 2 的質量（被撞車輛，初始靜止）
      
      - name: initial_velocity
        symbol: v
        type: positive_real
        unit: m/s
        description: 車輛 1 的初始速度
      
      - name: person_mass
        symbol: m
        type: positive_real
        unit: kg
        description: 乘客質量
      
      - name: seatbelt_spring_constant
        symbol: k
        type: positive_real
        unit: N/m
        description: 安全帶的等效彈簧係數
    
    optional:
      - name: safety_factor
        symbol: SF
        type: positive_real
        default: 3.0
        description: 材料設計的安全係數
      
      - name: collision_angle
        symbol: theta
        type: real
        default: 0
        unit: rad
        description: 碰撞角度（0 = 正向碰撞）
  
  # 推導前的檢查
  preconditions:
    - check: "M2 > 0"
      message: "車輛 2 必須有質量（非零）"
    - check: "v > 0"
      message: "初始速度必須為正"
    - check: "k > 0"
      message: "彈簧係數必須為正"
  
  steps:
    - id: 1
      name: momentum_conservation
      description: 使用動量守恆計算碰撞後速度
      action: solve
      inputs: [M1, M2, v]
      outputs: [v_f]
      hint:
        formula: "M1 * v = (M1 + M2) * v_f"
        sympy_mcp_tool: solve_algebraically
        explanation: |
          假設完全非彈性碰撞（兩車黏在一起），
          碰撞前總動量 = 碰撞後總動量
      verification:
        dimension_check: true
        expected_form: "M1 * v / (M1 + M2)"
    
    - id: 2
      name: velocity_change
      description: 計算乘客的速度變化量
      action: substitute
      inputs: [v, v_f]
      outputs: [Delta_v]
      hint:
        formula: "Delta_v = v - v_f"
        sympy_mcp_tool: substitute_expression
        explanation: |
          乘客相對於車輛的速度變化
          這是安全帶需要吸收的速度
      verification:
        dimension_check: true
        expected_form: "M2 * v / (M1 + M2)"
    
    - id: 3
      name: energy_conservation
      description: 使用能量守恆計算安全帶伸長量
      action: solve
      inputs: [Delta_v, m, k]
      outputs: [x]
      hint:
        formula: "(1/2) * m * Delta_v**2 = (1/2) * k * x**2"
        sympy_mcp_tool: solve_algebraically
        explanation: |
          乘客的動能 = 安全帶的彈性位能
          (1/2)mΔv² = (1/2)kx²
      verification:
        dimension_check: true
        expected_form: "Delta_v * sqrt(m / k)"
    
    - id: 4
      name: max_tension
      description: 計算安全帶最大張力
      action: substitute
      inputs: [k, x]
      outputs: [T_max]
      hint:
        formula: "T_max = k * x"
        sympy_mcp_tool: substitute_expression
        explanation: |
          彈簧力 F = kx
          在最大伸長時，張力最大
      verification:
        dimension_check: true
        expected_form: "Delta_v * sqrt(m * k)"
    
    - id: 5
      name: material_requirement
      description: 計算材料強度要求
      action: multiply
      inputs: [T_max, SF]
      outputs: [sigma_required]
      hint:
        formula: "sigma_required = T_max * SF"
        explanation: |
          工程設計需要考慮安全係數
          SF = 2.0 (一般), 3.0 (安全關鍵), 4.0 (航空)
      verification:
        dimension_check: true
  
  outputs:
    - symbol: v_f
      name: 碰撞後速度
      unit: m/s
      description: 碰撞後兩車共同速度
    
    - symbol: Delta_v
      name: 速度變化量
      unit: m/s
      description: 乘客相對速度變化
    
    - symbol: x
      name: 安全帶伸長量
      unit: m
      description: 安全帶最大伸長
    
    - symbol: T_max
      name: 最大張力
      unit: N
      description: 安全帶承受的最大張力
    
    - symbol: sigma_required
      name: 材料強度要求
      unit: N
      description: 考慮安全係數後的強度要求
  
  # 最終公式（供驗證用）
  final_formulas:
    T_max: "M2 * v * sqrt(m * k) / (M1 + M2)"
    T_max_with_angle: "M2 * v * cos(theta) * sqrt(m * k) / (M1 + M2)"
  
  # 程式碼生成模板
  code_template:
    python: |
      def calculate_seatbelt_tension(
          M1: float,  # {{ parameters.M1.description }} [{{ parameters.M1.unit }}]
          M2: float,  # {{ parameters.M2.description }} [{{ parameters.M2.unit }}]
          v: float,   # {{ parameters.v.description }} [{{ parameters.v.unit }}]
          m: float,   # {{ parameters.m.description }} [{{ parameters.m.unit }}]
          k: float,   # {{ parameters.k.description }} [{{ parameters.k.unit }}]
          SF: float = {{ parameters.SF.default }},  # {{ parameters.SF.description }}
      ) -> dict:
          """
          {{ template.description }}
          
          Auto-generated by NSForge from template: {{ template.id }}
          """
          import math
          
          # Step 1: {{ steps[0].description }}
          v_f = M1 * v / (M1 + M2)
          
          # Step 2: {{ steps[1].description }}
          delta_v = v - v_f
          
          # Step 3: {{ steps[2].description }}
          x = delta_v * math.sqrt(m / k)
          
          # Step 4: {{ steps[3].description }}
          T_max = k * x
          
          # Step 5: {{ steps[4].description }}
          sigma_required = T_max * SF
          
          return {
              "v_f": v_f,
              "delta_v": delta_v,
              "x": x,
              "T_max": T_max,
              "sigma_required": sigma_required,
          }
  
  # 相關資源
  references:
    - "動量守恆定律"
    - "能量守恆定律"
    - "彈性力學 - 虎克定律"
  
  # 可能的變體
  variants:
    - id: seatbelt_tension_with_angle
      description: 考慮碰撞角度的版本
      modifications:
        - step: 2
          formula: "Delta_v = (v - v_f) * cos(theta)"
    
    - id: seatbelt_tension_partial_inelastic
      description: 部分非彈性碰撞（考慮能量損失）
      additional_parameters:
        - name: restitution_coefficient
          symbol: e
          type: real
          range: [0, 1]
```

## 3. MCP Tools 設計

### 3.1 模板相關工具

```python
# tools/template.py

@mcp.tool()
def list_templates(
    domain: str | None = None,
    tag: str | None = None,
) -> dict:
    """列出可用的推導模板"""
    pass

@mcp.tool()
def get_template(
    template_id: str,
) -> dict:
    """獲取模板詳細資訊"""
    pass

@mcp.tool()
def check_template_params(
    template_id: str,
    given_params: dict,
) -> dict:
    """檢查參數完整性，返回缺少的參數"""
    pass

@mcp.tool()
def suggest_template(
    problem_description: str,
    domain: str | None = None,
) -> dict:
    """根據問題描述建議合適的模板"""
    pass

@mcp.tool()
def execute_template_step(
    template_id: str,
    step_id: int,
    params: dict,
    previous_results: dict | None = None,
) -> dict:
    """執行模板的單一步驟"""
    pass

@mcp.tool()
def generate_code_from_template(
    template_id: str,
    params: dict,
    language: str = "python",
) -> dict:
    """從模板生成可執行程式碼"""
    pass
```

## 4. 工作流程範例

### User 問題
> "質量 70kg 的人在 1500kg 的車子裡，以 50km/h 撞到靜止的 2000kg 車，
> 安全帶係數 5000 N/m，求最大張力？"

### Agent 工作流程

```
1. Agent 分析問題
   → 識別：碰撞 + 安全帶 + 張力
   
2. 呼叫 suggest_template("碰撞 安全帶 張力", domain="mechanics")
   → 返回：seatbelt_tension_analysis (匹配度 0.95)
   
3. 呼叫 get_template("seatbelt_tension_analysis")
   → 獲取模板詳情、參數列表
   
4. 呼叫 check_template_params(
       template_id="seatbelt_tension_analysis",
       given_params={
           "M1": 1500, "M2": 2000, "v": 13.89,  # 50km/h → m/s
           "m": 70, "k": 5000
       }
   )
   → 返回：complete=True, missing=[]
   
5. 逐步執行（或詢問 User 確認）
   
   5.1 execute_template_step(step_id=1, ...)
       → v_f = 5.95 m/s
       
   5.2 execute_template_step(step_id=2, ...)
       → Delta_v = 7.94 m/s
       
   5.3 execute_template_step(step_id=3, ...)
       → x = 0.94 m
       
   5.4 execute_template_step(step_id=4, ...)
       → T_max = 4700 N
       
   5.5 execute_template_step(step_id=5, ...)
       → sigma_required = 14100 N (SF=3.0)

6. 呼叫 generate_code_from_template(...)
   → 生成可執行的 Python 函數
```

## 5. 模板目錄結構

```
nsforge/
└── templates/
    ├── mechanics/
    │   ├── collision/
    │   │   ├── seatbelt_tension.yaml
    │   │   ├── elastic_collision_1d.yaml
    │   │   └── inelastic_collision_2d.yaml
    │   ├── projectile/
    │   │   ├── projectile_motion.yaml
    │   │   └── projectile_with_drag.yaml
    │   └── oscillation/
    │       ├── simple_harmonic.yaml
    │       └── damped_harmonic.yaml
    │
    ├── circuits/
    │   ├── filters/
    │   │   ├── rc_lowpass.yaml
    │   │   ├── rc_highpass.yaml
    │   │   └── rlc_bandpass.yaml
    │   └── amplifiers/
    │       └── opamp_inverting.yaml
    │
    ├── pharmacokinetics/
    │   ├── one_compartment.yaml
    │   ├── two_compartment.yaml
    │   └── michaelis_menten.yaml
    │
    └── thermodynamics/
        ├── carnot_cycle.yaml
        ├── ideal_gas_processes.yaml
        └── heat_engine_efficiency.yaml
```

## 6. 優勢

1. **可復用**：模板可以跨問題復用
2. **可客製**：參數化設計，適應不同情境
3. **可追蹤**：每步有明確的輸入輸出
4. **可驗證**：內建維度檢查和預期結果
5. **可擴展**：社群可以貢獻新模板
6. **與 Agent 協作**：Agent 選擇模板，User 確認參數
