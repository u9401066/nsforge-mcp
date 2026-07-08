# 🛠️ NSForge Tool Reference

Complete reference for all **91 MCP tools** across **11 modules**.

> This page is the single source of truth for the tool surface, linked from both
> [README (English)](../README.md) and [README (繁體中文)](../README.zh-TW.md).
> The machine-readable manifest lives at [`docs/agent/capabilities.json`](agent/capabilities.json).

| Module | Count | What it does |
| ------ | :---: | ------------ |
| [🔥 Derivation engine](#-derivation-engine-31) | 31 | Stateful derivation sessions: compose, step, track, store |
| [🧭 Task orchestration](#-task-orchestration-l2l3-3) | 3 | Declarative task spec → reification-ladder run / explore |
| [🧭 Suggester](#-suggester-1) | 1 | Retrieval-augmented next-step ranking |
| [🔢 Calculation](#-calculation-12) | 12 | Limits, series, sums, inequalities, probability, numerics |
| [🔣 Advanced algebra & transforms](#-advanced-algebra--transforms-14) | 14 | Expand/factor/apart… + Laplace/Fourier transforms |
| [✅ Verification](#-verification-6) | 6 | Equality, derivative, integral, solution, dimensions |
| [📝 Expression](#-expression-3) | 3 | Parse, validate, extract symbols |
| [💻 Code generation](#-code-generation-4) | 4 | Python function, LaTeX, report, standalone script |
| [🌐 Formula search](#-formula-search-6) | 6 | Wikidata, BioModels, SciPy constants |
| [🎵 Music](#-music-9) | 9 | Symbolic tones → waveform, spectrum, WAV |
| [🧩 Runtime self-description](#-runtime-self-description-meta-2) | 2 | Live server introspection: health, manifest |

---

## 🔥 Derivation engine (31)

Stateful, resumable derivation sessions — the "Forge" in NSForge. Each step can
carry human insight (`notes`) and is tracked with provenance.

### Session lifecycle

| Tool | Purpose |
| ---- | ------- |
| `derivation_start` | Start a new derivation session |
| `derivation_resume` | Resume a paused session |
| `derivation_status` | Current session status |
| `derivation_list_sessions` | List all sessions |
| `derivation_show` | Display the current formula (like SymPy's `print_latex_expression`) |
| `derivation_complete` | Complete and auto-save the derivation |
| `derivation_abort` | Abort the current session |

### Deriving

| Tool | Purpose |
| ---- | ------- |
| `derivation_load_formula` | Load a base formula into the session |
| `derivation_substitute` | Substitution (records human insight) |
| `derivation_simplify` | Simplify the current expression |
| `derivation_solve_for` | Solve for a variable |
| `derivation_differentiate` | Differentiate the current expression |
| `derivation_integrate` | Integrate the current expression |
| `derivation_record_step` | Record a step (from SymPy-MCP or manual) |
| `derivation_add_note` | Add a human insight (not a computation step) |

### Step control (CRUD)

| Tool | Purpose |
| ---- | ------- |
| `derivation_get_steps` | Get all steps |
| `derivation_get_step` | Get a single step's details |
| `derivation_update_step` | Update a step's metadata (not the expression) |
| `derivation_delete_step` | Delete the last step |
| `derivation_rollback` | ⚡ Roll back to any step |
| `derivation_insert_note` | Insert a note at a position |

### Repository (saved derivations)

| Tool | Purpose |
| ---- | ------- |
| `derivation_list_saved` | List saved derivations |
| `derivation_get_saved` | Get a saved derivation |
| `derivation_search_saved` | Search saved derivations |
| `derivation_repository_stats` | Repository statistics |
| `derivation_update_saved` | Update saved metadata |
| `derivation_delete_saved` | Delete a saved derivation |

### Bridges (SymPy-MCP ↔ USolver)

| Tool | Purpose |
| ---- | ------- |
| `derivation_export_for_sympy` | Export session state to SymPy-MCP |
| `derivation_import_from_sympy` | Import a result back from SymPy-MCP |
| `derivation_handoff_status` | Show handoff status and options |
| `derivation_prepare_for_optimization` | Prepare a result for a solver (e.g. USolver) |

---

## 🧭 Task orchestration (L2/L3) (3)

Turn a declarative **Derivation Task Spec (DTS)** into a provenance-tagged run of
the reification ladder. See the [general-formula-exploration roadmap](general-formula-exploration-roadmap.md).

| Tool | Purpose |
| ---- | ------- |
| `task_plan` | Reify a DTS into an ordered plan of tool calls |
| `task_run` | Run the DTS through the ladder (concept → symbol → derivation → verify → code); optional hard `timeout_s` |
| `task_explore` | Branching search: run the base + every alternative, return all verified candidates ranked best-first |

---

## 🧭 Suggester (1)

| Tool | Purpose |
| ---- | ------- |
| `derivation_suggest_next` | Rank candidate next steps by relevance (retrieve-then-rank) |

---

## 🔢 Calculation (12)

| Tool | Purpose |
| ---- | ------- |
| `calculate_limit` | Limit of an expression |
| `calculate_series` | Taylor / Laurent series expansion |
| `calculate_summation` | Symbolic summation Σ |
| `solve_inequality` | Solve a single inequality |
| `solve_inequality_system` | Solve a system of inequalities (intersection) |
| `define_distribution` | Define a probability distribution |
| `distribution_stats` | Distribution statistics (mean, variance, skew) |
| `distribution_probability` | Probability P(condition) |
| `query_assumptions` | Query properties from assumptions |
| `refine_expression` | Simplify using assumptions |
| `evaluate_numeric` | Numerical evaluation |
| `symbolic_equal` | Symbolic equality check |

---

## 🔣 Advanced algebra & transforms (14)

| Tool | Purpose |
| ---- | ------- |
| `expand_expression` | Expand products: (x+1)² → x²+2x+1 |
| `factor_expression` | Factorize: x²−1 → (x−1)(x+1) |
| `collect_expression` | Collect terms by variable |
| `trigsimp_expression` | Trig simplify: sin²+cos² → 1 |
| `powsimp_expression` | Power simplify: x²·x³ → x⁵ |
| `radsimp_expression` | Radical simplify |
| `combsimp_expression` | Factorial/binomial simplify: n!/(n−2)! → n(n−1) |
| `apart_expression` | 🔥 Partial fractions (for inverse Laplace) |
| `cancel_expression` | Cancel common factors |
| `together_expression` | Combine fractions over a common denominator |
| `laplace_transform_expression` | 🔥 f(t) → F(s) for ODE solving |
| `inverse_laplace_transform_expression` | 🔥 F(s) → f(t) for multi-compartment PK |
| `fourier_transform_expression` | f(x) → F(k) frequency analysis |
| `inverse_fourier_transform_expression` | F(k) → f(x) signal reconstruction |

---

## ✅ Verification (6)

| Tool | Purpose |
| ---- | ------- |
| `verify_equality` | Verify two expressions are equal |
| `verify_derivative` | Verify a derivative by comparison |
| `verify_integral` | Verify an integral by differentiating |
| `verify_solution` | Verify a value satisfies an equation |
| `check_dimensions` | Dimensional consistency analysis |
| `reverse_verify` | Verify by applying the reverse operation |

---

## 📝 Expression (3)

| Tool | Purpose |
| ---- | ------- |
| `parse_expression` | Parse into SymPy-computable form |
| `validate_expression` | Validate syntax / correctness |
| `extract_symbols` | Extract symbols with inferred metadata |

---

## 💻 Code generation (4)

> ⚠️ These reify **verified** derivation steps — always compute/verify first.

| Tool | Purpose |
| ---- | ------- |
| `generate_python_function` | Python function from verified steps |
| `generate_latex_derivation` | LaTeX document |
| `generate_derivation_report` | Markdown report |
| `generate_sympy_script` | Standalone SymPy script |

---

## 🌐 Formula search (6)

Formulas are **inputs** (from open sources), not a hand-built catalog.

| Tool | Purpose |
| ---- | ------- |
| `formula_search` | 🔍 Unified search (Wikidata, BioModels, SciPy) |
| `formula_get` | 📄 Get formula details by ID |
| `formula_categories` | 📂 List available categories |
| `formula_pk_models` | 💊 PK models (1/2-compartment, Michaelis-Menten) |
| `formula_kinetic_laws` | ⚗️ Reaction kinetics from BioModels |
| `formula_constants` | 🔬 Physical constants (from SciPy) |

---

## 🎵 Music (9)

Music as symbolic functions of time — a fun demonstration of the symbolic core.

| Tool | Purpose |
| ---- | ------- |
| `music_note_to_frequency` | Note name → frequency (Hz) |
| `music_compose_tone` | Symbolic tone A·sin(2πft + φ) |
| `music_compose_chord` | Sum of tones into a chord |
| `music_compose_sequence` | Melody as a piecewise function over time |
| `music_function_info` | Analyze a music function's symbolic properties |
| `music_function_to_waveform` | Evaluate a function to waveform data |
| `music_plot_waveform` | Plot the time-domain waveform |
| `music_plot_spectrum` | Plot the frequency spectrum (FFT) |
| `music_generate_wav` | Generate a WAV file from a function |

---

## 🧩 Runtime self-description (meta) (2)

The MCP side of the agent harness — a connected agent introspects the live server without touching the repo.

| Tool | Purpose |
| ---- | ------- |
| `nsforge_health` | Liveness + inventory: name, version, tool count, engine versions |
| `nsforge_manifest` | The full capability manifest (tools, gates, commands, north star) |

---

<div align="center">

[← Back to README](../README.md) · [中文 README](../README.zh-TW.md) · [Capability manifest](agent/capabilities.json)

</div>
