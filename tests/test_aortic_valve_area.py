"""
Tests for Aortic Valve Area estimation from A-line waveform.
"""

import math

import numpy as np
import pytest
from examples.aortic_valve_area_aline import (
    AlineWaveformFeatures,
    AVAResult,
    PatientHemodynamics,
    classify_ava_severity,
    estimate_aortic_impedance,
    generate_synthetic_aline_waveform,
    gorlin_ava,
    hakki_ava,
    pulse_contour_ava,
    pulse_contour_stroke_volume,
    quick_ava_assessment,
    waveform_regression_ava,
)

# ============================================================
# Classification Tests
# ============================================================


class TestClassifyAVASeverity:
    def test_normal(self):
        assert classify_ava_severity(3.0) == "Normal (正常)"
        assert classify_ava_severity(2.5) == "Normal (正常)"
        assert classify_ava_severity(2.0) == "Normal (正常)"

    def test_mild(self):
        assert classify_ava_severity(1.8) == "Mild (輕度狹窄)"
        assert classify_ava_severity(1.5) == "Mild (輕度狹窄)"

    def test_moderate(self):
        assert classify_ava_severity(1.2) == "Moderate (中度狹窄)"
        assert classify_ava_severity(1.0) == "Moderate (中度狹窄)"

    def test_severe(self):
        assert classify_ava_severity(0.8) == "Severe (重度狹窄)"
        assert classify_ava_severity(0.6) == "Severe (重度狹窄)"

    def test_critical(self):
        assert classify_ava_severity(0.5) == "Critical (危急狹窄)"
        assert classify_ava_severity(0.3) == "Critical (危急狹窄)"


# ============================================================
# PatientHemodynamics Tests
# ============================================================


class TestPatientHemodynamics:
    def test_pulse_pressure(self):
        p = PatientHemodynamics(heart_rate=75, systolic_bp=120, diastolic_bp=80)
        assert p.pulse_pressure == 40.0

    def test_mean_arterial_pressure(self):
        p = PatientHemodynamics(heart_rate=75, systolic_bp=120, diastolic_bp=80)
        expected = 80 + 40 / 3.0
        assert abs(p.mean_arterial_pressure - expected) < 0.01


# ============================================================
# AlineWaveformFeatures Tests
# ============================================================


