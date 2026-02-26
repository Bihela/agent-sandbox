from scenarios.base_scenario import BaseScenario

class PriceNegotiationScenario(BaseScenario):
    def __init__(self, buyer_max: float = 150.0, seller_min: float = 100.0, max_turns: int = 20):
        super().__init__(
            name="Standard Price Negotiation",
            description="A simple 1-on-1 price negotiation between a buyer and a seller.",
            max_turns=max_turns
        )
        self.buyer_max = buyer_max
        self.seller_min = seller_min
        
    def get_buyer_params(self) -> dict:
        return {"max_price": self.buyer_max}

    def get_seller_params(self) -> dict:
        return {"min_price": self.seller_min}

    def get_initial_state(self) -> dict:
        return {"current_price": None}
