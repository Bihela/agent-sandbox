# Agent Sandbox

A professional research-grade sandbox for simulating, benchmarking, and red-teaming multi-agent LLM negotiations.

## Overview
Agent Sandbox is a modular, high-performance ecosystem designed for studying emergent behaviors in LLM-based negotiation. It decouples agent logic from the simulation environment, allowing researchers to test various models, strategies, and adversarial scenarios in a controlled, observable space.

## Features
- **Model-Multiversal**: Pluggable provider system supporting Ollama (local), OpenAI, Gemini, and Groq.
- **Performance Arena**: Head-to-head benchmarking for comparing foundation model negotiation capabilities.
- **Scenario Architect**: Design and deploy custom negotiation environments via a dynamic UI.
- **Research-Grade Analytics**: Automated failure taxonomy, OpenTelemetry metrics, and one-click dataset exports.
- **Adversarial Testing**: Built-in Red Team agent to stress-test strategy robustness.

---

## Quick Start (One Command)

The fastest way to get started is using Docker Compose, which spins up the Backend and a local Ollama instance automatically:

```bash
docker-compose up -d
```
Then open `http://localhost:8000/play/` in your browser.

> [!NOTE]
> If running for the first time, you'll need to pull a model in the Ollama container:
> `docker exec -it agent-sandbox-ollama-1 ollama pull mistral`

---

## The Playground

Ready to see agents clash? Follow these steps for a 1-click Tournament:

1. Open the UI and navigate to the **Performance Arena**.
2. Select your models (e.g., `openai:gpt-4o` vs `ollama:mistral`).
3. Click **Start Battle**.
4. Watch the price trajectories and reasoning play out in real-time!

---

## Model Providers

Agent Sandbox is provider-agnostic. You can switch between:
- **Ollama** (Local/Default)
- **OpenAI** (GPT-4o, GPT-3.5)
- **Google Gemini** (1.5 Pro/Flash)
- **Groq** (Fast Llama/Mixtral)

See [Provider Guide](docs/providers.md) for setup instructions.

---

## Project Structure
- `agents/`: Agent implementations and behaviors.
- `backend/`: FastAPI application core.
- `world/`: Simulation environment and mediation logic.
- `scenarios/`: Negotiation scenario definitions.
- `metrics/`: Failure detection and dataset export tools.
- `telemetry_module/`: OpenTelemetry tracking.
- `tournaments/`: Automated benchmarking and leaderboard logic.

---

## Documentation
- [Architecture Overview](docs/architecture.md)
- [Research Decisions](docs/memory_bank.md)
- [Model Provider Guide](docs/providers.md)

---

## Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License
Released under the [MIT License](LICENSE).
