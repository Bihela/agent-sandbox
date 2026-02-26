"""
OpenTelemetry-based structured logging and tracing for the Agent Sandbox.

Provides:
  - Tracer: spans for decision latency, simulation lifecycle
  - Meter: counters/histograms for model errors, token usage, negotiation complexity
  - TelemetryCollector: in-memory collector that exposes metrics via API
"""

import time
from typing import Dict, List, Any, Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider


# ─── Provider Setup ───
trace_provider = TracerProvider()
trace.set_tracer_provider(trace_provider)

meter_provider = MeterProvider()
metrics.set_meter_provider(meter_provider)

# ─── Instruments ───
tracer = trace.get_tracer("agent-sandbox", "1.0.0")
meter = metrics.get_meter("agent-sandbox", "1.0.0")

# Counters
llm_call_counter = meter.create_counter(
    "llm.calls.total",
    description="Total LLM inference calls",
)
llm_error_counter = meter.create_counter(
    "llm.errors.total",
    description="Total LLM errors (fallback triggered)",
)
fallback_counter = meter.create_counter(
    "agent.fallback.total",
    description="Total programmatic fallback activations",
)
simulation_counter = meter.create_counter(
    "simulation.runs.total",
    description="Total simulation runs",
)

# Histograms
decision_latency = meter.create_histogram(
    "agent.decision.latency_ms",
    description="Agent decision latency in milliseconds",
    unit="ms",
)
token_usage_hist = meter.create_histogram(
    "llm.token.usage",
    description="Approximate token usage per LLM call",
    unit="tokens",
)
negotiation_complexity = meter.create_histogram(
    "simulation.negotiation.complexity",
    description="Negotiation complexity score (turns × unique_prices × price_range_ratio)",
)


class TelemetryCollector:
    """
    In-memory collector that aggregates telemetry data for API exposure.
    Works alongside OTel's native meters/tracers as a lightweight summary layer.
    """

    def __init__(self):
        self._events: List[Dict[str, Any]] = []
        self._sim_telemetry: Dict[str, Dict[str, Any]] = {}

    def record_event(self, event_type: str, data: dict):
        """Record a timestamped telemetry event."""
        self._events.append({
            "timestamp": time.time(),
            "type": event_type,
            **data,
        })

    def start_simulation_telemetry(self, sim_id: str):
        """Initialize telemetry tracking for a simulation."""
        self._sim_telemetry[sim_id] = {
            "start_time": time.time(),
            "agent_decisions": [],
            "total_llm_calls": 0,
            "total_errors": 0,
            "total_fallbacks": 0,
            "total_tokens": 0,
        }

    def record_decision(self, sim_id: str, agent: str, latency_ms: float,
                         tokens: int = 0, error: bool = False, fallback: bool = False,
                         model: str = ""):
        """Record an individual agent decision with metrics."""
        if sim_id not in self._sim_telemetry:
            return

        tel = self._sim_telemetry[sim_id]
        tel["agent_decisions"].append({
            "agent": agent,
            "latency_ms": round(latency_ms, 1),
            "tokens": tokens,
            "error": error,
            "fallback": fallback,
            "model": model,
        })
        tel["total_llm_calls"] += 1
        if error:
            tel["total_errors"] += 1
        if fallback:
            tel["total_fallbacks"] += 1
        tel["total_tokens"] += tokens

        # Feed OTel instruments
        attrs = {"agent": agent, "model": model}
        llm_call_counter.add(1, attrs)
        decision_latency.record(latency_ms, attrs)
        if tokens > 0:
            token_usage_hist.record(tokens, attrs)
        if error:
            llm_error_counter.add(1, attrs)
        if fallback:
            fallback_counter.add(1, attrs)

    def finalize_simulation(self, sim_id: str, turns: int, steps: list) -> dict:
        """Complete telemetry for a simulation and compute summary metrics."""
        if sim_id not in self._sim_telemetry:
            return {}

        tel = self._sim_telemetry[sim_id]
        elapsed = (time.time() - tel["start_time"]) * 1000  # ms

        # Compute negotiation complexity
        prices = [s["action"].get("price") for s in steps if s.get("action", {}).get("price") is not None]
        unique_prices = len(set(prices)) if prices else 0
        price_range = (max(prices) - min(prices)) if len(prices) >= 2 else 0
        avg_price = sum(prices) / len(prices) if prices else 1
        range_ratio = price_range / avg_price if avg_price > 0 else 0
        complexity_score = round(turns * unique_prices * max(range_ratio, 0.1), 2)

        # Feed OTel
        simulation_counter.add(1)
        negotiation_complexity.record(complexity_score)

        # Average decision latency
        latencies = [d["latency_ms"] for d in tel["agent_decisions"]]
        avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
        max_latency = round(max(latencies), 1) if latencies else 0

        summary = {
            "simulation_duration_ms": round(elapsed, 1),
            "avg_decision_latency_ms": avg_latency,
            "max_decision_latency_ms": max_latency,
            "total_llm_calls": tel["total_llm_calls"],
            "total_errors": tel["total_errors"],
            "total_fallbacks": tel["total_fallbacks"],
            "total_tokens": tel["total_tokens"],
            "negotiation_complexity": complexity_score,
            "decisions": tel["agent_decisions"],
        }

        self.record_event("simulation_complete", {
            "sim_id": sim_id,
            "duration_ms": round(elapsed, 1),
            "complexity": complexity_score,
        })

        return summary

    def get_global_metrics(self) -> dict:
        """Return aggregate metrics across all simulations."""
        all_decisions = []
        total_sims = len(self._sim_telemetry)
        total_errors = 0
        total_tokens = 0

        for tel in self._sim_telemetry.values():
            all_decisions.extend(tel["agent_decisions"])
            total_errors += tel["total_errors"]
            total_tokens += tel["total_tokens"]

        latencies = [d["latency_ms"] for d in all_decisions]

        return {
            "total_simulations": total_sims,
            "total_llm_calls": len(all_decisions),
            "total_errors": total_errors,
            "error_rate_pct": round((total_errors / max(len(all_decisions), 1)) * 100, 1),
            "total_tokens": total_tokens,
            "avg_decision_latency_ms": round(sum(latencies) / max(len(latencies), 1), 1),
            "p95_decision_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1),
            "max_decision_latency_ms": round(max(latencies) if latencies else 0, 1),
            "recent_events": self._events[-20:],
        }


# Singleton instance
collector = TelemetryCollector()
