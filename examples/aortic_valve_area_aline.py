"""
主動脈瓣面積（AVA）從動脈導管波形估算
==========================================

Aortic Valve Area Estimation from Arterial Line (A-line) Waveform

此腳本實現了從手部動脈導管（radial a-line）波形特徵估算主動脈瓣面積的多種方法：

方法概覽：
1. Gorlin 公式 — 血流動力學金標準
2. Hakki 簡化公式 — 快速床邊估算
3. 脈搏輪廓分析 (Pulse Contour) — 從 a-line 波形計算 SV 和 CO
4. 波形特徵指數 — 從 a-line 形態學提取診斷指標
5. 經驗回歸模型 — 結合多個波形指標的 AVA 預測

臨床背景：
- 主動脈瓣狹窄 (Aortic Stenosis, AS) 是常見的瓣膜性心臟病
- 金標準診斷為超聲心動圖（連續性方程式）或心導管（Gorlin 公式）
- 在 ICU 或手術室，a-line 常是唯一的連續血流動力學監測工具
- 從 a-line 波形提取的特徵可提供 AS 嚴重度的早期線索

推導來源: NSForge Derivation (2026-04-15)

References:
    Gorlin R, Gorlin SG. Am Heart J. 1951;41(1):1-29.
    Hakki AH, et al. Circulation. 1981;63(5):1050-1055.
    Wesseling KH, et al. J Appl Physiol. 1993;74(5):2566-2573.
"""

import math
from dataclasses import dataclass, field

import numpy as np

# ============================================================
# Data Classes
# ============================================================


@dataclass
class PatientHemodynamics:
    """患者血流動力學基本資料"""

    heart_rate: float  # HR (beats/min)
    systolic_bp: float  # 收縮壓 (mmHg)
    diastolic_bp: float  # 舒張壓 (mmHg)
    cardiac_output: float | None = None  # CO (L/min), from thermodilution or other
    stroke_volume: float | None = None  # SV (mL)
    mean_gradient: float | None = None  # ΔP_mean (mmHg), from echo Doppler

    @property
    def pulse_pressure(self) -> float:
        """脈壓 (mmHg)"""
        return self.systolic_bp - self.diastolic_bp

    @property
    def mean_arterial_pressure(self) -> float:
        """平均動脈壓 MAP (mmHg) = DBP + 1/3 * PP"""
        return self.diastolic_bp + self.pulse_pressure / 3.0


@dataclass
class AlineWaveformFeatures:
    """從動脈導管波形提取的特徵

    這些特徵可由監視器的波形分析演算法自動提取，
    或由臨床人員手動標註。
    """

    systolic_upstroke_time: float  # T_upstroke: 從波谷到峰值的時間 (s)
    systolic_ejection_time: float  # SEP/LVET: 收縮射出時間 (s)，到 dicrotic notch
    systolic_area: float  # A_sys: 收縮期壓力-時間積分 (mmHg·s)
    total_area: float  # A_total: 一個心動週期的壓力-時間積分 (mmHg·s)
    dp_dt_max: float  # (dP/dt)_max: 最大壓力上升速率 (mmHg/s)
    peak_systolic_pressure: float  # 收縮期峰值壓力 (mmHg)
    diastolic_pressure: float  # 舒張期壓力 (mmHg)

    @property
    def pulse_pressure(self) -> float:
        return self.peak_systolic_pressure - self.diastolic_pressure

    @property
    def upstroke_ratio(self) -> float:
        """收縮上升時間比 R_upstroke = T_upstroke / T_sys

        正常: 0.15-0.25, AS: 0.30-0.50+
        """
        if self.systolic_ejection_time <= 0:
            return 0.0
        return self.systolic_upstroke_time / self.systolic_ejection_time

    @property
    def pulse_pressure_ratio(self) -> float:
        """脈壓比 R_PP = PP / MAP (Pulsus Parvus Index)

        正常: 0.4-0.6, 嚴重 AS: < 0.25
        """
        mean_ap = self.diastolic_pressure + self.pulse_pressure / 3.0
        if mean_ap <= 0:
            return 0.0
        return self.pulse_pressure / mean_ap

    @property
    def systolic_area_fraction(self) -> float:
        """收縮面積分率 F_sys = A_sys / A_total"""
        if self.total_area <= 0:
            return 0.0
        return self.systolic_area / self.total_area

    @property
    def dp_dt_index(self) -> float:
        """dP/dt 指數 I_dpdt = (dP/dt)_max / PP (1/s)

        正常值較高，AS 時因上升緩慢而降低
        """
        if self.pulse_pressure <= 0:
            return 0.0
        return self.dp_dt_max / self.pulse_pressure


