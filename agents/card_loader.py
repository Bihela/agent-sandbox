"""
Agent Card Loader — discovers, loads, and validates agent cards from JSON files.

Agent cards are JSON descriptors that define agent capabilities, supported strategies,
models, parameters, and I/O schemas. This enables agent discovery and cross-agent
compatibility checking.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


CARDS_DIR = Path(__file__).parent / "cards"


def load_all_cards() -> List[Dict[str, Any]]:
    """Load all agent cards from the cards directory."""
    cards = []
    if not CARDS_DIR.exists():
        return cards

    for filepath in sorted(CARDS_DIR.glob("*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                card = json.load(f)
                card["_source_file"] = filepath.name
                cards.append(card)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[CardLoader] Warning: Failed to load {filepath.name}: {e}")

    return cards


def get_card(agent_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific agent card by agent_name."""
    for card in load_all_cards():
        if card.get("agent_name") == agent_name:
            return card
    return None


def check_compatibility(card_a: dict, card_b: dict) -> Dict[str, Any]:
    """
    Check if two agents are compatible for a simulation.

    Returns a compatibility report with:
    - compatible: bool
    - shared_capabilities: list
    - shared_strategies: list
    - shared_models: list
    - issues: list of incompatibility reasons
    """
    issues = []

    # Protocol check
    proto_a = card_a.get("protocol", "")
    proto_b = card_b.get("protocol", "")
    if proto_a != proto_b:
        issues.append(f"Protocol mismatch: {proto_a} vs {proto_b}")

    # Role check — need complementary roles
    role_a = card_a.get("role", "")
    role_b = card_b.get("role", "")
    if role_a == role_b:
        issues.append(f"Same role: both are '{role_a}' — need buyer + seller")

    # Shared capabilities
    caps_a = set(card_a.get("capabilities", []))
    caps_b = set(card_b.get("capabilities", []))
    shared_caps = sorted(caps_a & caps_b)

    if "price_negotiation" not in caps_a or "price_negotiation" not in caps_b:
        issues.append("Both agents must support 'price_negotiation'")

    # Shared strategies
    strats_a = set(card_a.get("strategy_options", []))
    strats_b = set(card_b.get("strategy_options", []))
    shared_strats = sorted(strats_a & strats_b)

    # Shared models
    models_a = set(card_a.get("models_supported", []))
    models_b = set(card_b.get("models_supported", []))
    shared_models = sorted(models_a & models_b)

    if not shared_models:
        issues.append("No shared models between agents")

    # I/O schema check
    out_a = card_a.get("output_schema", {}).get("fields", [])
    out_b = card_b.get("output_schema", {}).get("fields", [])
    if out_a != out_b:
        issues.append(f"Output schema mismatch: {out_a} vs {out_b}")

    return {
        "compatible": len(issues) == 0,
        "shared_capabilities": shared_caps,
        "shared_strategies": shared_strats,
        "shared_models": shared_models,
        "issues": issues,
    }
