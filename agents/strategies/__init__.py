"""
Agent Strategy Registry.

Provides a single `get_strategy(name)` function to load strategy modules.
"""

from agents.strategies.base_strategy import BaseStrategy
from agents.strategies.aggressive import AggressiveStrategy
from agents.strategies.balanced import BalancedStrategy
from agents.strategies.conservative import ConservativeStrategy

# ─── Strategy Registry ───
STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "aggressive": AggressiveStrategy,
    "balanced": BalancedStrategy,
    "adaptive": BalancedStrategy,       # alias
    "conservative": ConservativeStrategy,
    "cooperative": ConservativeStrategy, # alias
    "analytical": BalancedStrategy,      # alias → balanced with data focus
}


def get_strategy(name: str) -> BaseStrategy:
    """
    Load a strategy by name.

    Args:
        name: strategy name (aggressive, balanced, conservative, adaptive, cooperative, analytical)

    Returns:
        An instantiated strategy object.

    Raises:
        ValueError if strategy name is unknown.
    """
    cls = STRATEGY_REGISTRY.get(name.lower())
    if cls is None:
        available = ", ".join(sorted(STRATEGY_REGISTRY.keys()))
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
    return cls()


def list_strategies() -> list[str]:
    """Return all available strategy names."""
    return sorted(set(STRATEGY_REGISTRY.keys()))
