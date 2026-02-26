import json
import time
import ollama
from agents.base_agent import Agent
from agents.strategies import get_strategy
from telemetry_module.telemetry import tracer, collector


class LLMAgent(Agent):
    def __init__(self, name, role, temperature=0.7, strategy_name="balanced",
                 risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(name)
        self.role = role
        self.model = model
        self.temperature = temperature
        self.strategy = get_strategy(strategy_name)
        self.risk_prompt = risk_prompt
        self.style_prompt = style_prompt
        self.history = []
        self._sim_id = None  # Set by WorldManager before simulation starts
        self._role_type = "seller" if "seller" in role.lower() else "buyer"

    def decide_action(self, state):
        current_price = state.get('price', state.get('current_price', 'None yet'))

        # Build behavioral modifiers from strategy + config
        strategy_prompt = self.strategy.get_system_prompt(self._role_type)
        behavior_lines = "\n".join(filter(None, [
            strategy_prompt,
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

        start_time = time.perf_counter()
        tokens_used = 0

        with tracer.start_as_current_span(
            "agent.decide_action",
            attributes={
                "agent.name": self.name,
                "agent.model": self.model,
                "agent.temperature": self.temperature,
                "agent.strategy": self.strategy.name,
                "negotiation.current_price": str(current_price),
            }
        ) as span:
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=self.history,
                    options={"temperature": self.temperature}
                )

                generated_text = response.get("message", {}).get("content", "")
                tokens_used = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)

                # Clean up any potential markdown formatting
                generated_text = generated_text.replace("```json", "").replace("```", "").strip()

                result = json.loads(generated_text)

                # Normalize: if LLM used "action" instead of "type", fix it
                if "action" in result and "type" not in result:
                    result["type"] = result.pop("action")

                if "reasoning" not in result:
                    result["reasoning"] = ""

                self.history.append({"role": "assistant", "content": generated_text})

                span.set_attribute("agent.action", result.get("type", "unknown"))
                span.set_attribute("llm.tokens", tokens_used)

                latency_ms = (time.perf_counter() - start_time) * 1000
                if self._sim_id:
                    collector.record_decision(
                        self._sim_id, self.name, latency_ms,
                        tokens=tokens_used, model=self.model
                    )

                return result

            except Exception as e:
                span.set_attribute("agent.error", str(e))
                span.set_attribute("agent.fallback", True)

                print(f"[{self.name}] Ollama Error: {e} - Using strategy fallback ({self.strategy.name}).")

                latency_ms = (time.perf_counter() - start_time) * 1000
                if self._sim_id:
                    collector.record_decision(
                        self._sim_id, self.name, latency_ms,
                        error=True, fallback=True, model=self.model
                    )

                # Use strategy's fallback logic instead of hardcoded values
                if current_price is None or current_price == 'None yet':
                    opening = self._budget_limit * 0.7 if self._role_type == "buyer" else self._budget_limit
                    return {"type": "offer", "price": round(opening, 2),
                            "reasoning": f"Opening offer via {self.strategy.name} strategy (fallback)."}

                return self.strategy.compute_fallback_action(
                    self._role_type, float(current_price), self._budget_limit
                )

    @property
    def _budget_limit(self) -> float:
        """Return the agent's budget constraint for fallback logic."""
        return getattr(self, 'max_price', getattr(self, 'min_price', 100.0))


class LLMBuyerAgent(LLMAgent):
    def __init__(self, name: str, max_price: float, temperature=0.7,
                 strategy_name="balanced", risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(
            name,
            role=f"a buyer with a strict max budget of {max_price}",
            temperature=temperature,
            strategy_name=strategy_name,
            risk_prompt=risk_prompt,
            style_prompt=style_prompt,
            model=model,
        )
        self.max_price = max_price


class LLMSellerAgent(LLMAgent):
    def __init__(self, name: str, min_price: float, temperature=0.7,
                 strategy_name="balanced", risk_prompt="", style_prompt="", model="mistral"):
        super().__init__(
            name,
            role=f"a seller with a strict minimum acceptable price of {min_price}",
            temperature=temperature,
            strategy_name=strategy_name,
            risk_prompt=risk_prompt,
            style_prompt=style_prompt,
            model=model,
        )
        self.min_price = min_price