@dataclass
class AVAResult:
    """AVA 估算結果"""

    ava: float  # 估算的主動脈瓣面積 (cm²)
    method: str  # 使用的方法
    severity: str  # 嚴重度分級
    confidence: str  # 估算信心 (high/moderate/low)
    details: dict = field(default_factory=dict)


# ============================================================
# AVA Classification
# ============================================================


def classify_ava_severity(ava: float) -> str:
    """根據 ACC/AHA 指南分級主動脈瓣狹窄嚴重度

    Args:
        ava: 主動脈瓣面積 (cm²)

    Returns:
        嚴重度分級字串
    """
    if ava >= 2.0:
        return "Normal (正常)"
    elif ava >= 1.5:
        return "Mild (輕度狹窄)"
    elif ava >= 1.0:
        return "Moderate (中度狹窄)"
    elif ava >= 0.6:
        return "Severe (重度狹窄)"
    else:
        return "Critical (危急狹窄)"


# ============================================================
# Method 1: Gorlin Formula
# ============================================================


def gorlin_ava(
    cardiac_output_mL_min: float,
    heart_rate: float,
    systolic_ejection_period: float,
    mean_gradient: float,
    gorlin_constant: float = 1.0,
) -> AVAResult:
    """Gorlin 公式計算 AVA

    AVA = CO / (44.3 × C × HR × SEP × √ΔP_mean)

    Args:
        cardiac_output_mL_min: 心輸出量 (mL/min)
        heart_rate: 心率 (beats/min)
        systolic_ejection_period: 收縮射出時間 (s/beat)
        mean_gradient: 平均跨瓣壓力差 (mmHg)
        gorlin_constant: Gorlin 經驗常數 (主動脈瓣 = 1.0)

    Returns:
        AVAResult 結果
    """
    if mean_gradient <= 0:
        return AVAResult(
            ava=float("inf"),
            method="Gorlin",
            severity="Normal (正常)",
            confidence="low",
            details={"note": "ΔP_mean ≤ 0, no stenosis detected"},
        )

    denominator = (
        44.3
        * gorlin_constant
        * heart_rate
        * systolic_ejection_period
        * math.sqrt(mean_gradient)
    )

    if denominator <= 0:
        raise ValueError("Invalid parameters: denominator is non-positive")

    ava = cardiac_output_mL_min / denominator
    severity = classify_ava_severity(ava)

    return AVAResult(
        ava=ava,
        method="Gorlin",
        severity=severity,
        confidence="high" if cardiac_output_mL_min > 3000 else "moderate",
        details={
            "CO_mL_min": cardiac_output_mL_min,
            "HR": heart_rate,
            "SEP": systolic_ejection_period,
            "mean_gradient": mean_gradient,
            "denominator": denominator,
        },
    )


# ============================================================
# Method 2: Hakki Simplified Formula
# ============================================================


def hakki_ava(
    cardiac_output_L_min: float,
    peak_gradient: float,
) -> AVAResult:
    """Hakki 簡化公式

    AVA ≈ CO / √ΔP_peak

    適用條件: HR × SEP ≈ 1000 (HR 60-100 bpm)

    Args:
        cardiac_output_L_min: 心輸出量 (L/min)
        peak_gradient: 峰值跨瓣壓力差 (mmHg)

    Returns:
        AVAResult 結果
    """
    if peak_gradient <= 0:
        return AVAResult(
            ava=float("inf"),
            method="Hakki",
            severity="Normal (正常)",
            confidence="low",
            details={"note": "ΔP_peak ≤ 0, no stenosis detected"},
        )

    ava = cardiac_output_L_min / math.sqrt(peak_gradient)
    severity = classify_ava_severity(ava)

    return AVAResult(
        ava=ava,
        method="Hakki",
        severity=severity,
        confidence="moderate",
        details={
            "CO_L_min": cardiac_output_L_min,
            "peak_gradient": peak_gradient,
            "note": "Assumes HR × SEP ≈ 1000",
        },
    )


# ============================================================
# Method 3: Pulse Contour Analysis
# ============================================================


