"""
Music Function Tools

Tools for representing music as mathematical functions and generating
scientific visualizations (waveform plots, frequency spectra) from them.

═══════════════════════════════════════════════════════════════════════════════
🎵 CONCEPT: Sound as Mathematical Functions
═══════════════════════════════════════════════════════════════════════════════

Every sound can be expressed as a function of time:
- A pure tone is a sinusoid: A·sin(2πft + φ)
- A chord is a sum of sinusoids
- A melody is a piecewise function of tones over time intervals
- Any periodic sound can be decomposed via Fourier series

These tools bridge symbolic math (SymPy) with scientific visualization
(matplotlib) and audio generation (scipy.io.wavfile), enabling:
1. Symbolic representation of music as mathematical expressions
2. Time-domain waveform plotting (oscilloscope view)
3. Frequency-domain spectrum plotting (FFT analysis)
4. WAV audio file generation from the mathematical function

═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import base64
import io
import wave
from typing import Any

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# Standard transformations for parsing
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Musical note → frequency mapping (Equal temperament, A4 = 440 Hz)
# ═══════════════════════════════════════════════════════════════════════════════

# Semitone offsets from C within an octave
_NOTE_OFFSETS: dict[str, int] = {
    "C": -9,
    "D": -7,
    "E": -5,
    "F": -4,
    "G": -2,
    "A": 0,
    "B": 2,
}


def _note_to_frequency(note: str, a4_freq: float = 440.0) -> float:
    """Convert a musical note name to its frequency in Hz.

    Supports formats like: A4, C#5, Bb3, D##4, Ebb2
    Uses 12-tone equal temperament with configurable A4 reference.
    """
    if not note or len(note) < 2:
        msg = f"Invalid note format: '{note}'. Expected format like 'A4', 'C#5', 'Bb3'."
        raise ValueError(msg)

    # Parse note name, accidentals, and octave
    base = note[0].upper()
    if base not in _NOTE_OFFSETS:
        msg = f"Unknown note name: '{base}'. Must be one of A-G."
        raise ValueError(msg)

    rest = note[1:]
    accidental = 0
    i = 0
    while i < len(rest) and rest[i] in ("#", "b"):
        if rest[i] == "#":
            accidental += 1
        else:
            accidental -= 1
        i += 1

    octave_str = rest[i:]
    if not octave_str.lstrip("-").isdigit():
        msg = f"Invalid octave in note: '{note}'. Expected a number after note name."
        raise ValueError(msg)
    octave = int(octave_str)

    # Calculate semitones from A4
    semitones = _NOTE_OFFSETS[base] + accidental + (octave - 4) * 12

    return a4_freq * (2.0 ** (semitones / 12.0))


def register_music_tools(mcp: Any) -> None:  # noqa: C901
    """Register music function tools with MCP server.

    These tools enable representing music as mathematical functions
    and generating scientific visualizations from them.
    """

    @mcp.tool()
    def music_note_to_frequency(
        note: str,
        a4_freq: float = 440.0,
    ) -> dict[str, Any]:
        """
        Convert a musical note name to its frequency in Hz.

        Uses 12-tone equal temperament tuning.

        Args:
            note: Note name with octave (e.g., "A4", "C#5", "Bb3", "D4")
            a4_freq: Reference frequency for A4 in Hz (default: 440.0)

        Returns:
            Frequency in Hz and the symbolic expression f = 440 * 2^(n/12)

        Examples:
            music_note_to_frequency("A4")     → 440.0 Hz
            music_note_to_frequency("C4")     → 261.63 Hz (Middle C)
            music_note_to_frequency("A5")     → 880.0 Hz
        """
        try:
            freq = _note_to_frequency(note, a4_freq)
            return {
                "success": True,
                "note": note,
                "frequency_hz": round(freq, 4),
                "a4_reference": a4_freq,
                "formula": f"{a4_freq} * 2^(n/12)",
                "description": f"Note {note} = {round(freq, 4)} Hz",
            }
        except (ValueError, IndexError) as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_compose_tone(
        frequency: float | None = None,
        note: str | None = None,
        amplitude: float = 1.0,
        phase: float = 0.0,
        duration: float = 1.0,
    ) -> dict[str, Any]:
        """
        Create a symbolic tone function: A·sin(2πft + φ).

        A pure tone is the fundamental building block of music.
        Provide either a frequency in Hz or a note name.

        Args:
            frequency: Frequency in Hz (e.g., 440.0)
            note: Musical note name (e.g., "A4", "C#5") — used if frequency is None
            amplitude: Amplitude (default: 1.0)
            phase: Phase offset in radians (default: 0.0)
            duration: Duration in seconds (default: 1.0)

        Returns:
            Symbolic expression and metadata

        Examples:
            music_compose_tone(frequency=440.0)          → sin(880*pi*t)
            music_compose_tone(note="A4")                → sin(880*pi*t)
            music_compose_tone(note="C4", amplitude=0.5) → 0.5*sin(...)
        """
        try:
            if frequency is None and note is None:
                return {"success": False, "error": "Provide either 'frequency' or 'note'."}

            if frequency is None and note is not None:
                frequency = _note_to_frequency(note)

            t = sp.Symbol("t")
            freq_val = sp.Rational(frequency).limit_denominator(10000)
            amp_val = sp.Rational(amplitude).limit_denominator(10000)

            if phase == 0.0:
                expr = amp_val * sp.sin(2 * sp.pi * freq_val * t)
            else:
                phase_val = sp.Rational(phase).limit_denominator(10000)
                expr = amp_val * sp.sin(2 * sp.pi * freq_val * t + phase_val)

            return {
                "success": True,
                "expression": str(expr),
                "latex": sp.latex(expr),
                "frequency_hz": float(frequency),
                "amplitude": float(amplitude),
                "phase": float(phase),
                "duration": float(duration),
                "note": note or f"{frequency} Hz",
                "description": f"Tone: {note or f'{frequency} Hz'}, A={amplitude}, dur={duration}s",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_compose_chord(
        tones: list[dict[str, Any]],
        normalize: bool = True,
    ) -> dict[str, Any]:
        """
        Combine multiple tones into a chord (sum of sinusoids).

        A chord is a superposition of pure tones: f(t) = Σ Aᵢ·sin(2πfᵢt + φᵢ)

        Args:
            tones: List of tone specifications, each with:
                - "frequency" (float) or "note" (str): pitch
                - "amplitude" (float, optional): default 1.0
                - "phase" (float, optional): default 0.0
            normalize: If True, normalize total amplitude to 1.0 (default: True)

        Returns:
            Combined symbolic expression

        Examples:
            music_compose_chord([
                {"note": "C4"},
                {"note": "E4"},
                {"note": "G4"}
            ])
            → C major chord as sum of sinusoids
        """
        try:
            if not tones:
                return {"success": False, "error": "At least one tone is required."}

            t = sp.Symbol("t")
            total_expr = sp.Integer(0)
            tone_info = []

            for tone in tones:
                freq = tone.get("frequency")
                note = tone.get("note")
                amp = tone.get("amplitude", 1.0)
                phase = tone.get("phase", 0.0)

                if freq is None and note is None:
                    return {
                        "success": False,
                        "error": "Each tone must have 'frequency' or 'note'.",
                    }

                if freq is None and note is not None:
                    freq = _note_to_frequency(note)

                freq_val = sp.Rational(freq).limit_denominator(10000)
                amp_val = sp.Rational(amp).limit_denominator(10000)

                if phase == 0.0:
                    term = amp_val * sp.sin(2 * sp.pi * freq_val * t)
                else:
                    phase_val = sp.Rational(phase).limit_denominator(10000)
                    term = amp_val * sp.sin(2 * sp.pi * freq_val * t + phase_val)

                total_expr += term
                tone_info.append({
                    "note": note or f"{freq} Hz",
                    "frequency_hz": float(freq),
                    "amplitude": float(amp),
                })

            if normalize and len(tones) > 1:
                total_expr = total_expr / len(tones)

            return {
                "success": True,
                "expression": str(total_expr),
                "latex": sp.latex(total_expr),
                "tones": tone_info,
                "tone_count": len(tones),
                "normalized": normalize,
                "description": f"Chord with {len(tones)} tones",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_compose_sequence(
        notes: list[dict[str, Any]],
        default_duration: float = 0.5,
    ) -> dict[str, Any]:
        """
        Compose a melody as a piecewise function of tones over time.

        A melody is a sequence of notes played one after another,
        represented as a piecewise function:
            f(t) = { A₁·sin(2πf₁t)  for 0 ≤ t < d₁
                   { A₂·sin(2πf₂t)  for d₁ ≤ t < d₁+d₂
                   { ...

        Args:
            notes: List of note specifications in order:
                - "note" (str) or "frequency" (float): pitch
                - "duration" (float, optional): duration in seconds
                - "amplitude" (float, optional): default 1.0
                - "rest" (bool, optional): if True, this is a rest (silence)
            default_duration: Default note duration in seconds (default: 0.5)

        Returns:
            Piecewise expression and total duration

        Examples:
            music_compose_sequence([
                {"note": "C4", "duration": 0.5},
                {"note": "D4", "duration": 0.5},
                {"note": "E4", "duration": 0.5},
                {"note": "C4", "duration": 0.5}
            ])
            → "Twinkle Twinkle" opening as a piecewise function
        """
        try:
            if not notes:
                return {"success": False, "error": "At least one note is required."}

            t = sp.Symbol("t")
            pieces = []
            current_time = 0.0
            note_info = []

            for item in notes:
                dur = item.get("duration", default_duration)
                amp = item.get("amplitude", 1.0)
                is_rest = item.get("rest", False)

                start = sp.Rational(current_time).limit_denominator(10000)
                end = sp.Rational(current_time + dur).limit_denominator(10000)

                if is_rest:
                    expr = sp.Integer(0)
                    note_info.append({
                        "type": "rest",
                        "start": float(current_time),
                        "duration": float(dur),
                    })
                else:
                    freq = item.get("frequency")
                    note = item.get("note")
                    if freq is None and note is None:
                        return {
                            "success": False,
                            "error": "Each note must have 'frequency', 'note', or 'rest': True.",
                        }
                    if freq is None and note is not None:
                        freq = _note_to_frequency(note)

                    freq_val = sp.Rational(freq).limit_denominator(10000)
                    amp_val = sp.Rational(amp).limit_denominator(10000)
                    expr = amp_val * sp.sin(2 * sp.pi * freq_val * t)

                    note_info.append({
                        "type": "note",
                        "note": note or f"{freq} Hz",
                        "frequency_hz": float(freq),
                        "start": float(current_time),
                        "duration": float(dur),
                    })

                condition = sp.And(t >= start, t < end)
                pieces.append((expr, condition))
                current_time += dur

            # Add silence after the last note
            pieces.append((sp.Integer(0), True))
            piecewise_expr = sp.Piecewise(*pieces)

            total_duration = current_time

            return {
                "success": True,
                "expression": str(piecewise_expr),
                "latex": sp.latex(piecewise_expr),
                "notes": note_info,
                "total_duration": float(total_duration),
                "note_count": len(notes),
                "description": f"Melody: {len(notes)} notes, {total_duration:.2f}s total",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_function_to_waveform(
        expression: str,
        duration: float = 1.0,
        sample_rate: int = 44100,
    ) -> dict[str, Any]:
        """
        Numerically evaluate a music function to produce waveform data.

        Takes any symbolic expression f(t) and evaluates it at discrete
        time points to produce a digital waveform.

        Args:
            expression: SymPy expression in terms of 't' (e.g., "sin(2*pi*440*t)")
            duration: Duration in seconds (default: 1.0)
            sample_rate: Samples per second (default: 44100, CD quality)

        Returns:
            Waveform data summary (sample count, min/max amplitude, RMS)

        Examples:
            music_function_to_waveform("sin(2*pi*440*t)", duration=0.5)
            → Evaluates A4 tone for 0.5 seconds at 44100 Hz sample rate
        """
        try:
            expr_clean = expression.replace("^", "**")
            t = sp.Symbol("t")
            sympy_expr = parse_expr(expr_clean, transformations=TRANSFORMATIONS)

            # Create fast numerical function
            f_numeric = sp.lambdify(t, sympy_expr, modules=["numpy"])

            # Generate time array and evaluate
            num_samples = int(duration * sample_rate)
            t_array = np.linspace(0, duration, num_samples, endpoint=False)
            waveform = np.array(f_numeric(t_array), dtype=np.float64)

            # Handle scalar results (constant functions)
            if waveform.ndim == 0:
                waveform = np.full(num_samples, float(waveform))

            rms = float(np.sqrt(np.mean(waveform**2)))

            return {
                "success": True,
                "sample_count": num_samples,
                "sample_rate": sample_rate,
                "duration": duration,
                "min_amplitude": float(np.min(waveform)),
                "max_amplitude": float(np.max(waveform)),
                "rms": round(rms, 6),
                "expression": str(sympy_expr),
                "description": (
                    f"Waveform: {num_samples} samples, "
                    f"{duration}s at {sample_rate} Hz, "
                    f"RMS={rms:.4f}"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_plot_waveform(
        expression: str,
        duration: float = 0.01,
        sample_rate: int = 44100,
        title: str = "Waveform",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Plot the time-domain waveform of a music function.

        Generates a scientific plot showing amplitude vs. time,
        like an oscilloscope display.

        Args:
            expression: SymPy expression in terms of 't'
            duration: Duration to plot in seconds (default: 0.01 for detail)
            sample_rate: Samples per second (default: 44100)
            title: Plot title (default: "Waveform")
            output_path: File path to save the plot (e.g., "waveform.png").
                         If None, returns base64-encoded PNG.

        Returns:
            Plot file path or base64-encoded PNG image

        Examples:
            music_plot_waveform("sin(2*pi*440*t)", duration=0.005)
            → Oscilloscope view of A4 tone showing ~2 cycles
        """
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            expr_clean = expression.replace("^", "**")
            t = sp.Symbol("t")
            sympy_expr = parse_expr(expr_clean, transformations=TRANSFORMATIONS)

            f_numeric = sp.lambdify(t, sympy_expr, modules=["numpy"])

            num_samples = int(duration * sample_rate)
            t_array = np.linspace(0, duration, num_samples, endpoint=False)
            waveform = np.array(f_numeric(t_array), dtype=np.float64)
            if waveform.ndim == 0:
                waveform = np.full(num_samples, float(waveform))

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(t_array * 1000, waveform, linewidth=0.5, color="#2196F3")
            ax.set_xlabel("Time (ms)")
            ax.set_ylabel("Amplitude")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="gray", linewidth=0.5)
            fig.tight_layout()

            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches="tight")
                plt.close(fig)
                return {
                    "success": True,
                    "file_path": output_path,
                    "format": "png",
                    "description": f"Waveform plot saved to {output_path}",
                }
            else:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                return {
                    "success": True,
                    "image_base64": img_base64,
                    "format": "png",
                    "description": f"Waveform plot: {title}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_plot_spectrum(
        expression: str,
        duration: float = 1.0,
        sample_rate: int = 44100,
        max_freq: float = 2000.0,
        title: str = "Frequency Spectrum",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Plot the frequency spectrum (FFT) of a music function.

        Performs Fast Fourier Transform on the evaluated waveform
        and plots magnitude vs. frequency — a spectral analysis view.

        Args:
            expression: SymPy expression in terms of 't'
            duration: Duration for FFT analysis in seconds (default: 1.0)
            sample_rate: Samples per second (default: 44100)
            max_freq: Maximum frequency to display in Hz (default: 2000.0)
            title: Plot title (default: "Frequency Spectrum")
            output_path: File path to save the plot. If None, returns base64 PNG.

        Returns:
            Plot and dominant frequency information

        Examples:
            music_plot_spectrum("sin(2*pi*440*t) + 0.5*sin(2*pi*880*t)")
            → Shows peaks at 440 Hz (fundamental) and 880 Hz (harmonic)
        """
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            expr_clean = expression.replace("^", "**")
            t = sp.Symbol("t")
            sympy_expr = parse_expr(expr_clean, transformations=TRANSFORMATIONS)

            f_numeric = sp.lambdify(t, sympy_expr, modules=["numpy"])

            num_samples = int(duration * sample_rate)
            t_array = np.linspace(0, duration, num_samples, endpoint=False)
            waveform = np.array(f_numeric(t_array), dtype=np.float64)
            if waveform.ndim == 0:
                waveform = np.full(num_samples, float(waveform))

            # Compute FFT
            fft_vals = np.fft.rfft(waveform)
            fft_freqs = np.fft.rfftfreq(num_samples, d=1.0 / sample_rate)
            fft_magnitude = np.abs(fft_vals) / num_samples * 2

            # Find dominant frequencies (peaks above 5% of max)
            if np.max(fft_magnitude) > 0:
                threshold = 0.05 * np.max(fft_magnitude)
                peak_indices = np.where(fft_magnitude > threshold)[0]
                dominant_freqs = [
                    {"frequency_hz": round(float(fft_freqs[i]), 2),
                     "magnitude": round(float(fft_magnitude[i]), 6)}
                    for i in peak_indices
                    if fft_freqs[i] > 0 and fft_freqs[i] <= max_freq
                ]
                # Sort by magnitude descending, limit to top 10
                dominant_freqs.sort(key=lambda x: x["magnitude"], reverse=True)
                dominant_freqs = dominant_freqs[:10]
            else:
                dominant_freqs = []

            # Plot
            freq_mask = fft_freqs <= max_freq
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(
                fft_freqs[freq_mask],
                fft_magnitude[freq_mask],
                linewidth=0.8,
                color="#FF5722",
            )
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Magnitude")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()

            if output_path:
                fig.savefig(output_path, dpi=150, bbox_inches="tight")
                plt.close(fig)
                return {
                    "success": True,
                    "file_path": output_path,
                    "format": "png",
                    "dominant_frequencies": dominant_freqs,
                    "description": f"Spectrum plot saved to {output_path}",
                }
            else:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                return {
                    "success": True,
                    "image_base64": img_base64,
                    "format": "png",
                    "dominant_frequencies": dominant_freqs,
                    "description": f"Spectrum plot: {title}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_generate_wav(
        expression: str,
        duration: float = 1.0,
        sample_rate: int = 44100,
        output_path: str = "output.wav",
        amplitude_scale: float = 0.8,
    ) -> dict[str, Any]:
        """
        Generate a WAV audio file from a mathematical function.

        Evaluates the function f(t) numerically and writes the result
        as a standard 16-bit PCM WAV file.

        Args:
            expression: SymPy expression in terms of 't'
            duration: Duration in seconds (default: 1.0)
            sample_rate: Samples per second (default: 44100, CD quality)
            output_path: Path to save the WAV file (default: "output.wav")
            amplitude_scale: Scale factor to prevent clipping (default: 0.8)

        Returns:
            File path and audio metadata

        Examples:
            music_generate_wav("sin(2*pi*440*t)", duration=2.0)
            → Generates a 2-second A4 tone as WAV file
        """
        try:
            expr_clean = expression.replace("^", "**")
            t = sp.Symbol("t")
            sympy_expr = parse_expr(expr_clean, transformations=TRANSFORMATIONS)

            f_numeric = sp.lambdify(t, sympy_expr, modules=["numpy"])

            num_samples = int(duration * sample_rate)
            t_array = np.linspace(0, duration, num_samples, endpoint=False)
            waveform = np.array(f_numeric(t_array), dtype=np.float64)
            if waveform.ndim == 0:
                waveform = np.full(num_samples, float(waveform))

            # Normalize to prevent clipping
            max_val = np.max(np.abs(waveform))
            if max_val > 0:
                waveform = waveform / max_val * amplitude_scale

            # Convert to 16-bit PCM
            pcm_data = np.clip(waveform * 32767, -32768, 32767).astype(np.int16)

            # Write WAV file
            with wave.open(output_path, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_data.tobytes())

            return {
                "success": True,
                "file_path": output_path,
                "format": "wav",
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": 1,
                "bit_depth": 16,
                "file_size_bytes": num_samples * 2 + 44,  # PCM data + WAV header
                "description": (
                    f"WAV file: {duration}s, {sample_rate} Hz, "
                    f"16-bit mono → {output_path}"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def music_function_info(
        expression: str,
    ) -> dict[str, Any]:
        """
        Analyze a music function and return its symbolic properties.

        Provides the LaTeX representation, symbols used, expression type,
        and whether it's periodic. Useful for understanding and documenting
        the mathematical structure of a music function.

        Args:
            expression: SymPy expression in terms of 't'

        Returns:
            Symbolic analysis: LaTeX, free symbols, periodicity info

        Examples:
            music_function_info("sin(2*pi*440*t) + 0.5*sin(2*pi*880*t)")
            → LaTeX, symbols: {t}, function type: sum of sinusoids
        """
        try:
            expr_clean = expression.replace("^", "**")
            sympy_expr = parse_expr(expr_clean, transformations=TRANSFORMATIONS)

            free_syms = sorted(str(s) for s in sympy_expr.free_symbols)

            # Analyze the expression structure
            t = sp.Symbol("t")
            is_sum = isinstance(sympy_expr, sp.Add)
            is_piecewise = isinstance(sympy_expr, sp.Piecewise)
            terms = sympy_expr.as_ordered_terms() if is_sum else [sympy_expr]
            num_terms = len(terms)

            # Try to detect periodicity
            period = None
            try:
                if t in sympy_expr.free_symbols:
                    period_result = sp.periodicity(sympy_expr, t)
                    if period_result is not None:
                        period = str(period_result)
            except Exception:
                pass

            expr_type = "piecewise" if is_piecewise else ("sum" if is_sum else "single_term")

            return {
                "success": True,
                "expression": str(sympy_expr),
                "latex": sp.latex(sympy_expr),
                "free_symbols": free_syms,
                "num_terms": num_terms,
                "expression_type": expr_type,
                "period": period,
                "is_periodic": period is not None,
                "description": (
                    f"Music function: {num_terms} term(s), "
                    f"symbols: {free_syms}, "
                    f"periodic: {period is not None}"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
