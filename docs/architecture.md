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
- `world/`: Environment and world state definitions for the agents.
- `scenarios/`: Specific simulation scenarios and workflows.
- `metrics/`: Analytics and performance tracking of agent outcomes.
- `frontend/`: UI components (if applicable in the future).
- `docs/`: Project documentation, architecture, and memory bank.

## Features
- **Core API Server**: A basic FastAPI server running on `backend/main.py` with app configurations handled via Pydantic in `backend/config.py`. 
- **World Manager Engine**: The core simulation engine defined in `world/world_manager.py` that handles starting simulations, creating agents, and managing the core negotiation loop between Agent A, Agent B, and the Mediator based on a provided scenario.
- **Negotiation Protocol**: A simple rule-based message format defined in `world/messages.py` using Pydantic, supporting `offer`, `counter_offer`, `accept`, and `reject` types to structure interactions.
- **Mediator Engine**: Enforces simulation logic in `world/mediator.py`. Capable of halting the loop if agents exceed the 20-turn maximum, produce invalid messages, or get mathematically stuck in repeating loops.
- **Metrics Storage**: SQLAlchemy ORM for storing simulation results in a local SQLite database (`sandbox_metrics.db`), defined in `metrics/storage.py`. Stores simulation ID, agent names, outcome status, turn count, and final agreement price to build a historical dataset.
- **Scenario Engine**: A flexible framework defined in `scenarios/base_scenario.py` allowing extensible simulation types.
  - `PriceNegotiationScenario`: Implements the base rules for a 1-on-1 negotiation, overriding agent parameters and initial state logic.
- **Simulation API**: Exposes four key endpoints in `backend/main.py` via FastAPI to interact with the engine.
  - `POST /simulation/start`: Kicks off a new specified negotiation scenario (e.g., `scenario_type="price_negotiation"`) returning live results.
  - `POST /simulation/batch`: Runs a specified scenario back-to-back `N` times (e.g., `runs=100`) and returns aggregated analytics (success rate, deadlocks, average turns, average price).
  - `GET /simulation/replay`: Returns all historical runs loaded into memory with their full sequential play-by-play steps.
  - `GET /simulation/{id}`: Retrieves the full history and details of a specific simulation run.
- **Replay System**: Built-in tracking inside `world/world_manager.py` that records the precise agent actions, capturing the actor, turn number, and raw action state in a linear `steps` array, which is then exposed in the API outputs.
- **Browser UI**: A responsive, vanilla HTML/JS/CSS frontend located in `frontend/index.html`. It is statically mounted and served via FastAPI at the `/play` endpoint. Features include: a simulation control panel with buyer/seller parameters, a past-run history sidebar, a **Chart.js price-over-time graph** (buyer vs seller price trajectories), a **metrics panel** (total turns, final price, efficiency score, loop detection), **session-level aggregate analytics** (success rate, total runs, average turns, deadlocks), and a **decision timeline** that displays each agent's action, price, and AI reasoning step-by-step. Uses a premium dark glassmorphism design with micro-animations.
- **Agent Implementations**: Multiple types of agents exist in `agents/`, all inheriting from `BaseAgent`.
  - **Rule-based Agents**: `BuyerAgent` and `SellerAgent` capable of deterministic simple negotiation logic (offer, counter, accept).
  - **LLM-based Agents**: `LLMAgent` located in `agents/llm_agent.py` dynamically builds prompt contexts (price, budget constraints), constructs an action history, and calls the local Ollama inference engine (currently configured to use the `mistral` model). Returns structured JSON with `type`, `price`, and `reasoning` fields. Enforces strict JSON return parsers with programmatic fallback on failure.
  - **Runtime Execution**: The `world_manager.py` defaults to running `LLMBuyerAgent` and `LLMSellerAgent` to demonstrate the active AI capabilities.
- **Mediator Engine**: Enforces simulation logic in `world/mediator.py`. Crucially, this remains **strictly rule-based**. Even when LLMs propose actions, the Mediator validates formats, halts infinite loops, and acts as the unbribable referee before the World Manager executes state changes.
- **Failure Detection Engine**: A research-grade failure taxonomy system in `metrics/failure_detector.py` that performs post-simulation analysis across 5 failure categories: `loop_failure` (identical/stagnant prices), `deadlock` (diverging price gaps), `irrational_concession` (agents acting against own interests), `invalid_action` (malformed messages), and `protocol_violation` (rule-breaking sequences). Produces a risk score (0-100) and detailed per-turn failure cards displayed in the frontend.
- **Simulation Config System**: `configs/simulation_config.py` provides a Pydantic-based configuration model (`SimulationConfig`) with per-agent `AgentConfig` for strategy (`aggressive/cooperative/analytical/adaptive`), risk level (`low/medium/high`), LLM temperature (0-2), negotiation style (`formal/casual/competitive/collaborative`), and model selection. Config values are injected into LLM prompts as behavioral modifiers and included as a snapshot in simulation output. Frontend exposes collapsible Advanced Config controls.
- **OpenTelemetry Logging System**: `telemetry_module/telemetry.py` provides research-grade structured telemetry using OpenTelemetry SDK. Tracks decision latency (per-agent, avg, P95, max), token usage, model errors/fallbacks, and negotiation complexity scores. `TelemetryCollector` aggregates per-simulation and global metrics. Exposed via `/telemetry` API endpoint and rendered in the frontend's 📡 Telemetry panel with latency bar visualizations.
- **Agent Strategy System**: Pluggable strategy modules in `agents/strategies/` with `BaseStrategy` abstract class, three implementations (aggressive 5% concession, balanced 10%, conservative 20%), and a registry with aliases. Strategies provide both LLM system prompts and programmatic fallback logic, replacing the previous hardcoded fallback. Enables strategy experiments from the UI.
- **Dataset Export System**: `metrics/dataset_exporter.py` flattens simulation replays into tabular rows (one per decision step) with 20 columns spanning simulation metadata, config, failure analysis, telemetry, and per-step actions. Exposed via `GET /dataset/export?format=json|csv`. Frontend sidebar has JSON/CSV download buttons. Turns the sandbox into a negotiation dataset generator.

