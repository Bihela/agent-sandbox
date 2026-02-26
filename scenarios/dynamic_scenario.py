from typing import Dict, Any, List, Optional
from scenarios.base_scenario import BaseScenario

class DynamicScenario(BaseScenario):
    """
    A scenario that can be dynamically configured via JSON/API parameters.
    """
    def __init__(
        self, 
        name: str, 
        description: str, 
        buyer_max: float = 150.0, 
        seller_min: float = 100.0, 
        num_vendors: int = 1,
        max_turns: int = 20,
        goal: str = "maximize_efficiency",
        custom_params: Dict[str, Any] = None
    ):
        super().__init__(name=name, description=description, max_turns=max_turns)
        self.buyer_max = buyer_max
        self.seller_min = seller_min
        self.num_vendors = num_vendors
        self.goal = goal
        self.custom_params = custom_params or {}

    def get_initial_state(self) -> Dict[str, Any]:
        participants = ["Buyer"]
        if self.num_vendors == 1:
            participants.append("Seller")
        else:
            participants.extend([f"Vendor {i+1}" for i in range(self.num_vendors)])
            
        return {
            "current_price": None,
            "turn": 1,
            "participants": participants,
            "goal": self.goal,
            **self.custom_params
        }

    def get_buyer_params(self) -> Dict[str, Any]:
        return {
            "max_price": self.buyer_max,
            "goal": self.goal,
            "context": self.description
        }

    def get_seller_params(self) -> Dict[str, Any]:
        return {
            "min_price": self.seller_min,
            "goal": self.goal,
            "context": self.description
        }
