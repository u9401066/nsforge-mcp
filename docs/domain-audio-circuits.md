# Audio Circuit Design - NSForge 領域規劃

> **Domain**: Audio Electronics / Analog Circuit Design  
> **Priority**: ⭐⭐⭐ High (User Interest)  
> **Status**: Planning Phase

---

## 🎵 領域概述

音響電路學涉及模擬信號處理、放大器設計、濾波器設計等。這個領域特別適合推導框架，因為：

1. **基礎原理明確**：歐姆定律、KVL/KCL、轉移函數
2. **修正項豐富**：寄生電容、非理想 Op-amp、負載效應
3. **實用性強**：實際電路總是非理想的

---

## 📐 Principles（基礎原理）

### 1. Ohm's Law
```yaml
principle:
  id: ohms_law
  name: 歐姆定律
  base_form: "V = I * R"
  lean4_reference:
    module: "Mathlib.Physics.Electrical.Ohm"
    theorem: "ohms_law"
  
  variables:
    V: {description: "電壓", unit: "V", type: "real"}
    I: {description: "電流", unit: "A", type: "real"}
    R: {description: "電阻", unit: "Ω", type: "positive_real"}
```

### 2. Kirchhoff's Voltage Law (KVL)
```yaml
principle:
  id: kvl
  name: 克希荷夫電壓定律
  base_form: "Σ(V_i) = 0"  # 迴路電壓和為零
  
  description: |
    沿著閉合迴路，電壓降的代數和為零
```

### 3. Transfer Function (理想)
```yaml
principle:
  id: transfer_function
  name: 轉移函數
  base_form: "H(s) = V_out(s) / V_in(s)"
  
  laplace_domain: true
```

---

## 🔧 Modifications（修正項）

### 1. Parasitic Capacitance（寄生電容）
```yaml
modification:
  id: parasitic_capacitance
  name: 寄生電容
  
  term: "1 / (1 + s*R*C_parasitic)"
  
  description: |
    實際電路中，PCB 走線、元件引腳都會產生寄生電容
    在高頻時影響顯著
  
  typical_values:
    pcb_trace_per_cm: "0.1-1 pF"
    smd_resistor: "0.05-0.5 pF"
    through_hole: "1-5 pF"
  
  when_to_use:
    - "高頻應用 (>100kHz)"
    - "精密電路設計"
```

### 2. Op-Amp Non-Ideal (非理想運算放大器)
```yaml
modification:
  id: opamp_non_ideal
  name: 非理想運算放大器
  
  modifications:
    finite_gain:
      term: "A_ol / (1 + A_ol * beta)"
      description: "有限開迴路增益"
      typical: "A_ol = 10^5 ~ 10^6"
    
    input_bias_current:
      term: "+ I_bias * R"
      description: "輸入偏置電流造成的電壓偏移"
      typical: "1 pA ~ 100 nA"
    
    slew_rate_limit:
      description: "輸出電壓變化率限制"
      typical: "0.5 ~ 50 V/μs"
    
    gbw_product:
      description: "增益頻寬積限制"
      typical: "1 ~ 100 MHz"
```

### 3. Load Effect（負載效應）
```yaml
modification:
  id: load_effect
  name: 負載效應
  
  term: "Z_out || Z_load"
  
  description: |
    輸出阻抗與負載阻抗並聯
    影響實際輸出電壓和頻率響應
  
  when_to_use:
    - "低阻抗負載"
    - "長傳輸線"
    - "多級放大器級聯"
```

### 4. Thermal Noise（熱噪聲）
```yaml
modification:
  id: thermal_noise
  name: 熱噪聲 (Johnson-Nyquist)
  
  term: "sqrt(4 * k_B * T * R * BW)"
  
  variables:
    k_B: {value: "1.38e-23", unit: "J/K", description: "波茲曼常數"}
    T: {unit: "K", description: "絕對溫度"}
    R: {unit: "Ω", description: "電阻值"}
    BW: {unit: "Hz", description: "頻寬"}
  
  typical_scenario: "低噪聲前級設計"
```

---

## 🎯 Derived Forms（常見電路）

### 1. RC Low-Pass Filter (實際)
```yaml
derived_form:
  id: rc_lowpass_with_parasitics
  name: RC 低通濾波器（考慮寄生效應）
  
  based_on:
    principle: transfer_function
    modifications: [parasitic_capacitance, load_effect]
  
  ideal_form: "H(s) = 1 / (1 + s*R*C)"
  
  with_parasitics:
    equation: |
      H(s) = 1 / (1 + s*R*(C + C_parasitic))
    
    effect: |
      - 實際截止頻率降低
      - f_c_actual < f_c_ideal
```

