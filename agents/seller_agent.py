from agents.base_agent import Agent

class SellerAgent(Agent):
    def __init__(self, name: str, min_price: float):
        super().__init__(name)
        self.min_price = min_price

    def decide_action(self, state: dict) -> dict:
        current_price = state.get("current_price")
        
        if current_price is None:
             # Initial ask higher than minimum
             ask = self.min_price * 1.2
             return {"action": "offer", "price": ask}
             
        if current_price < self.min_price:
            # Counter with minimum acceptable price + margin
            ask = self.min_price * 1.1
            return {"action": "counter", "price": ask}
        else:
            # Accept if price is above minimum
            return {"action": "accept", "price": current_price}
