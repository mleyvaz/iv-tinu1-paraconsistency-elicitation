# IV-TINU1 — Section 9 empirical code and data

Code and raw data for the empirical Section 9 ("Declared-Order Instantiation") of *Interval Neutrosophic (T, I, N, U₁, …, Uₙ, F) Multi-Uncertainty Set/Logic, the Partial Consistency / Partial Paraconsistency Hierarchy, and a Total-Order Proof for the Interval Ranking Cascade"* (Smarandache & Leyva-Vázquez). Sections 1–8 of the paper (Smarandache's formal extension) are pure mathematics and do not depend on anything in this repository. This repo holds only the elicitation scripts, raw results, and figures for the feasibility-check pilots; the paper manuscript itself is not included here.

## Contents

- `experiment/` — pilot scripts and raw results, in order:
  - `run_pilot.py` / `analyze_pilot.py` — pilot 1 (8 items, Arm 1 + Arm 2, single wording, 2 OpenRouter models)
  - `run_pilot2.py` / `analyze_pilot2.py` — pilot 2 (10 items, Arm 1 only, fixed I-probe wording, paraphrase + auditor crossover)
  - `run_pilot3.py` / `analyze_pilot3.py` — pilot 3 (forced-choice redesign for U₁–U₅, mirroring Jev's own `Choice` type)
  - `run_pilot4_jev.mjs` / `analyze_pilot4.py` — pilot 4 (Jev, single call per letter — **superseded by pilot 5**, kept for the record)
  - `check_jev_determinism.mjs` — 5-call repeat check that found Jev's calibrated outputs are not deterministic
  - `run_pilot5_jev_repeated.mjs` / `analyze_pilot5.py` — pilot 5 (Jev, k=5 repeats per letter — the reliable reading of Jev)
- `figures/` — `make_figures.py` and the two PNGs it generates, referenced from the paper's §3.3 and §9.6.

## Reproducing

Pilots 1–3 need `OPENROUTER_API_KEY` in the environment and Python 3 (`requests`). Pilot 4/5 and the determinism check need `AI_GATEWAY_API_KEY` (Vercel AI Gateway, TypeSafe AI's `typesafe-ai/jev` model) and Node.js with the `ai` package (`npm install ai @ai-sdk/gateway`). Each `analyze_*.py` reads its corresponding `*_raw_results.json` and recomputes sup(letter) and the declared order per Definition 9 of the paper.

## Status

All results here are feasibility-check pilots (n=8–10 items, not the pre-registered n≈100–200 study referenced in the paper). See the paper's §9.5–9.6 for the full discussion and caveats.