### 2. Inverting Amplifier (非理想 Op-amp)
```yaml
derived_form:
  id: inverting_amp_non_ideal
  name: 反相放大器（非理想）
  
  based_on:
    principle: opamp_inverting
    modifications: [opamp_non_ideal, load_effect]
  
  ideal_gain: "- R_f / R_in"
  
  actual_gain: |
    G = - (R_f / R_in) * (A_ol / (1 + A_ol * (1 + R_f/R_in)))
  
  frequency_response: |
    f_3dB = GBW / (1 + R_f/R_in)
```

### 3. Sallen-Key Filter (Active Filter)
```yaml
derived_form:
  id: sallen_key_lowpass
  name: Sallen-Key 低通濾波器
  
  topology: "二階主動濾波器"
  
  transfer_function: |
    H(s) = K / (s² + s*(ω₀/Q) + ω₀²)
  
  parameters:
    omega_0: "sqrt(1/(R1*R2*C1*C2))"
    Q: "sqrt(R1*R2*C1*C2) / (R2*C1 + R1*C1*(1-K) + R2*C2)"
    K: "1 + R_f/R_in"  # Op-amp gain
  
  modifications_to_consider:
    - opamp_gbw_product: "限制高頻性能"
    - component_tolerance: "影響 Q 值和共振頻率"
```

---

## 🧪 應用場景範例

### 場景 1：設計麥克風前級放大器

**問題**：
> "設計一個麥克風前級，增益 60dB，輸入阻抗 2kΩ，噪聲要低"

**推導流程**：
1. **選擇拓撲**：非反相放大器（高輸入阻抗）
2. **基礎計算**：
   - 增益 60dB = 1000 倍
   - G = 1 + R_f/R_in = 1000
3. **應用修正**：
   - `thermal_noise`：計算電阻產生的噪聲
   - `opamp_input_noise`：選擇低噪聲 Op-amp
   - `bandwidth_limit`：GBW / G = 實際頻寬
4. **元件選擇**：
   - Op-amp: OPA1612 (低噪聲，GBW=10MHz)
   - R_in = 2kΩ → R_f = 1.998 MΩ

### 場景 2：音響 EQ 設計

**問題**：
> "設計一個 1kHz 的 parametric EQ，可調 ±12dB"

**推導流程**：
1. **選擇拓撲**：Band-pass filter + summing amplifier
2. **基礎參數**：
   - Center frequency: f₀ = 1kHz
   - Q factor: 決定頻寬
3. **應用修正**：
   - `component_tolerance`：實際中心頻率偏移
   - `opamp_gbw`：確保頻率響應平坦

---

## 📚 知識庫結構

```
formulas/audio_circuits/
├── principles/
│   ├── ohms_law.yaml
│   ├── kvl.yaml
│   ├── kcl.yaml
│   ├── transfer_function.yaml
│   └── opamp_golden_rules.yaml
│
├── modifications/
│   ├── parasitic_capacitance.yaml
│   ├── opamp_non_ideal.yaml
│   ├── load_effect.yaml
│   ├── thermal_noise.yaml
│   └── component_tolerance.yaml
│
└── derived_forms/
    ├── filters/
    │   ├── rc_lowpass.yaml
    │   ├── sallen_key.yaml
    │   └── state_variable_filter.yaml
    ├── amplifiers/
    │   ├── inverting_amp.yaml
    │   ├── non_inverting_amp.yaml
    │   └── instrumentation_amp.yaml
    └── oscillators/
        ├── wien_bridge.yaml
        └── phase_shift.yaml
```

---

## 🎓 學習路徑

### 初級：基礎濾波器
1. RC passive filters
2. 理想 Op-amp 電路
3. 一階系統分析

### 中級：主動電路
1. 多級放大器
2. 二階濾波器 (Sallen-Key, MFB)
3. 非理想效應修正

### 高級：專業設計
1. 低噪聲設計
2. 高頻補償
3. 穩定性分析

---

## 🔗 相關資源

- **教材**：《The Art of Electronics》 - Horowitz & Hill
- **工具**：LTSpice, Falstad Circuit Simulator
- **Package**：lcapy (Python symbolic circuit analysis)

---

## 📝 實作優先順序

1. ✅ RC 低通濾波器（已有範例）
2. [ ] 反相放大器（考慮非理想 Op-amp）
3. [ ] Sallen-Key 濾波器
4. [ ] 麥克風前級完整設計範例

---

**Status**: 2026-01-01 - Domain planning completed  
**Next**: Implement first principle + modification example
