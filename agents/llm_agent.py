import json
import requests
from agents.base_agent import Agent
from backend.config import settings

class LLMAgent(Agent):
    def __init__(self, name: str, role: str):
        super().__init__(name)
        self.role = role
        self.history = []

    def decide_action(self, state: dict) -> dict:
        current_price = state.get('current_price', 'None yet')
        
        prompt = f"""
You are {self.role} in a negotiation.

Current price: {current_price}
Your goal: maximize outcome.

Available actions:
offer
counter_offer
accept
reject

Respond in EXACT JSON format with no markdown wrappers or other text:
{{ "action": "...", "price": number }}
"""
        import ollama
        
        # We append to history to keep context, though Ollama handles it natively well
        self.history.append({"role": "user", "content": prompt})

        try:
            # Using Ollama's local chat inference
            response = ollama.chat(
                model=settings.MODEL_NAME,
                messages=self.history
            )
            
            generated_text = response.get("message", {}).get("content", "")
            
            # Clean up any potential markdown formatting
            generated_text = generated_text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(generated_text)
            if "action" in result and "type" not in result:
                result["type"] = result.pop("action")
            
            self.history.append({"role": "assistant", "content": generated_text})
            return result
                
        except Exception as e:
            # Reverting to programmatic mock fallback so the simulation can still run visually
            print(f"[{self.name}] Ollama Error: {e} - Using programmatic fallback.")
            if current_price == 'None yet':
                return {"type": "offer", "price": 100.0 if "seller" in self.role.lower() else 150.0}
            
            p = float(current_price)
            if "seller" in self.role.lower():
                return {"type": "accept" if p >= 110 else "counter", "price": None if p >= 110 else p * 1.1}
            else:
                return {"type": "accept" if p <= 140 else "counter", "price": None if p <= 140 else p * 0.9}

class LLMBuyerAgent(LLMAgent):
    def __init__(self, name: str, max_price: float):
        super().__init__(name, role=f"a buyer with a strict max budget of {max_price}")
        self.max_price = max_price

class LLMSellerAgent(LLMAgent):
    def __init__(self, name: str, min_price: float):
        super().__init__(name, role=f"a seller with a strict minimum acceptable price of {min_price}")
        self.min_price = min_price