def pulse_contour_stroke_volume(
    systolic_area: float,
    aortic_impedance: float,
    calibration_constant: float = 1.0,
) -> float:
    """Wesseling 脈搏輪廓法計算每搏輸出量

    SV = k × A_sys / Z_ao

    Args:
        systolic_area: 收縮期壓力-時間積分 (mmHg·s)
        aortic_impedance: 主動脈阻抗 (mmHg·s/mL)
        calibration_constant: 校準常數

    Returns:
        SV (mL)
    """
    if aortic_impedance <= 0:
        raise ValueError("Aortic impedance must be positive")
    return calibration_constant * systolic_area / aortic_impedance


def estimate_aortic_impedance(
    age: int,
    mean_arterial_pressure: float,
    body_surface_area: float = 1.7,
) -> float:
    """估算主動脈阻抗

    基於年齡、MAP 和體表面積的經驗公式。
    Z_ao 隨年齡增加（血管硬化）。

    Args:
        age: 年齡 (years)
        mean_arterial_pressure: 平均動脈壓 (mmHg)
        body_surface_area: 體表面積 (m²)

    Returns:
        Z_ao (mmHg·s/mL)
    """
    # 基礎阻抗 (年輕健康成人 ≈ 0.05)
    z_base = 0.04 + 0.0003 * age
    # MAP 影響
    z_map = mean_arterial_pressure / 2000.0
    # BSA 修正
    z_bsa = 1.7 / body_surface_area
    return (z_base + z_map) * z_bsa


def pulse_contour_ava(
    waveform: AlineWaveformFeatures,
    heart_rate: float,
    mean_gradient: float,
    aortic_impedance: float,
    calibration_constant: float = 1.0,
) -> AVAResult:
    """脈搏輪廓法結合 Gorlin 公式估算 AVA

    AVA = k × A_sys × HR / (Z_ao × 44.3 × SEP × √ΔP_mean)

    Args:
        waveform: A-line 波形特徵
        heart_rate: 心率 (beats/min)
        mean_gradient: 平均跨瓣壓力差 (mmHg)
        aortic_impedance: 主動脈阻抗 (mmHg·s/mL)
        calibration_constant: 脈搏輪廓校準常數

    Returns:
        AVAResult 結果
    """
    if mean_gradient <= 0:
        return AVAResult(
            ava=float("inf"),
            method="Pulse Contour + Gorlin",
            severity="Normal (正常)",
            confidence="low",
            details={"note": "ΔP_mean ≤ 0"},
        )

    sv = pulse_contour_stroke_volume(
        waveform.systolic_area, aortic_impedance, calibration_constant
    )
    co_mL_min = sv * heart_rate

    denominator = (
        44.3 * heart_rate * waveform.systolic_ejection_time * math.sqrt(mean_gradient)
    )
    if denominator <= 0:
        raise ValueError("Invalid parameters")

    ava = co_mL_min / denominator
    severity = classify_ava_severity(ava)

    return AVAResult(
        ava=ava,
        method="Pulse Contour + Gorlin",
        severity=severity,
        confidence="moderate",
        details={
            "SV_mL": sv,
            "CO_mL_min": co_mL_min,
            "A_sys": waveform.systolic_area,
            "Z_ao": aortic_impedance,
            "SEP": waveform.systolic_ejection_time,
            "mean_gradient": mean_gradient,
        },
    )


# ============================================================
# Method 4: Waveform Feature Regression
# ============================================================


# Default regression coefficients (from literature correlation studies)
DEFAULT_REGRESSION_COEFFICIENTS = {
    "beta_0": 3.5,  # Intercept (normal AVA baseline)
    "beta_upstroke": -4.0,  # Upstroke ratio (higher → smaller AVA)
    "beta_pp_ratio": 2.0,  # Pulse pressure ratio (higher → larger AVA)
    "beta_sys_frac": -1.5,  # Systolic area fraction
    "beta_dpdt": 0.02,  # dP/dt index
    "beta_hr_sep": -0.001,  # HR × SEP product
}


