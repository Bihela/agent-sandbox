from agents.base_agent import Agent

class BuyerAgent(Agent):
    def __init__(self, name: str, max_price: float):
        super().__init__(name)
        self.max_price = max_price

    def decide_action(self, state: dict) -> dict:
        current_price = state.get("current_price")
        
        if current_price is None:
            # If no price yet, offer a lower price than max
            offer = self.max_price * 0.8
            return {"action": "offer", "price": offer}
            
        if current_price > self.max_price:
            # Counter offer slightly lower
            offer = self.max_price * 0.9
            return {"action": "counter", "price": offer}
        else:
            # Accept if price is acceptable
            return {"action": "accept", "price": current_price}
