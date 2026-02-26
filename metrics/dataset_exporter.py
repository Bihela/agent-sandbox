"""
Dataset Exporter — flattens simulation replay data into tabular format
for export as JSON or CSV. Turns the sandbox into a dataset generator.
"""

import csv
import io
from typing import List, Dict, Any


# ─── Column schema for the flat dataset ───
COLUMNS = [
    "simulation_id", "status", "turns", "final_price",
    "negotiation_style", "buyer_strategy", "seller_strategy",
    "buyer_temperature", "seller_temperature", "model",
    "risk_score", "failure_count",
    "avg_decision_latency_ms", "total_tokens", "negotiation_complexity",
    "turn", "agent", "action_type", "price", "reasoning",
]


def flatten_simulation(run: dict) -> List[Dict[str, Any]]:
    """
    Flatten a single simulation replay into one row per decision step.
    Each row contains simulation-level metadata + per-step action data.
    """
    sim_id = run.get("simulation_id", "")
    status = run.get("status", "")
    turns = run.get("turns", 0)
    final_price = run.get("final_price")

    # Config
    cfg = run.get("config", {})
    style = cfg.get("negotiation_style", "")
    buyer_strat = cfg.get("buyer_strategy", "")
    seller_strat = cfg.get("seller_strategy", "")
    buyer_temp = cfg.get("buyer_temperature", "")
    seller_temp = cfg.get("seller_temperature", "")
    model = cfg.get("model", "")

    # Failure report
    fr = run.get("failure_report", {})
    risk_score = fr.get("risk_score", 0)
    failure_count = len(fr.get("failures", []))

    # Telemetry
    tel = run.get("telemetry", {})
    avg_latency = tel.get("avg_decision_latency_ms", "")
    total_tokens = tel.get("total_tokens", "")
    complexity = tel.get("negotiation_complexity", "")

    steps = run.get("steps", [])
    if not steps:
        # Return one summary row even if no steps
        return [{
            "simulation_id": sim_id, "status": status, "turns": turns,
            "final_price": final_price, "negotiation_style": style,
            "buyer_strategy": buyer_strat, "seller_strategy": seller_strat,
            "buyer_temperature": buyer_temp, "seller_temperature": seller_temp,
            "model": model, "risk_score": risk_score,
            "failure_count": failure_count,
            "avg_decision_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "negotiation_complexity": complexity,
            "turn": "", "agent": "", "action_type": "", "price": "",
            "reasoning": "",
        }]

    rows = []
    for step in steps:
        action = step.get("action", {})
        rows.append({
            "simulation_id": sim_id,
            "status": status,
            "turns": turns,
            "final_price": final_price,
            "negotiation_style": style,
            "buyer_strategy": buyer_strat,
            "seller_strategy": seller_strat,
            "buyer_temperature": buyer_temp,
            "seller_temperature": seller_temp,
            "model": model,
            "risk_score": risk_score,
            "failure_count": failure_count,
            "avg_decision_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "negotiation_complexity": complexity,
            "turn": step.get("turn", ""),
            "agent": step.get("agent", ""),
            "action_type": action.get("type", ""),
            "price": action.get("price", ""),
            "reasoning": action.get("reasoning", ""),
        })
    return rows


def export_to_rows(replays: List[dict]) -> List[Dict[str, Any]]:
    """Flatten all replays into a single list of rows."""
    all_rows = []
    for run in replays:
        all_rows.extend(flatten_simulation(run))
    return all_rows


def export_to_csv_string(replays: List[dict]) -> str:
    """Export all replays as a CSV string."""
    rows = export_to_rows(replays)
    if not rows:
        return ",".join(COLUMNS) + "\n"

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNS, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