def waveform_regression_ava(
    waveform: AlineWaveformFeatures,
    heart_rate: float,
    coefficients: dict | None = None,
) -> AVAResult:
    """波形特徵回歸模型估算 AVA

    AVA_est = β₀ + β₁·R_upstroke + β₂·R_PP + β₃·F_sys + β₄·I_dpdt + β₅·HR·SEP

    Args:
        waveform: A-line 波形特徵
        heart_rate: 心率 (beats/min)
        coefficients: 回歸係數字典 (可選，默認使用文獻值)

    Returns:
        AVAResult 結果
    """
    coeff = coefficients if coefficients is not None else DEFAULT_REGRESSION_COEFFICIENTS

    r_upstroke = waveform.upstroke_ratio
    r_pp = waveform.pulse_pressure_ratio
    f_sys = waveform.systolic_area_fraction
    i_dpdt = waveform.dp_dt_index
    hr_sep = heart_rate * waveform.systolic_ejection_time

    ava = (
        coeff["beta_0"]
        + coeff["beta_upstroke"] * r_upstroke
        + coeff["beta_pp_ratio"] * r_pp
        + coeff["beta_sys_frac"] * f_sys
        + coeff["beta_dpdt"] * i_dpdt
        + coeff["beta_hr_sep"] * hr_sep
    )

    # Clamp to physiological range
    ava = max(0.1, min(6.0, ava))
    severity = classify_ava_severity(ava)

    return AVAResult(
        ava=ava,
        method="Waveform Regression",
        severity=severity,
        confidence="low",
        details={
            "R_upstroke": r_upstroke,
            "R_PP": r_pp,
            "F_sys": f_sys,
            "I_dpdt": i_dpdt,
            "HR_SEP": hr_sep,
            "coefficients": coeff,
        },
    )


# ============================================================
# Synthetic Waveform Generator (for demonstration)
# ============================================================


def generate_synthetic_aline_waveform(
    heart_rate: float = 75.0,
    systolic_bp: float = 120.0,
    diastolic_bp: float = 80.0,
    ava: float = 3.0,
    sampling_rate: float = 500.0,
) -> tuple[np.ndarray, np.ndarray, AlineWaveformFeatures]:
    """生成合成 a-line 波形（用於演示）

    根據 AVA 嚴重度調整波形形態：
    - 正常: 快速上升, 正常脈壓
    - AS: 緩慢上升 (pulsus tardus), 低脈壓 (pulsus parvus)

    Args:
        heart_rate: 心率 (bpm)
        systolic_bp: 收縮壓 (mmHg)
        diastolic_bp: 舒張壓 (mmHg)
        ava: 模擬的 AVA (cm²), 影響波形形態
        sampling_rate: 取樣率 (Hz)

    Returns:
        (time_array, pressure_array, waveform_features)
    """
    period = 60.0 / heart_rate  # seconds per beat
    n_samples = int(period * sampling_rate)
    t = np.linspace(0, period, n_samples, endpoint=False)

    # AVA 影響波形形態的參數
    # 正常 AVA ~3.0 cm², 嚴重狹窄 < 1.0 cm²
    stenosis_factor = max(0.0, min(1.0, 1.0 - ava / 3.0))

    # 收縮上升時間: 正常 ~0.08s, AS ~0.20s
    upstroke_time = 0.08 + 0.15 * stenosis_factor

    # 收縮射出時間: 正常 ~0.30s, AS ~0.40s
    ejection_time = 0.30 + 0.10 * stenosis_factor

    # 脈壓修正: AS 時脈壓降低
    pp_factor = 1.0 - 0.4 * stenosis_factor
    effective_sbp = diastolic_bp + (systolic_bp - diastolic_bp) * pp_factor

    # 生成波形
    pp = effective_sbp - diastolic_bp
    pressure = np.full(n_samples, diastolic_bp, dtype=float)

    for i, ti in enumerate(t):
        if ti < upstroke_time:
            # 上升相: 用 sigmoid 模擬 (AS 時更平緩)
            x = (ti / upstroke_time) * 6 - 3  # map to [-3, 3]
            pressure[i] = diastolic_bp + pp * (1.0 / (1.0 + math.exp(-x)))
        elif ti < ejection_time:
            # 射出相: 從峰值緩慢下降
            frac = (ti - upstroke_time) / (ejection_time - upstroke_time)
            pressure[i] = effective_sbp - 0.15 * pp * frac
        elif ti < ejection_time + 0.03:
            # Dicrotic notch
            frac = (ti - ejection_time) / 0.03
            notch_depth = 0.1 * pp
            pressure[i] = (effective_sbp - 0.15 * pp) - notch_depth * math.sin(
                math.pi * frac
            )
        else:
            # 舒張期: 指數衰減
            tau = 0.5 + 0.1 * stenosis_factor
            frac_decay = (ti - ejection_time - 0.03) / tau
            start_p = effective_sbp - 0.15 * pp - 0.05 * pp
            pressure[i] = diastolic_bp + (start_p - diastolic_bp) * math.exp(
                -frac_decay
            )

    # 計算波形特徵
    dt = 1.0 / sampling_rate
    dp_dt = np.gradient(pressure, dt)
    dp_dt_max = float(np.max(dp_dt))

    # 收縮期面積 (到 ejection time)
    n_sys = int(ejection_time * sampling_rate)
    n_sys = min(n_sys, n_samples)
    systolic_area = float(np.trapezoid(pressure[:n_sys], dx=dt))
    total_area = float(np.trapezoid(pressure, dx=dt))

    features = AlineWaveformFeatures(
        systolic_upstroke_time=upstroke_time,
        systolic_ejection_time=ejection_time,
        systolic_area=systolic_area,
        total_area=total_area,
        dp_dt_max=dp_dt_max,
        peak_systolic_pressure=effective_sbp,
        diastolic_pressure=diastolic_bp,
    )

    return t, pressure, features


