# Project Architecture

## Overview
The Agent Sandbox is a multi-agent system backend built using FastAPI.

## Tech Stack
- **Backend framework**: FastAPI
- **Server ASGI**: Uvicorn
- **Data validation**: Pydantic
- **Database ORM**: SQLAlchemy (setup pending)

## Modular Structure
- `backend/`: FastApi backend core application logic, settings, and main entries.
- `agents/`: Agent implementations and behaviors.
  - `agents/providers/`: Pluggable LLM provider implementations (Ollama, OpenAI, Gemini, Groq).
- `world/`: Environment and world state definitions for the agents.
- `scenarios/`: Specific simulation scenarios and workflows.
- `metrics/`: Analytics and performance tracking of agent outcomes.
- `tournaments/`: Round-robin tournament runner and leaderboard logic.
- `docs/`: Project documentation, architecture, and memory bank.

## Features
- **Core API Server**: A basic FastAPI server running on `backend/main.py` with app configurations handled via Pydantic in `backend/config.py`. 
- **World Manager Engine**: The core simulation engine defined in `world/world_manager.py`. It has been extended to support **N-agent Multi-Party Negotiations** by handling a dynamic list of participants. It manages the core negotiation loop, arbitrating between any number of Buyers and Sellers based on the provided scenario.
- **Negotiation Protocol**: A standardized, ACP-like (Agent Communication Protocol) message format defined in `world/messages.py`. It supports granular action types including `proposal`, `counter_proposal`, `acceptance`, `rejection`, `information`, and `challenge`. Every message explicitly includes `sender` and `receiver` fields to ensure interoperability and support for multi-agent environments.
- **Mediator Engine**: Enforces simulation logic in `world/mediator.py`. Validates ACP message schemas, handles turn-taking, and halts the loop if agents exceed the 20-turn maximum, produce invalid/malformed protocol messages, or get mathematically stuck in repeating loops.
- **Metrics Storage**: SQLAlchemy ORM for storing simulation results in a local SQLite database (`sandbox_metrics_v2.db`), defined in `metrics/storage.py`. 
- **High-Concurrency Optimization (The "Barista" Solution)**: To support 20+ simultaneous workers without database locking, the backend uses **SQLite WAL (Write-Ahead Logging) Mode**. This enables a "Multi-Lane Highway" for data, allowing multiple reads and writes concurrently. It also includes an increased `busy_timeout` of 30 seconds to handle high-frequency job acquisition.
- **Scenario Engine**: A flexible framework defined in `scenarios/base_scenario.py` allowing extensible simulation types.
  - `PriceNegotiationScenario`: Implements the base rules for a standardized 1-on-1 negotiation.
  - `MultiVendorNegotiationScenario`: Implements a 1-Buyer vs N-Vendor scenario, enabling the study of competitive undercutting and price wars.
- **Simulation API**: Exposes four key endpoints in `backend/main.py` via FastAPI to interact with the engine.
  - `POST /simulation/start`: Kicks off a new specified negotiation scenario (e.g., `scenario_type="price_negotiation"`) returning live results.
  - `POST /simulation/batch`: Runs a specified scenario back-to-back `N` times (e.g., `runs=100`) and returns aggregated analytics (success rate, deadlocks, average turns, average price).
  - `GET /simulation/replay`: Returns all historical runs loaded into memory with their full sequential play-by-play steps.
  - `GET /simulation/{id}`: Retrieves the full history and details of a specific simulation run.
  - `POST /scenario/create`: API for dynamically generating and persisting custom negotiation scenarios.
  - `GET /scenario/list`: Retrieves all available core and user-defined custom scenarios.
  - `GET /batch/{batch_id}/progress`: Returns real-time completion status, statistics, and ETA for a specific simulation batch.
- **Replay System**: Built-in tracking inside `world/world_manager.py` that records the precise agent actions, capturing the actor, turn number, and raw action state in a linear `steps` array, which is then exposed in the API outputs.
- **Browser UI**: A responsive, vanilla HTML/JS/CSS frontend located in `frontend/index.html`. It is statically mounted and served via FastAPI at the `/play` endpoint. Features include:
  - **Global Command Header**: Centralized navigation for Ecoystem Discovery, Performance Arena, and Intelligence Hub.
  - **Performance Analytics**: Chart.js price-over-time graphs, metrics panels (efficiency scores, loop detection).
  - **Decision Timeline**: Sequential display of each agent's action, price, and AI reasoning.
  - **System Robustness Overlay**: Specialized modal for adversarial settings (Attack Probability), keeping the main controls focused.
  - **Design Style**: Premium "Midnight Slate" glassmorphism with emoji-free professional aesthetics and micro-animations.
- **Agent Implementations**: Multiple types of agents exist in `agents/`, all inheriting from `BaseAgent`.
  - **Rule-based Agents**: `BuyerAgent` and `SellerAgent` capable of deterministic simple negotiation logic (offer, counter, accept).
  - **LLM-based Agents**: `LLMAgent` located in `agents/llm_agent.py` dynamically builds prompt contexts (price, budget constraints), constructs an action history, and calls the **Provider System** for inference. It is now completely provider-agnostic, supporting both local and cloud-based foundation models. Returns structured ACP-compliant JSON with `sender`, `receiver`, `type`, `price`, and `reasoning` fields. Includes a normalization layer to map legacy terms (e.g., "offer") to the standard protocol.
  - **Runtime Execution**: The `world_manager.py` defaults to running `LLMBuyerAgent` and `LLMSellerAgent` to demonstrate the active AI capabilities.
