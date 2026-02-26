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

*(No more entries. Add entries here when evaluating features, dependencies, or architectural choices.)*