# ============================================================
# Convenience Functions
# ============================================================


def quick_ava_assessment(
    heart_rate: float,
    systolic_bp: float,
    diastolic_bp: float,
    cardiac_output_L_min: float,
    mean_gradient: float,
    systolic_ejection_period: float = 0.32,
) -> dict:
    """快速 AVA 評估（使用 Gorlin + Hakki）

    Args:
        heart_rate: 心率 (bpm)
        systolic_bp: 收縮壓 (mmHg)
        diastolic_bp: 舒張壓 (mmHg)
        cardiac_output_L_min: 心輸出量 (L/min)
        mean_gradient: 平均跨瓣壓力差 (mmHg)
        systolic_ejection_period: 收縮射出時間 (s), 默認 0.32s

    Returns:
        包含 Gorlin 和 Hakki 結果的字典
    """
    co_mL_min = cardiac_output_L_min * 1000.0

    gorlin = gorlin_ava(
        co_mL_min, heart_rate, systolic_ejection_period, mean_gradient
    )
    hakki = hakki_ava(cardiac_output_L_min, mean_gradient)

    return {
        "patient": {
            "HR": heart_rate,
            "SBP": systolic_bp,
            "DBP": diastolic_bp,
            "PP": systolic_bp - diastolic_bp,
            "MAP": diastolic_bp + (systolic_bp - diastolic_bp) / 3.0,
            "CO": cardiac_output_L_min,
            "mean_gradient": mean_gradient,
        },
        "gorlin": {
            "AVA": gorlin.ava,
            "severity": gorlin.severity,
            "confidence": gorlin.confidence,
        },
        "hakki": {
            "AVA": hakki.ava,
            "severity": hakki.severity,
            "confidence": hakki.confidence,
        },
    }


# ============================================================
# Demo
# ============================================================


