"""
Test Music Function Tools

Tests all 9 music tools:
- music_note_to_frequency: Musical note → Hz conversion
- music_compose_tone: Single sinusoidal tone
- music_compose_chord: Sum of sinusoids (chord)
- music_compose_sequence: Piecewise melody
- music_function_to_waveform: Numerical evaluation
- music_plot_waveform: Time-domain plot
- music_plot_spectrum: Frequency spectrum (FFT)
- music_generate_wav: WAV audio generation
- music_function_info: Symbolic analysis
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from nsforge_mcp.tools.music import register_music_tools


class MockMCP:
    """Mock MCP server to collect tools."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.fixture()
def mcp():
    """Create a MockMCP with music tools registered."""
    mock = MockMCP()
    register_music_tools(mock)
    return mock


# ═══════════════════════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════════════════════


def test_register_all_music_tools(mcp):
    """All 9 music tools should be registered."""
    expected = {
        "music_note_to_frequency",
        "music_compose_tone",
        "music_compose_chord",
        "music_compose_sequence",
        "music_function_to_waveform",
        "music_plot_waveform",
        "music_plot_spectrum",
        "music_generate_wav",
        "music_function_info",
    }
    assert set(mcp.tools.keys()) == expected


# ═══════════════════════════════════════════════════════════════════════════════
# music_note_to_frequency
# ═══════════════════════════════════════════════════════════════════════════════


