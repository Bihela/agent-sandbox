"""
Balanced Strategy — moderate approach, adapt to opponent, seek fair deals.
"""

from agents.strategies.base_strategy import BaseStrategy


class BalancedStrategy(BaseStrategy):

    name = "balanced"
    description = "Adaptive and moderate. Evaluate each offer carefully and adjust based on opponent behavior."

    @property
    def concession_rate(self) -> float:
        return 0.10  # 10% concession per turn

    def get_system_prompt(self, role: str) -> str:
        return (
            f"You are a BALANCED {role} negotiator. "
            "Take a moderate, adaptive approach. Make reasonable counter-offers of about 10% movement. "
            "Evaluate each offer carefully before responding. "
            "If the opponent is conceding, push a bit harder. If they hold firm, show flexibility. "
            "Aim for a fair deal that is favorable but realistic."
        )

    def compute_fallback_action(self, role: str, current_price: float,
                                 budget_limit: float) -> dict:
        if role == "buyer":
            if current_price <= budget_limit * 0.9:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} is within 90% of budget — good deal."}
            return {"type": "counter_offer", "price": round(current_price * 0.90, 2),
                    "reasoning": f"Balanced counter: 10% lower at ${round(current_price * 0.90, 2)}."}
        else:
            if current_price >= budget_limit * 1.1:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} is 10% above minimum — accepting."}
            return {"type": "counter_offer", "price": round(current_price * 1.10, 2),
                    "reasoning": f"Balanced counter: 10% higher at ${round(current_price * 1.10, 2)}."}
