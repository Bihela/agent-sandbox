import json
import ollama
from agents.base_agent import Agent


class LLMAgent(Agent):
    def __init__(self, name, role, temperature=0.7, strategy_prompt="", risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(name)
        self.role = role
        self.model = model
        self.temperature = temperature
        self.strategy_prompt = strategy_prompt
        self.risk_prompt = risk_prompt
        self.style_prompt = style_prompt
        self.history = []

    def decide_action(self, state):
        current_price = state.get('price', state.get('current_price', 'None yet'))

        # Build behavioral modifiers from config
        behavior_lines = "\n".join(filter(None, [
            self.strategy_prompt,
            self.risk_prompt,
            self.style_prompt,
        ]))

        prompt = f"""
You are {self.role} in a negotiation.

Current price: {current_price}
Your goal: maximize outcome.

{behavior_lines}

Available actions:
offer
counter_offer
accept
reject

Respond in EXACT JSON format with no markdown wrappers or other text:
{{ "type": "...", "price": number_or_null, "reasoning": "one sentence explaining your decision" }}
"""

        self.history.append({"role": "user", "content": prompt})

        try:
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                options={"temperature": self.temperature}
            )

            generated_text = response.get("message", {}).get("content", "")

            # Clean up any potential markdown formatting
            generated_text = generated_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(generated_text)

            # Normalize: if LLM used "action" instead of "type", fix it
            if "action" in result and "type" not in result:
                result["type"] = result.pop("action")

            # Ensure reasoning field exists
            if "reasoning" not in result:
                result["reasoning"] = ""

            self.history.append({"role": "assistant", "content": generated_text})
            return result

        except Exception as e:
            print(f"[{self.name}] Ollama Error: {e} - Using programmatic fallback.")
            if current_price is None or current_price == 'None yet':
                return {"type": "offer", "price": 100.0 if "seller" in self.role.lower() else 150.0, "reasoning": "Opening offer (fallback)."}

            p = float(current_price)
            if "seller" in self.role.lower():
                if p >= 110:
                    return {"type": "accept", "price": None, "reasoning": f"Price ${p} meets minimum threshold (fallback)."}
                return {"type": "counter_offer", "price": round(p * 1.1, 2), "reasoning": f"Counter-offering 10% higher (fallback)."}
            else:
                if p <= 140:
                    return {"type": "accept", "price": None, "reasoning": f"Price ${p} is within budget (fallback)."}
                return {"type": "counter_offer", "price": round(p * 0.9, 2), "reasoning": f"Counter-offering 10% lower (fallback)."}


class LLMBuyerAgent(LLMAgent):
    def __init__(self, name: str, max_price: float, temperature=0.7,
                 strategy_prompt="", risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(
            name,
            role=f"a buyer with a strict max budget of {max_price}",
            temperature=temperature,
            strategy_prompt=strategy_prompt,
            risk_prompt=risk_prompt,
            style_prompt=style_prompt,
            model=model,
        )
        self.max_price = max_price


class LLMSellerAgent(LLMAgent):
    def __init__(self, name: str, min_price: float, temperature=0.7,
                 strategy_prompt="", risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(
            name,
            role=f"a seller with a strict minimum acceptable price of {min_price}",
            temperature=temperature,
            strategy_prompt=strategy_prompt,
            risk_prompt=risk_prompt,
            style_prompt=style_prompt,
            model=model,
        )
        self.min_price = min_price