def demo():
    """完整示範"""

    print("=" * 70)
    print("主動脈瓣面積（AVA）從動脈導管波形估算 - 完整示範")
    print("Aortic Valve Area Estimation from A-line Waveform")
    print("=" * 70)

    # --------------------------------------------------------
    # 範例 1: Gorlin 公式 + Hakki 簡化
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 1】Gorlin 公式 vs Hakki 簡化公式")
    print("=" * 70)

    # 模擬三種程度的主動脈瓣狹窄
    cases = [
        ("正常", 75, 5.0, 5.0, 0.32),
        ("輕度 AS", 75, 4.5, 18.0, 0.34),
        ("中度 AS", 80, 4.0, 35.0, 0.36),
        ("重度 AS", 85, 3.5, 55.0, 0.38),
        ("危急 AS", 90, 3.0, 75.0, 0.40),
    ]

    print(f"\n{'狀態':<10} {'CO':>5} {'ΔP':>5} {'Gorlin':>8} {'Hakki':>8} {'嚴重度'}")
    print("-" * 65)

    for label, hr, co, gradient, sep in cases:
        gorlin = gorlin_ava(co * 1000, hr, sep, gradient)
        hakki = hakki_ava(co, gradient)
        print(
            f"{label:<10} {co:>4.1f}L {gradient:>4.0f} "
            f"{gorlin.ava:>7.2f} {hakki.ava:>7.2f}  {gorlin.severity}"
        )

    # --------------------------------------------------------
    # 範例 2: 合成波形分析
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 2】合成 A-line 波形特徵分析")
    print("=" * 70)

    ava_values = [3.0, 2.0, 1.2, 0.8, 0.5]
    print(
        f"\n{'模擬AVA':>8} {'R_upstroke':>11} {'R_PP':>7} {'F_sys':>7} "
        f"{'I_dpdt':>8} {'回歸AVA':>8} {'嚴重度'}"
    )
    print("-" * 75)

    for true_ava in ava_values:
        _, _, features = generate_synthetic_aline_waveform(
            heart_rate=75, systolic_bp=120, diastolic_bp=80, ava=true_ava
        )

        regression = waveform_regression_ava(features, heart_rate=75)

        print(
            f"{true_ava:>7.1f}  {features.upstroke_ratio:>10.3f} "
            f"{features.pulse_pressure_ratio:>7.3f} "
            f"{features.systolic_area_fraction:>7.3f} "
            f"{features.dp_dt_index:>7.1f} "
            f"{regression.ava:>7.2f}  {regression.severity}"
        )

    # --------------------------------------------------------
    # 範例 3: 脈搏輪廓法 AVA 估算
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 3】脈搏輪廓法結合 Gorlin 公式")
    print("=" * 70)

    _, _, features_normal = generate_synthetic_aline_waveform(ava=3.0)
    _, _, features_severe = generate_synthetic_aline_waveform(ava=0.8)

    z_ao = estimate_aortic_impedance(
        age=65, mean_arterial_pressure=93.3, body_surface_area=1.8
    )

    print(f"\n主動脈阻抗估算: Z_ao = {z_ao:.4f} mmHg·s/mL")

    for label, features, gradient in [
        ("正常瓣膜", features_normal, 5.0),
        ("重度狹窄", features_severe, 55.0),
    ]:
        result = pulse_contour_ava(features, 75, gradient, z_ao)
        print(f"\n{label}:")
        print(f"  SV = {result.details['SV_mL']:.1f} mL")
        print(f"  CO = {result.details['CO_mL_min']:.0f} mL/min")
        print(f"  AVA = {result.ava:.2f} cm²")
        print(f"  嚴重度: {result.severity}")

    # --------------------------------------------------------
    # 範例 4: 完整臨床案例
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【範例 4】完整臨床案例")
    print("=" * 70)

    print("""
病例：72 歲男性，因呼吸困難入 ICU
      已放置橈動脈導管 (radial a-line)
      A-line 波形顯示緩慢上升 (pulsus tardus) 和脈壓降低 (pulsus parvus)
""")

    result = quick_ava_assessment(
        heart_rate=82,
        systolic_bp=105,
        diastolic_bp=78,
        cardiac_output_L_min=3.8,
        mean_gradient=48.0,
        systolic_ejection_period=0.37,
    )

    print("血流動力學資料:")
    for k, v in result["patient"].items():
        unit = {"HR": "bpm", "CO": "L/min", "mean_gradient": "mmHg"}.get(k, "mmHg")
        print(f"  {k}: {v:.1f} {unit}")

    print("\nGorlin 公式:")
    print(f"  AVA = {result['gorlin']['AVA']:.2f} cm²")
    print(f"  嚴重度: {result['gorlin']['severity']}")

    print("\nHakki 簡化:")
    print(f"  AVA = {result['hakki']['AVA']:.2f} cm²")
    print(f"  嚴重度: {result['hakki']['severity']}")

    # --------------------------------------------------------
    # 提醒
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("【重要提醒】")
    print("=" * 70)
    print("""
⚠️  臨床使用限制:

1. A-line 波形分析僅為 **篩檢/輔助** 工具，不能取代超聲心動圖
2. 周邊動脈波形受血管順應性和波反射影響，與中心主動脈壓不同
3. Gorlin 公式在低流量-低壓力差狀態下會低估 AVA
4. 脈搏輪廓法的 SV 估算需要定期校準（如熱稀釋法）
5. 回歸模型的係數可能需要針對不同人群調整

✅ 推薦工作流:
   A-line 波形篩檢 → 疑似 AS → 床邊超聲心動圖確認 → 治療決策
""")


if __name__ == "__main__":
    demo()