class TestNoteToFrequency:
    def test_a4_is_440(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("A4")
        assert result["success"]
        assert result["frequency_hz"] == 440.0

    def test_a5_is_880(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("A5")
        assert result["success"]
        assert result["frequency_hz"] == 880.0

    def test_middle_c(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("C4")
        assert result["success"]
        assert abs(result["frequency_hz"] - 261.6256) < 0.01

    def test_c_sharp(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("C#4")
        assert result["success"]
        assert abs(result["frequency_hz"] - 277.1826) < 0.01

    def test_b_flat(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("Bb3")
        assert result["success"]
        assert abs(result["frequency_hz"] - 233.0819) < 0.01

    def test_custom_a4_reference(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("A4", a4_freq=432.0)
        assert result["success"]
        assert result["frequency_hz"] == 432.0

    def test_invalid_note(self, mcp):
        result = mcp.tools["music_note_to_frequency"]("X4")
        assert not result["success"]


# ═══════════════════════════════════════════════════════════════════════════════
# music_compose_tone
# ═══════════════════════════════════════════════════════════════════════════════


class TestComposeTone:
    def test_tone_from_frequency(self, mcp):
        result = mcp.tools["music_compose_tone"](frequency=440.0)
        assert result["success"]
        assert "sin" in result["expression"]
        assert result["frequency_hz"] == 440.0

    def test_tone_from_note(self, mcp):
        result = mcp.tools["music_compose_tone"](note="A4")
        assert result["success"]
        assert "sin" in result["expression"]
        assert result["frequency_hz"] == 440.0

    def test_tone_with_amplitude(self, mcp):
        result = mcp.tools["music_compose_tone"](note="A4", amplitude=0.5)
        assert result["success"]
        assert result["amplitude"] == 0.5

    def test_tone_with_phase(self, mcp):
        result = mcp.tools["music_compose_tone"](note="A4", phase=1.5708)
        assert result["success"]
        assert result["phase"] == 1.5708

    def test_tone_no_input(self, mcp):
        result = mcp.tools["music_compose_tone"]()
        assert not result["success"]

    def test_tone_has_latex(self, mcp):
        result = mcp.tools["music_compose_tone"](frequency=440.0)
        assert result["success"]
        assert "latex" in result
        assert len(result["latex"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# music_compose_chord
# ═══════════════════════════════════════════════════════════════════════════════


class TestComposeChord:
    def test_c_major_chord(self, mcp):
        tones = [{"note": "C4"}, {"note": "E4"}, {"note": "G4"}]
        result = mcp.tools["music_compose_chord"](tones)
        assert result["success"]
        assert result["tone_count"] == 3
        assert "sin" in result["expression"]

    def test_chord_with_frequencies(self, mcp):
        tones = [{"frequency": 440.0}, {"frequency": 550.0}, {"frequency": 660.0}]
        result = mcp.tools["music_compose_chord"](tones)
        assert result["success"]
        assert result["tone_count"] == 3

    def test_empty_chord(self, mcp):
        result = mcp.tools["music_compose_chord"]([])
        assert not result["success"]

    def test_chord_normalization(self, mcp):
        tones = [{"note": "C4"}, {"note": "E4"}]
        result = mcp.tools["music_compose_chord"](tones, normalize=True)
        assert result["success"]
        assert result["normalized"]

    def test_chord_no_normalization(self, mcp):
        tones = [{"note": "C4"}, {"note": "E4"}]
        result = mcp.tools["music_compose_chord"](tones, normalize=False)
        assert result["success"]
        assert not result["normalized"]

    def test_chord_has_latex(self, mcp):
        tones = [{"note": "C4"}, {"note": "E4"}, {"note": "G4"}]
        result = mcp.tools["music_compose_chord"](tones)
        assert result["success"]
        assert "latex" in result


# ═══════════════════════════════════════════════════════════════════════════════
# music_compose_sequence
# ═══════════════════════════════════════════════════════════════════════════════


class TestComposeSequence:
    def test_simple_melody(self, mcp):
        notes = [
            {"note": "C4", "duration": 0.5},
            {"note": "D4", "duration": 0.5},
            {"note": "E4", "duration": 0.5},
        ]
        result = mcp.tools["music_compose_sequence"](notes)
        assert result["success"]
        assert result["note_count"] == 3
        assert result["total_duration"] == 1.5

    def test_melody_with_rest(self, mcp):
        notes = [
            {"note": "C4", "duration": 0.5},
            {"rest": True, "duration": 0.25},
            {"note": "E4", "duration": 0.5},
        ]
        result = mcp.tools["music_compose_sequence"](notes)
        assert result["success"]
        assert result["total_duration"] == 1.25

    def test_default_duration(self, mcp):
        notes = [{"note": "C4"}, {"note": "D4"}]
        result = mcp.tools["music_compose_sequence"](notes, default_duration=0.3)
        assert result["success"]
        assert abs(result["total_duration"] - 0.6) < 0.001

    def test_empty_sequence(self, mcp):
        result = mcp.tools["music_compose_sequence"]([])
        assert not result["success"]

    def test_sequence_has_piecewise(self, mcp):
        notes = [{"note": "C4", "duration": 0.5}, {"note": "E4", "duration": 0.5}]
        result = mcp.tools["music_compose_sequence"](notes)
        assert result["success"]
        assert "Piecewise" in result["expression"]


# ═══════════════════════════════════════════════════════════════════════════════
# music_function_to_waveform
# ═══════════════════════════════════════════════════════════════════════════════


class TestFunctionToWaveform:
    def test_simple_sine(self, mcp):
        result = mcp.tools["music_function_to_waveform"]("sin(2*pi*440*t)", duration=0.01)
        assert result["success"]
        assert result["sample_count"] == 441
        assert result["sample_rate"] == 44100
        assert result["rms"] > 0

    def test_custom_sample_rate(self, mcp):
        result = mcp.tools["music_function_to_waveform"](
            "sin(2*pi*440*t)", duration=0.01, sample_rate=22050
        )
        assert result["success"]
        assert result["sample_rate"] == 22050

    def test_amplitude_range(self, mcp):
        result = mcp.tools["music_function_to_waveform"]("sin(2*pi*440*t)", duration=0.1)
        assert result["success"]
        assert result["min_amplitude"] >= -1.01
        assert result["max_amplitude"] <= 1.01


# ═══════════════════════════════════════════════════════════════════════════════
# music_plot_waveform
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlotWaveform:
    def test_plot_to_file(self, mcp):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = mcp.tools["music_plot_waveform"](
                "sin(2*pi*440*t)", duration=0.005, output_path=path
            )
            assert result["success"]
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_plot_to_base64(self, mcp):
        result = mcp.tools["music_plot_waveform"]("sin(2*pi*440*t)", duration=0.005)
        assert result["success"]
        assert "image_base64" in result
        assert len(result["image_base64"]) > 100


# ═══════════════════════════════════════════════════════════════════════════════
# music_plot_spectrum
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlotSpectrum:
    def test_spectrum_to_file(self, mcp):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = mcp.tools["music_plot_spectrum"](
                "sin(2*pi*440*t)", duration=1.0, output_path=path
            )
            assert result["success"]
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_spectrum_dominant_frequency(self, mcp):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = mcp.tools["music_plot_spectrum"](
                "sin(2*pi*440*t) + 0.5*sin(2*pi*880*t)", duration=1.0, output_path=path
            )
            assert result["success"]
            freqs = result["dominant_frequencies"]
            assert len(freqs) >= 2
            # The highest magnitude should be near 440 Hz
            assert abs(freqs[0]["frequency_hz"] - 440.0) < 2.0
        finally:
            os.unlink(path)

    def test_spectrum_to_base64(self, mcp):
        result = mcp.tools["music_plot_spectrum"]("sin(2*pi*440*t)", duration=0.1)
        assert result["success"]
        assert "image_base64" in result


# ═══════════════════════════════════════════════════════════════════════════════
# music_generate_wav
# ═══════════════════════════════════════════════════════════════════════════════


class TestGenerateWav:
    def test_generate_wav_file(self, mcp):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            result = mcp.tools["music_generate_wav"](
                "sin(2*pi*440*t)", duration=0.5, output_path=path
            )
            assert result["success"]
            assert os.path.exists(path)
            assert os.path.getsize(path) > 44  # WAV header is 44 bytes
            assert result["duration"] == 0.5
            assert result["sample_rate"] == 44100
            assert result["bit_depth"] == 16
        finally:
            os.unlink(path)

    def test_wav_custom_sample_rate(self, mcp):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            result = mcp.tools["music_generate_wav"](
                "sin(2*pi*440*t)", duration=0.1, sample_rate=22050, output_path=path
            )
            assert result["success"]
            assert result["sample_rate"] == 22050
        finally:
            os.unlink(path)


# ═══════════════════════════════════════════════════════════════════════════════
# music_function_info
# ═══════════════════════════════════════════════════════════════════════════════


class TestFunctionInfo:
    def test_single_sine(self, mcp):
        result = mcp.tools["music_function_info"]("sin(2*pi*440*t)")
        assert result["success"]
        assert "t" in result["free_symbols"]
        assert result["is_periodic"]

    def test_sum_of_sines(self, mcp):
        result = mcp.tools["music_function_info"]("sin(2*pi*440*t) + 0.5*sin(2*pi*880*t)")
        assert result["success"]
        assert result["num_terms"] == 2
        assert result["expression_type"] == "sum"

    def test_latex_output(self, mcp):
        result = mcp.tools["music_function_info"]("sin(2*pi*440*t)")
        assert result["success"]
        assert "latex" in result
        assert "\\sin" in result["latex"]

    def test_invalid_expression(self, mcp):
        result = mcp.tools["music_function_info"]("invalid+++")
        assert not result["success"]
