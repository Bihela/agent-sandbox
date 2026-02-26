"""
Multi-Vendor Negotiation Scenario.
One Buyer vs multiple Sellers competing simultaneously.
"""

from typing import Dict, Any, List
from scenarios.base_scenario import BaseScenario

class MultiVendorNegotiationScenario(BaseScenario):
    def __init__(self, buyer_max: float = 150.0, seller_min: float = 100.0, num_vendors: int = 2):
        self.buyer_max = buyer_max
        self.seller_min = seller_min
        self.num_vendors = num_vendors
        self.max_turns = 20

    def get_initial_state(self) -> Dict[str, Any]:
        return {
            "current_price": None,
            "turn": 1,
            "participants": ["Buyer"] + [f"Vendor {i+1}" for i in range(self.num_vendors)]
        }

    def get_buyer_params(self) -> Dict[str, Any]:
        return {
            "max_price": self.buyer_max,
            "role_description": "You are a buyer looking for the best deal among multiple competing vendors."
        }

    def get_seller_params(self) -> Dict[str, Any]:
        return {
            "min_price": self.seller_min,
            "role_description": "You are a vendor competing with others to win a contract from a single buyer."
        }
