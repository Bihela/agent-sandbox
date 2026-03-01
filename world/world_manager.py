from typing import List, Dict, Any, Optional
import uuid
from agents.base_agent import Agent
from agents.llm_agent import LLMBuyerAgent, LLMSellerAgent
from agents.red_team_agent import RedTeamAgent
from world.mediator import Mediator
from metrics.storage import save_simulation_result
from configs.simulation_config import SimulationConfig, DEFAULT_CONFIG
from telemetry_module.telemetry import tracer, collector

class WorldManager:
    """
    The central orchestration engine for the Agent Sandbox.
    
    Responsible for initializing agents, managing the negotiation environment,
    and recording simulation results.
    """
    def __init__(self):
        self.results = []
        # In-memory storage for replays
        self.historical_runs: Dict[str, Any] = {}
        self.red_team = RedTeamAgent()

    def start_simulation(self, scenario: Any, config: Optional[SimulationConfig] = None) -> dict:
        """
        Initiates a simulation with a specific scenario and configuration.
        
        Args:
            scenario: The negotiation scenario to run (e.g., PriceNegotiationScenario).
            config: Optional SimulationConfig for agent behaviors and global settings.
            
        Returns:
            A dictionary containing the simulation history, status, and telemetry.
        """
        if config is None:
            config = DEFAULT_CONFIG

        sim_id = str(uuid.uuid4())
        
        # ─── 1. Build Agent Pool ───
        agents = []
        style_prompt = config.get_style_prompt()

        if config.agents_configs:
            # Multi-agent initialization
            for idx, agent_cfg in enumerate(config.agents_configs):
                role = agent_cfg.role.lower()
                name = agent_cfg.name or f"Agent {idx+1} ({role})"
                
                # Determine class based on role
                if "buyer" in role:
                    agent_cls = LLMBuyerAgent
                else:
                    agent_cls = LLMSellerAgent
                
                strategy_prompt = config.get_strategy_prompt(agent_cfg.strategy)
                risk_prompt = config.get_risk_prompt(agent_cfg.risk_level)
                
                # Merge scenario params if applicable (fallback to defaults)
                # For multi-agent, the scenario might provide a list of params
                # For now, we'll try to get role-based params from scenario
                params = {}
                if "buyer" in role:
                    params = scenario.get_buyer_params()
                else:
                    params = scenario.get_seller_params()

                agent = agent_cls(
                    name=name,
                    **params,
                    temperature=agent_cfg.temperature,
                    strategy_name=agent_cfg.strategy.value,
                    risk_prompt=risk_prompt,
                    style_prompt=f"{style_prompt} {strategy_prompt}",
                    model=agent_cfg.model_name or config.model_name
                )
                agent._sim_id = sim_id
                agent._seed = config.seed # Propagate seed
                agents.append(agent)
        else:
            # Legacy 1v1 fallback
            buyer_params = scenario.get_buyer_params()
            seller_params = scenario.get_seller_params()
            
            buyer_risk = config.get_risk_prompt(config.buyer_config.risk_level)
            seller_risk = config.get_risk_prompt(config.seller_config.risk_level)

            agent_a = LLMBuyerAgent(
                "Alice (LLM Buyer)", **buyer_params,
                temperature=config.buyer_config.temperature,
                strategy_name=config.buyer_config.strategy.value,
                risk_prompt=buyer_risk,
                style_prompt=style_prompt,
                model=config.buyer_config.model_name or config.model_name,
            )
            agent_b = LLMSellerAgent(
                "Bob (LLM Seller)", **seller_params,
                temperature=config.seller_config.temperature,
                strategy_name=config.seller_config.strategy.value,
                risk_prompt=seller_risk,
                style_prompt=style_prompt,
                model=config.seller_config.model_name or config.model_name,
            )
            agent_a._sim_id = sim_id
            agent_b._sim_id = sim_id
            agent_a._seed = config.seed
            agent_b._seed = config.seed
            agents = [agent_a, agent_b]

        mediator = Mediator(max_turns=scenario.max_turns, num_participants=len(agents))

        # Initialize telemetry for this simulation
        collector.start_simulation_telemetry(sim_id)

        # ─── 2. Start negotiation and monitor ───
        with tracer.start_as_current_span(
            "simulation.run",
            attributes={
                "simulation.id": sim_id,
                "simulation.participants": len(agents),
                "simulation.max_turns": scenario.max_turns,
                "config.style": config.negotiation_style.value,
            }
        ) as span:
            result_details = self._run_negotiation_loop(agents, mediator, scenario.get_initial_state(), config)
            span.set_attribute("simulation.status", result_details["status"])
            span.set_attribute("simulation.turns", result_details["turns"])

        # ─── 3. Post-Sim Analysis ───
        # For multi-agent, we use default thresholds for failure detection if not clear
        buyer_max = getattr(scenario, 'buyer_max', 150.0)
        seller_min = getattr(scenario, 'seller_min', 100.0)

        failure_report = mediator.get_failure_report(
            result_details["steps"],
            buyer_max=buyer_max,
            seller_min=seller_min
        )
        
        # Determine final price from last step if agreement
        final_price = None
        if result_details["status"] == "agreement":
            final_price = result_details.get("final_price") or (mediator.history[-1].price if mediator.history else None)
            
            # If still null (common in acceptance messages), look at the turn before or global state
            if final_price is None and len(mediator.history) > 1:
                final_price = mediator.history[-2].price
             
        # Save to DB (Legacy DB schema only supports 2 agents, we use first 2 or summary)
        agent_names = [a.name for a in agents]
        save_simulation_result(
            sim_id=sim_id,
            agent_a=agent_names[0],
            agent_b=agent_names[1] if len(agent_names) > 1 else "None",
            status=result_details["status"],
            turns=result_details["turns"],
            final_price=final_price
        )

        # ─── 4. Save replay data ───
        output = {
            "simulation_id": sim_id,
            "agent_a": agent_names[0] if len(agent_names) > 0 else "Unknown",
            "agent_b": agent_names[1] if len(agent_names) > 1 else "None",
            "status": result_details["status"],
            "turns": result_details["turns"],
            "final_price": final_price,
            "reason": result_details["reason"],
            "history": [msg.dict() for msg in mediator.history],
            "steps": result_details["steps"],
            "failure_report": failure_report,
            "config": {"model": config.model_name, "style": config.negotiation_style.value},
            "telemetry": collector.finalize_simulation(sim_id, result_details["turns"], result_details["steps"]),
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

    def _run_negotiation_loop(self, participants: List[Agent], mediator: Mediator, initial_state: dict, config: SimulationConfig):
        finished = False
        turn_count = 0
        state = initial_state
        steps = []

        import random

        while not finished and turn_count < mediator.max_turns:
            for idx, current_agent in enumerate(participants):
                
                # In multi-agent, we need to decide who the receiver is.
                # Simplest model: Next agent in list (round-robin) or broadcast.
                # For now, we'll set receiver to the 'other' principal agent or broadcast.
                next_idx = (idx + 1) % len(participants)
                receiver = participants[next_idx]
                
                action_dict = current_agent.decide_action(state)
                action_dict["sender"] = current_agent.name
                action_dict["receiver"] = receiver.name
                
                # ─── RED TEAM DISRUPTION ───
                if config.red_team_config.enabled and random.random() < config.red_team_config.attack_probability:
                    action_dict = self.red_team.disrupt(action_dict, config.red_team_config.attack_types)

                steps.append({
                    "turn": turn_count + 1, 
                    "agent": current_agent.name, 
                    "action": action_dict, 
                    "is_adversarial": action_dict.get("is_adversarial", False)
                })
                
                mediator_check = mediator.check_turn(action_dict)
                if mediator_check["stop"]:
                    return {
                        "status": mediator_check["status"], 
                        "turns": turn_count + 1, 
                        "reason": mediator_check["reason"], 
                        "steps": steps
                    }
                
                # Update global state with most recent valid price
                if action_dict.get("price") is not None:
                    state["current_price"] = action_dict.get("price")
            
            turn_count += 1

        # Reached max turns without Mediator explicitly ending via rules
        return {"status": "timeout", "turns": turn_count, "reason": "Max turns reached", "steps": steps}
    
    def get_simulation(self, sim_id: str) -> dict:
        return self.historical_runs.get(sim_id, {"error": "Not Found"})
    
    def get_all_replays(self) -> List[dict]:
        return list(self.historical_runs.values())
