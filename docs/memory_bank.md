# Memory Bank & Decision Log

This document records decisions made during development, specifically logging approaches, strategies, or features we decided *not* to use and the reasons why. This prevents repeating past mistakes and revisiting discarded paths.

## Logging Format

### 🟢 [Feature/Decision Name]
- **Date**: [YYYY-MM-DD]
- **Context**: [Briefly describe the problem we were solving]
- **Decision**: [What we decided and what we explicitly decided *not* to do]
- **Reasoning (Why rejected)**: [Why the alternative was discarded]
- **Impact**: [What this means for the project]

---

## Log Entries

### 🟢 [Hugging Face API Router Migration & Free Tier Viability]
- **Date**: 2026-02-25
- **Context**: Hugging Face's legacy serverless endpoints (`api-inference.huggingface.co`) started persistently returning HTTP `410 Gone` errors. We migrated to the new active router: `router.huggingface.co/hf-inference/models/`.
- **Decision**: After migrating to the new URL, extensive testing revealed that *all* standard free-tier models (Mistral, Llama-3, Qwen, Zephyr, DialoGPT, Flan-T5, Gemma) STILL systematically return `404 Not Found` or `410 Gone` for unbilled accounts. We definitively concluded that **the Hugging Face Free Tier Inference API is no longer viable for reliable Agent NLP hosting.**
- **Reasoning (Why rejected)**: Hugging Face has aggressively locked down free model routing. Finding a single model that stays active for more than a day without an Enterprise PRO token ($9/mo) is impossible. We reject spending further engineering time on Hugging Face API free-layer workarounds.
- **Impact**: We have entirely stripped HuggingFace from the codebase and transitioned to **Ollama** for stable, free, offline local inference. The `LLMAgent` now uses the `ollama` python client to communicate with local models (e.g., `mistral`).

---

### 🟢 [Local LLM Inference with Ollama]
- **Date**: 2026-02-26
- **Context**: Relying on external APIs (like Hugging Face) for agent decision-making introduced latency, rate limits, and instability during sandbox simulations.
- **Decision**: We integrated `ollama` as the primary LLM backend for local agents, specifically pulling the `mistral` model, and updated `LLMAgent` to use the official Python client. 
- **Reasoning (Why rejected)**: Cloud inference APIs were rejected due to costs, network unreliability, and unexpected API failures. Local execution is free, stable, offline, and ideal for our continuous sandbox simulation architecture.
- **Impact**: The system now runs entirely locally. Agents use `ollama.chat()` for decisions, guaranteeing zero API failures or rate limits during multi-agent simulations.

---

### 🟢 [Advanced Simulation Visualization & Agent Reasoning]
- **Date**: 2026-02-26
- **Context**: The existing UI was a basic play-by-play timeline with minimal analytics. We needed much richer visualization to analyze agent behavior and make the project look production-grade.
- **Decision**: We rebuilt the entire `frontend/index.html` with: Chart.js price-over-time graph (buyer vs seller trajectories), a 4-metric dashboard (turns, final price, efficiency score, loop detection), session-level aggregate analytics (success rate, total runs, avg turns, deadlocks), and an enhanced decision timeline with per-step agent reasoning. We also added a `reasoning` field to the LLM prompt, `NegotiationMessage` model, and the agent's JSON output format.
- **Reasoning (Why rejected)**: Simple table-based or text-only displays were rejected as they don't convey negotiation dynamics (convergence, deadlocks, strategy shifts). Chart.js was chosen over D3.js for simplicity and CDN availability. We kept the UI as a single `index.html` file (no build step) for maximum portability.
- **Impact**: The frontend is now a complete analytics dashboard. Agent decisions include human-readable reasoning, making simulations interpretable and debuggable.

---

### 🟢 [Failure Taxonomy Engine — Research-Grade Failure Detection]
- **Date**: 2026-02-26
- **Context**: The mediator only detected simple loops (same price repeated). We needed a comprehensive failure classification system to analyze *why* negotiations fail, not just *that* they fail.
- **Decision**: Built `metrics/failure_detector.py` with 5 failure detectors (loop_failure, deadlock, irrational_concession, invalid_action, protocol_violation). Integrated into the Mediator as a post-simulation analysis pass, surfaced in the API output as `failure_report`, and rendered in the frontend as a risk-scored failure analysis panel. Kept the Mediator's existing rule-based loop halt logic intact; the FailureDetector is an additive analytical layer, not a replacement.
- **Reasoning (Why rejected)**: We considered making the FailureDetector a real-time halt mechanism (stopping the sim on any failure), but rejected it because many failures (like irrational concessions) are interesting to observe playing out. The detector is diagnostic, not prescriptive.
- **Impact**: Every simulation now produces a structured failure report with risk scoring, enabling research-level analysis of agent behavior patterns.

---

