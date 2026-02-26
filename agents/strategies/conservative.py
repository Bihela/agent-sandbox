"""
Conservative Strategy — risk-averse, seek quick agreement, large concessions.
"""

from agents.strategies.base_strategy import BaseStrategy


class ConservativeStrategy(BaseStrategy):

    name = "conservative"
    description = "Risk-averse. Accept reasonable deals early. Make large concessions to close quickly."

    @property
    def concession_rate(self) -> float:
        return 0.20  # 20% concession per turn — wants to close fast

    def get_system_prompt(self, role: str) -> str:
        return (
            f"You are a CONSERVATIVE {role} negotiator. "
            "You are risk-averse and prefer quick agreements over holding out for the best deal. "
            "Make generous concessions of up to 20% to show good faith. "
            "Accept any reasonable offer rather than risking a breakdown. "
            "Value the relationship and long-term collaboration over short-term gains."
        )

    def compute_fallback_action(self, role: str, current_price: float,
                                 budget_limit: float) -> dict:
        if role == "buyer":
            if current_price <= budget_limit:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} is within budget — accepting to close quickly."}
            return {"type": "counter_offer", "price": round(current_price * 0.80, 2),
                    "reasoning": f"Conservative counter: 20% lower at ${round(current_price * 0.80, 2)}."}
        else:
            if current_price >= budget_limit:
                return {"type": "accept", "price": None,
                        "reasoning": f"Price ${current_price} meets minimum — accepting to close quickly."}
            return {"type": "counter_offer", "price": round(current_price * 1.20, 2),
                    "reasoning": f"Conservative counter: 20% higher at ${round(current_price * 1.20, 2)}."}
