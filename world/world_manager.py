from typing import List, Dict, Any
import uuid
from agents.base_agent import Agent
from agents.llm_agent import LLMBuyerAgent, LLMSellerAgent
from world.mediator import Mediator
from metrics.storage import save_simulation_result

class WorldManager:
    def __init__(self):
        self.results = []
        # In-memory storage for replays (in a real app, this might go to DB or Redis)
        self.historical_runs: Dict[str, Any] = {}

    def start_simulation(self, scenario: Any) -> dict:
        """
        Core entry point to start the simulation with a defined Scenario
        """
        sim_id = str(uuid.uuid4())
        
        # 1. create agents and mediator using the scenario
        buyer_params = scenario.get_buyer_params()
        seller_params = scenario.get_seller_params()
        
        agent_a = LLMBuyerAgent("Alice (LLM Buyer)", **buyer_params)
        agent_b = LLMSellerAgent("Bob (LLM Seller)", **seller_params)
        mediator = Mediator(max_turns=scenario.max_turns)

        # 2. Start negotiation and monitor with initial state
        result_details = self._run_negotiation_loop(agent_a, agent_b, mediator, scenario.get_initial_state())
        
        # 3. Store results in SQLite
        final_price = None
        if result_details["status"] == "agreement" and len(mediator.history) > 0:
             final_price = mediator.history[-1].price
             
        db_result = save_simulation_result(
            sim_id=sim_id,
            agent_a=agent_a.name,
            agent_b=agent_b.name,
            status=result_details["status"],
            turns=result_details["turns"],
            final_price=final_price
        )

        # 4. Save replay data in memory
        output = {
            "simulation_id": sim_id,
            "status": result_details["status"],
            "turns": result_details["turns"],
            "final_price": final_price,
            "reason": result_details["reason"],
            "history": [msg.dict() for msg in mediator.history],
            "steps": result_details["steps"]
        }
        self.historical_runs[sim_id] = output
        self.results.append(output)
        
        return output

    def run_batch_simulations(self, scenario: Any, runs: int) -> dict:
        """
        Runs multiple simulations back-to-back and aggregates the metrics.
        """
        batch_results = []
        for _ in range(runs):
            # We don't want to save thousands of massive replays in memory during massive batches,
            # so we could optionally bypass `start_simulation` saving to `self.historical_runs`, 
            # but for this MVP, we'll just reuse start_simulation.
            res = self.start_simulation(scenario)
            batch_results.append(res)
            
        # Aggregate metrics
        total = len(batch_results)
        agreements = sum(1 for r in batch_results if r["status"] == "agreement")
        timeouts = sum(1 for r in batch_results if r["status"] == "timeout")
        errors = sum(1 for r in batch_results if r["status"] == "error")
        
        total_turns = sum(r["turns"] for r in batch_results)
        avg_turns = total_turns / total if total > 0 else 0
        
        successful_prices = [r["final_price"] for r in batch_results if r["final_price"] is not None]
        avg_price = sum(successful_prices) / len(successful_prices) if successful_prices else 0
        
        return {
            "total_runs": total,
            "success_rate": (agreements / total) * 100 if total > 0 else 0,
            "agreements": agreements,
            "timeouts": timeouts,
            "deadlocks_or_errors": errors,
            "average_turns": avg_turns,
            "average_agreement_price": avg_price
        }

    def _run_negotiation_loop(self, agent_a: Agent, agent_b: Agent, mediator: Mediator, initial_state: dict):
        finished = False
        turn_count = 0
        state = initial_state
        steps = []

        
        while not finished and turn_count < mediator.max_turns:
            # Agent A's (Buyer) turn
            action_a = agent_a.decide_action(state)
            steps.append({"turn": turn_count + 1, "agent": agent_a.name, "action": action_a})
            
            mediator_check_a = mediator.check_turn(action_a)
            if mediator_check_a["stop"]:
                return {"status": mediator_check_a["status"], "turns": turn_count + 1, "reason": mediator_check_a["reason"], "steps": steps}
            state["current_price"] = action_a.get("price")
            
            # Agent B's (Seller) turn
            action_b = agent_b.decide_action(state)
            steps.append({"turn": turn_count + 1, "agent": agent_b.name, "action": action_b})
            
            mediator_check_b = mediator.check_turn(action_b)
            if mediator_check_b["stop"]:
                return {"status": mediator_check_b["status"], "turns": turn_count + 1, "reason": mediator_check_b["reason"], "steps": steps}
            state["current_price"] = action_b.get("price")
            
            turn_count += 1

        # Reached max turns without Mediator explicitly ending via rules
        return {"status": "timeout", "turns": turn_count, "reason": "Max turns reached", "steps": steps}
    
    def get_simulation(self, sim_id: str) -> dict:
        return self.historical_runs.get(sim_id, {"error": "Not Found"})
    
    def get_all_replays(self) -> List[dict]:
        return list(self.historical_runs.values())