### 🟢 [Simulation Config System — Experiment-Ready Configuration]
- **Date**: 2026-02-26
- **Context**: Simulations used fixed settings. Every experiment required code changes. We needed a config system to make experiments repeatable and tweakable from the UI.
- **Decision**: Built `configs/simulation_config.py` with Pydantic models for `SimulationConfig`, `AgentConfig`, `StrategyType`, `RiskLevel`, and `NegotiationStyle`. Config values generate behavioral LLM prompt modifiers (strategy/risk/style sentences) injected at runtime. Temperature is passed to Ollama's `options`. Config snapshot included in API output. Frontend has collapsible "Advanced Config" panel with dropdowns and temperature slider. Added `/config/options` API endpoint for dynamic dropdown population.
- **Reasoning (Why rejected)**: YAML/TOML config files were considered but rejected since the config needs to be set per-simulation from the UI, not per-deployment. Environment variables were rejected for the same reason.
- **Impact**: Experiments can now be configured entirely from the browser. Strategy/risk/style combinations create distinct agent behaviors without code changes.

---

### 🟢 [OpenTelemetry Logging System — Research-Grade Telemetry]
- **Date**: 2026-02-26
- **Context**: No structured observability existed. We needed to measure decision latency, token usage, model errors, and negotiation complexity — the metrics real agent research systems track.
- **Decision**: Built `telemetry_module/telemetry.py` using OpenTelemetry SDK with a custom `TelemetryCollector` for in-memory aggregation. OTel counters (LLM calls, errors, fallbacks) and histograms (latency, tokens, complexity) feed the standard OTel pipeline. The collector provides per-simulation and global metric summaries via `/telemetry` API. Initially named the package `logging/` but renamed to `telemetry_module/` to avoid shadowing Python's built-in `logging`.
- **Reasoning (Why rejected)**: Pure OTel exporters (Jaeger, Prometheus) were considered but rejected since they require external infrastructure. The in-memory collector gives immediate API-accessible metrics with zero setup.
- **Impact**: Every agent decision now has latency, token count, and error tracking. Cross-session P95/max latency and error rates enable real research-grade analysis.

---

### 🟢 [Agent Strategy System — Pluggable Strategy Modules]
- **Date**: 2026-02-26
- **Context**: Strategy behavior was previously just a prompt string from config. We needed actual strategy modules with both LLM prompts and fallback logic to enable proper strategy experiments.
- **Decision**: Built `agents/strategies/` package with `BaseStrategy` abstract class defining `get_system_prompt()`, `compute_fallback_action()`, and `concession_rate`. Three implementations: `AggressiveStrategy` (5%), `BalancedStrategy` (10%), `ConservativeStrategy` (20%). Registry with aliases maps config enum values to strategy instances. Updated `LLMAgent` to load strategies via `get_strategy()` and use them for both LLM prompt injection and programmatic fallback.
- **Impact**: Strategy experiments are now possible: aggressive-vs-conservative completes in 3 turns (fast concession), aggressive-vs-aggressive takes longer. New strategies can be added by creating a new file and adding to the registry.

---

### 🟢 [Dataset Export System — Simulation Data Generator]
- **Date**: 2026-02-26
- **Context**: Simulation data was trapped in memory/API responses. We needed an export pipeline to turn the sandbox into a reusable dataset generator for research.
- **Decision**: Built `metrics/dataset_exporter.py` that flattens replay data into one row per decision step with 20 columns (sim_id, status, turns, final_price, config fields, failure metrics, telemetry metrics, per-step action data). Added `GET /dataset/export?format=json|csv` endpoint with Content-Disposition header for CSV downloads. Frontend sidebar has export buttons with download status feedback.
- **Impact**: Every simulation run can now be exported as structured research data. CSV files can be loaded directly into pandas/R for analysis.

---

### 🟢 [Tournament Engine & Global Leaderboard — Automated Benchmarking]
- **Date**: 2026-02-26
- **Context**: We needed a way to objectively compare agent strategies and models over many runs to observe emergent behaviors and performance trends.
- **Decision**: Implemented a `TournamentRunner` that performs round-robin matchups between all active strategies. Created a `Leaderboard` system with JSON persistence (`data/leaderboard.json`).
- **Reasoning (Why rejected)**: Initially attempted to use strictly typed Pydantic models for the tournament API, but rejected this in favor of a `Dict`-based request handler due to persistent `PydanticUserError` (not fully defined) issues specifically encountered in the Windows FastAPI/Uvicorn environment during runtime model evaluation. 
### 🟢 [Red Team Adversarial Engine — Stress Testing]
- **Date**: 2026-02-26
- **Context**: We need to verify that the `FailureDetector` can handle malicious or irrational actor inputs and observe how different agent strategies react to deception.
- **Decision**: Implemented a `RedTeamAgent` as a "Man-in-the-Middle" disruptor. It intercepts and corrupts actions (wrong numbers, fake constraints, protocol violations) based on a configurable probability.
- **Impact**: Allows for adversarial benchmarking. Strategies can now be "Red Teamed" to see if they concede irrationally to fake pressure or break under malformed protocol inputs.

### 🟢 [Experiment Research Engine — Grid Search API]
- **Date**: 2026-02-26
- **Context**: To turn the sandbox into a research engine, we needed a way to automate hundreds of simulations while varying specific hyperparameters (Grid Search).
- **Decision**: Implemented `ExperimentRunner` in a dedicated `experiments/` module. It performs Cartesian product sweeps over strategies and temperatures.
- **Impact**: Enables scientific study of negotiation behavior. Users can now click one button to see how `temperature` affects win rates across all strategy combinations.

*(No more entries. Add entries here when evaluating features, dependencies, or architectural choices.)*
