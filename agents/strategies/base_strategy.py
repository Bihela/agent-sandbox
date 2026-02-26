"""
Abstract base class for all negotiation strategies.

A strategy defines:
  - system_prompt: injected into the LLM prompt to shape behavior
  - fallback_logic: programmatic decision-making when LLM fails
  - concession_rate: how much the agent concedes per turn (0.0–1.0)
"""

from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """Base class for agent negotiation strategies."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def get_system_prompt(self, role: str) -> str:
        """Return the behavioral prompt modifier for the LLM."""
        ...

    @abstractmethod
    def compute_fallback_action(self, role: str, current_price: float,
                                 budget_limit: float) -> dict:
        """
        Compute a programmatic fallback action when LLM fails.

        Args:
            role: 'buyer' or 'seller'
            current_price: the current negotiation price
            budget_limit: buyer's max_price or seller's min_price

        Returns:
            dict with 'type', 'price', 'reasoning'
        """
        ...

    @property
    @abstractmethod
    def concession_rate(self) -> float:
        """How aggressively the agent concedes (0.0 = never, 1.0 = immediately)."""
        ...