- **Mediator Engine**: Enforces simulation logic in `world/mediator.py`. Crucially, this remains **strictly rule-based**. Even when LLMs propose actions, the Mediator validates formats, halts infinite loops, and acts as the unbribable referee before the World Manager executes state changes.
- **Failure Detection Engine**: A research-grade failure taxonomy system in `metrics/failure_detector.py` that performs post-simulation analysis across 5 failure categories: `loop_failure` (identical/stagnant prices), `deadlock` (diverging price gaps), `irrational_concession` (agents acting against own interests), `invalid_action` (malformed messages), and `protocol_violation` (rule-breaking sequences). Produces a risk score (0-100) and detailed per-turn failure cards displayed in the frontend.
- **Multi-Provider LLM System**: A pluggable architecture in `agents/providers/` that abstracts LLM interactions.
  - `BaseProvider`: Defines a standard chat interface and model discovery.
  - `ProviderFactory`: Manages lazy-loading of providers, ensuring the system remains stable even if cloud SDKs (OpenAI, Gemini) are missing.
  - **Supported Backends**: Ollama (local), OpenAI, Google Gemini, and Groq (high-speed).
- **Simulation Config System**: `configs/simulation_config.py` provides a Pydantic-based configuration model (`SimulationConfig`) with per-agent `AgentConfig` for strategy (`aggressive/cooperative/analytical/adaptive`), risk level (`low/medium/high`), LLM temperature (0-2), negotiation style (`formal/casual/competitive/collaborative`), seed (for reproducibility), and model selection (prefixed with provider, e.g., `openai:gpt-4o`). Config values are injected into LLM prompts as behavioral modifiers and included as a snapshot in simulation output. Frontend exposes collapsible Advanced Config controls.
- **OpenTelemetry Logging System**: `telemetry_module/telemetry.py` provides research-grade structured telemetry using OpenTelemetry SDK. Tracks decision latency (per-agent, avg, P95, max), token usage, model errors/fallbacks, and negotiation complexity scores. `TelemetryCollector` aggregates per-simulation and global metrics. Exposed via `/telemetry` API endpoint and rendered in the frontend's Telemetry panel with latency bar visualizations.
- **Agent Strategy System**: Pluggable strategy modules in `agents/strategies/` with `BaseStrategy` abstract class, three implementations (aggressive 5% concession, balanced 10%, conservative 20%), and a registry with aliases. Strategies provide both LLM system prompts and programmatic fallback logic, replacing the previous hardcoded fallback. Enables strategy experiments from the UI.
- **Dataset Export System**: `metrics/dataset_exporter.py` flattens simulation replays into tabular rows (one per decision step) with 20 columns spanning simulation metadata, config, failure analysis, telemetry, and per-step actions. Exposed via `GET /dataset/export?format=json|csv`. Frontend sidebar has JSON/CSV download buttons. Turns the sandbox into a negotiation dataset generator.
- **Agent Cards & Discovery System**: Machine-readable agent descriptors in `agents/cards/` (JSON). `agents/card_loader.py` provides semantic discovery and cross-agent compatibility checking (protocol, I/O schema, capabilities). Discovery area in the frontend automatically surface available agents and simulation-readiness reports. This aligns with emerging industry standards for agentic ecosystems.
- **Tournament Engine & Intelligence Hub**: Automated benchmarking system in `tournaments/`. 
  - `TournamentRunner`: Orchestrates round-robin simulations between multiple strategies and models. 
  - `Leaderboard`: Persistent JSON-based storage (`data/leaderboard.json`) calculating win rates and aggregate performance. 
  - **Intelligence Hub View**: A dedicated, full-screen dashboard in the UI for visualizing global strategy effectiveness, model benchmarks, and detailed ranking metrics.
- **Red Team Adversarial Engine**: A specialized `RedTeamAgent` that acts as a "Man-in-the-Middle" during simulations. It disrupts negotiations by injecting wrong numbers, fake constraints, or protocol violations based on a configurable attack probability. This allows stress-testing of the `FailureDetector` and observation of how strategies handle deception.
- **Experiment Research Engine**: A high-level orchestrator (`ExperimentRunner`) that performs complex parameter sweeps (Grid Search) across multiple variables (temperature, strategies, models). Results are aggregated into structured JSON datasets for scientific analysis of model convergence and behavior.
- **Simulation Scheduler**: A persistent, thread-safe queue system in `simulation_queue/` that enables long-running background experiments and cloud acceleration.
  - `SimulationJob`: Database model for tracking job state (pending, running, completed, failed).
  - `SimulationWorker`: Multi-threaded background process that acquires jobs atomically to prevent duplication.
  - **Remote Worker API**: New endpoints (`/queue/acquire`, `/queue/submit`) in `backend/main.py` allowing cloud instances (Google Colab) to act as horizontally scaled workers.
  - Endpoints: `POST /simulation/schedule`, `GET /queue/status`, `GET /queue/recent`.
- **Performance Arena**: A competitive benchmarking mode with a "Versus" clashing layout.
  - **Model vs Model**: Supports independent foundation model selection for both Buyer and Seller, enabling direct cross-model and cross-provider benchmarking.
  - **Per-Fighter Config**: Isolated strategy, risk, model, and provider configuration panels for each challenger.
  - **Competitive Metrics**: Tracks Strategy-vs-Strategy and Model-vs-Model win rates via the Intelligence Hub.
- **Scenario Architect System**: A platform-tier feature enabling the dynamic design of negotiation environments.
  - **Dynamic Engine**: `scenarios/dynamic_scenario.py` provides a polymorphic container for runtime parameters (agent count, constraints, goals).
  - **Architect UI**: A full-screen dashboard tab in the frontend for visual scenario design and one-click deployment.
  - **Persistent Storage**: `data/scenarios.json` acts as the user's private library of custom-built research environments.