class TestAlineWaveformFeatures:
    @pytest.fixture
    def normal_waveform(self):
        return AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )

    def test_pulse_pressure(self, normal_waveform):
        assert normal_waveform.pulse_pressure == 40.0

    def test_upstroke_ratio_normal(self, normal_waveform):
        expected = 0.08 / 0.30
        assert abs(normal_waveform.upstroke_ratio - expected) < 0.01

    def test_pulse_pressure_ratio(self, normal_waveform):
        pp = 40.0
        mean_ap = 80.0 + pp / 3.0
        expected = pp / mean_ap
        assert abs(normal_waveform.pulse_pressure_ratio - expected) < 0.01

    def test_systolic_area_fraction(self, normal_waveform):
        expected = 25.0 / 60.0
        assert abs(normal_waveform.systolic_area_fraction - expected) < 0.01

    def test_dp_dt_index(self, normal_waveform):
        expected = 1200.0 / 40.0
        assert abs(normal_waveform.dp_dt_index - expected) < 0.01

    def test_zero_ejection_time(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.0,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        assert wf.upstroke_ratio == 0.0

    def test_zero_total_area(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=0.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        assert wf.systolic_area_fraction == 0.0

    def test_zero_pulse_pressure(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=80.0,
            diastolic_pressure=80.0,
        )
        assert wf.dp_dt_index == 0.0
        assert wf.pulse_pressure_ratio == 0.0


# ============================================================
# Gorlin Formula Tests
# ============================================================


class TestGorlinAVA:
    def test_normal_valve(self):
        """Normal CO 5 L/min, low gradient → large AVA"""
        result = gorlin_ava(
            cardiac_output_mL_min=5000,
            heart_rate=75,
            systolic_ejection_period=0.32,
            mean_gradient=5.0,
        )
        assert result.ava > 2.0
        assert result.method == "Gorlin"
        assert "Normal" in result.severity

    def test_severe_stenosis(self):
        """Low CO, high gradient → small AVA"""
        result = gorlin_ava(
            cardiac_output_mL_min=3500,
            heart_rate=85,
            systolic_ejection_period=0.38,
            mean_gradient=55.0,
        )
        assert result.ava < 1.0
        assert "Severe" in result.severity or "Critical" in result.severity

    def test_zero_gradient(self):
        """Zero gradient → infinite AVA (no stenosis)"""
        result = gorlin_ava(5000, 75, 0.32, 0.0)
        assert result.ava == float("inf")

    def test_negative_gradient(self):
        """Negative gradient → no stenosis"""
        result = gorlin_ava(5000, 75, 0.32, -5.0)
        assert result.ava == float("inf")

    def test_low_co_confidence(self):
        """Low CO → moderate confidence"""
        result = gorlin_ava(2500, 75, 0.32, 30.0)
        assert result.confidence == "moderate"

    def test_high_co_confidence(self):
        """Normal CO → high confidence"""
        result = gorlin_ava(5000, 75, 0.32, 30.0)
        assert result.confidence == "high"


# ============================================================
# Hakki Formula Tests
# ============================================================


class TestHakkiAVA:
    def test_normal_valve(self):
        result = hakki_ava(5.0, 5.0)
        # AVA = 5 / sqrt(5) ≈ 2.24
        expected = 5.0 / math.sqrt(5.0)
        assert abs(result.ava - expected) < 0.01
        assert "Normal" in result.severity

    def test_severe_stenosis(self):
        result = hakki_ava(3.5, 64.0)
        # AVA = 3.5 / sqrt(64) = 3.5 / 8 = 0.4375
        assert abs(result.ava - 0.4375) < 0.01
        assert "Critical" in result.severity

    def test_zero_gradient(self):
        result = hakki_ava(5.0, 0.0)
        assert result.ava == float("inf")

    def test_method_name(self):
        result = hakki_ava(5.0, 25.0)
        assert result.method == "Hakki"


# ============================================================
# Pulse Contour Tests
# ============================================================


class TestPulseContour:
    def test_stroke_volume(self):
        sv = pulse_contour_stroke_volume(
            systolic_area=25.0, aortic_impedance=0.05, calibration_constant=0.1
        )
        # SV = 0.1 * 25 / 0.05 = 50 mL
        assert abs(sv - 50.0) < 0.01

    def test_stroke_volume_zero_impedance(self):
        with pytest.raises(ValueError):
            pulse_contour_stroke_volume(25.0, 0.0)

    def test_aortic_impedance_age_increases(self):
        z_young = estimate_aortic_impedance(30, 90.0)
        z_old = estimate_aortic_impedance(70, 90.0)
        assert z_old > z_young

    def test_pulse_contour_ava(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        result = pulse_contour_ava(wf, 75, 20.0, 0.05, calibration_constant=0.1)
        assert result.ava > 0
        assert result.method == "Pulse Contour + Gorlin"
        assert "SV_mL" in result.details

    def test_pulse_contour_ava_zero_gradient(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        result = pulse_contour_ava(wf, 75, 0.0, 0.05)
        assert result.ava == float("inf")


# ============================================================
# Waveform Regression Tests
# ============================================================


class TestWaveformRegression:
    def test_normal_waveform(self):
        """Normal waveform features → normal AVA range"""
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        result = waveform_regression_ava(wf, heart_rate=75)
        assert result.ava > 0.1
        assert result.method == "Waveform Regression"

    def test_stenotic_waveform(self):
        """Stenotic waveform (slow upstroke, low PP) → lower AVA"""
        wf_normal = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        wf_stenotic = AlineWaveformFeatures(
            systolic_upstroke_time=0.18,
            systolic_ejection_time=0.38,
            systolic_area=28.0,
            total_area=55.0,
            dp_dt_max=500.0,
            peak_systolic_pressure=100.0,
            diastolic_pressure=82.0,
        )
        ava_normal = waveform_regression_ava(wf_normal, 75).ava
        ava_stenotic = waveform_regression_ava(wf_stenotic, 85).ava
        assert ava_stenotic < ava_normal

    def test_clamping(self):
        """AVA should be clamped to physiological range [0.1, 6.0]"""
        # Extreme features
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.30,
            systolic_ejection_time=0.35,
            systolic_area=35.0,
            total_area=40.0,
            dp_dt_max=100.0,
            peak_systolic_pressure=85.0,
            diastolic_pressure=80.0,
        )
        result = waveform_regression_ava(wf, heart_rate=100)
        assert 0.1 <= result.ava <= 6.0

    def test_custom_coefficients(self):
        wf = AlineWaveformFeatures(
            systolic_upstroke_time=0.08,
            systolic_ejection_time=0.30,
            systolic_area=25.0,
            total_area=60.0,
            dp_dt_max=1200.0,
            peak_systolic_pressure=120.0,
            diastolic_pressure=80.0,
        )
        custom = {
            "beta_0": 2.0,
            "beta_upstroke": 0.0,
            "beta_pp_ratio": 0.0,
            "beta_sys_frac": 0.0,
            "beta_dpdt": 0.0,
            "beta_hr_sep": 0.0,
        }
        result = waveform_regression_ava(wf, 75, coefficients=custom)
        assert abs(result.ava - 2.0) < 0.01


# ============================================================
# Synthetic Waveform Tests
# ============================================================


class TestSyntheticWaveform:
    def test_returns_correct_shapes(self):
        t, p, features = generate_synthetic_aline_waveform()
        assert len(t) == len(p)
        assert len(t) > 0

    def test_pressure_range(self):
        t, p, features = generate_synthetic_aline_waveform(
            systolic_bp=120, diastolic_bp=80
        )
        # Pressure should generally be within physiological range
        assert np.min(p) >= 60  # Should not drop below reasonable floor
        assert np.max(p) <= 140  # Should not exceed reasonable ceiling

    def test_stenosis_reduces_pulse_pressure(self):
        _, _, feat_normal = generate_synthetic_aline_waveform(ava=3.0)
        _, _, feat_severe = generate_synthetic_aline_waveform(ava=0.5)
        assert feat_severe.pulse_pressure < feat_normal.pulse_pressure

    def test_stenosis_increases_upstroke_time(self):
        _, _, feat_normal = generate_synthetic_aline_waveform(ava=3.0)
        _, _, feat_severe = generate_synthetic_aline_waveform(ava=0.5)
        assert feat_severe.systolic_upstroke_time > feat_normal.systolic_upstroke_time

    def test_features_are_positive(self):
        _, _, features = generate_synthetic_aline_waveform()
        assert features.systolic_area > 0
        assert features.total_area > 0
        assert features.dp_dt_max > 0
        assert features.systolic_ejection_time > 0


# ============================================================
# Quick Assessment Tests
# ============================================================


class TestQuickAssessment:
    def test_returns_expected_keys(self):
        result = quick_ava_assessment(
            heart_rate=75,
            systolic_bp=120,
            diastolic_bp=80,
            cardiac_output_L_min=5.0,
            mean_gradient=10.0,
        )
        assert "patient" in result
        assert "gorlin" in result
        assert "hakki" in result
        assert "AVA" in result["gorlin"]
        assert "severity" in result["gorlin"]

    def test_normal_assessment(self):
        result = quick_ava_assessment(
            heart_rate=75,
            systolic_bp=120,
            diastolic_bp=80,
            cardiac_output_L_min=5.0,
            mean_gradient=5.0,
        )
        assert result["gorlin"]["AVA"] > 2.0

    def test_severe_assessment(self):
        result = quick_ava_assessment(
            heart_rate=85,
            systolic_bp=100,
            diastolic_bp=75,
            cardiac_output_L_min=3.5,
            mean_gradient=55.0,
        )
        assert result["gorlin"]["AVA"] < 1.5


# ============================================================
# AVAResult Tests
# ============================================================


class TestAVAResult:
    def test_default_details(self):
        r = AVAResult(ava=1.0, method="test", severity="test", confidence="low")
        assert r.details == {}

    def test_with_details(self):
        r = AVAResult(
            ava=1.0,
            method="test",
            severity="test",
            confidence="low",
            details={"key": "value"},
        )
        assert r.details["key"] == "value"
