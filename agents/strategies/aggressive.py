"""
Aggressive Strategy — push hard, concede little, hold out for best deal.
"""

from agents.strategies.base_strategy import BaseStrategy


class AggressiveStrategy(BaseStrategy):

    name = "aggressive"
    description = "Push hard for the best deal. Make small concessions and never give more than 5% at a time."

    @property
    def concession_rate(self) -> float:
        return 0.05  # Only 5% concession per turn

    def get_system_prompt(self, role: str) -> str:
        return (
            f"You are an AGGRESSIVE {role} negotiator. "
            "Push hard for the absolute best deal. Never concede more than 5% at a time. "
            "Reject offers aggressively if they are not close to your target. "
            "Use anchoring — start with an extreme position and move slowly. "
            "Show willingness to walk away if the deal isn't favorable."
        )

    def compute_fallback_action(self, role: str, current_price: float,
                                 budget_limit: float) -> dict:
        if role == "buyer":
            # Aggressive buyer: only accept if way under budget, small counter-offers
            if current_price <= budget_limit * 0.75:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} is well below budget — accepting aggressively."}
            return {"type": "counter_offer", "price": round(current_price * 0.95, 2),
                    "reasoning": f"Aggressive counter: only 5% lower at ${round(current_price * 0.95, 2)}."}
        else:
            # Aggressive seller: only accept if way above minimum, small concessions
            if current_price >= budget_limit * 1.3:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} far exceeds minimum — accepting."}
            return {"type": "counter_offer", "price": round(current_price * 1.05, 2),
                    "reasoning": f"Aggressive counter: 5% higher at ${round(current_price * 1.05, 2)}."}
