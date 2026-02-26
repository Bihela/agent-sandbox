import json
import uuid
import itertools
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from world.world_manager import WorldManager
from scenarios.price_negotiation import PriceNegotiationScenario
from configs.simulation_config import SimulationConfig, AgentConfig, StrategyType, RiskLevel, NegotiationStyle

EXPERIMENTS_DIR = Path("c:/Users/Harsha Wanasekara/Documents/agent-sandbox/agent-sandbox/data/experiments")

class ExperimentRunner:
    def __init__(self, world_manager: WorldManager):
        self.world_manager = world_manager
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    async def run_parameter_sweep(self, 
                                 experiment_name: str,
                                 strategies: List[str], 
                                 temperatures: List[float],
                                 models: List[str],
                                 runs_per_config: int = 5) -> str:
        """
        Runs a comprehensive parameter sweep, varying multiple factors.
        Returns the experiment_id.
        """
        experiment_id = str(uuid.uuid4())
        results = []
        
        # Scenario setup
        scenario = PriceNegotiationScenario(buyer_max=150.0, seller_min=100.0, max_turns=20)
        
        # Generate all combinations of parameters
        combinations = list(itertools.product(models, strategies, strategies, temperatures))
        total_runs = len(combinations) * runs_per_config
        
        print(f"DEBUG: Starting experiment {experiment_id} ({experiment_name})")
        print(f"DEBUG: Total configs: {len(combinations)}, Total runs: {total_runs}")

        for model, b_strat, s_strat, temp in combinations:
            config_results = []
            for i in range(runs_per_config):
                config = SimulationConfig(
                    buyer_max=150.0,
                    seller_min=100.0,
                    max_turns=20,
                    negotiation_style=NegotiationStyle.FORMAL,
                    buyer_config=AgentConfig(
                        strategy=StrategyType(b_strat),
                        risk_level=RiskLevel.MEDIUM,
                        temperature=temp
                    ),
                    seller_config=AgentConfig(
                        strategy=StrategyType(s_strat),
                        risk_level=RiskLevel.MEDIUM,
                        temperature=temp
                    ),
                    model_name=model,
                    temperature=temp
                )
                
                # run simulation
                res = self.world_manager.start_simulation(scenario, config)
                config_results.append(res)
            
            # Aggregate results for this specific config
            agreements = sum(1 for r in config_results if r["status"] == "agreement")
            avg_turns = sum(r["turns"] for r in config_results) / len(config_results)
            
            results.append({
                "parameters": {
                    "model": model,
                    "buyer_strategy": b_strat,
                    "seller_strategy": s_strat,
                    "temperature": temp
                },
                "metrics": {
                    "win_rate": (agreements / len(config_results)) * 100,
                    "avg_turns": avg_turns,
                    "runs": len(config_results)
                }
            })

        # Save experiment data
        experiment_data = {
            "experiment_id": experiment_id,
            "name": experiment_name,
            "timestamp": datetime.now().isoformat(),
            "configurations": results
        }
        
        file_path = EXPERIMENTS_DIR / f"{experiment_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(experiment_data, f, indent=2)
            
        print(f"DEBUG: Experiment {experiment_id} complete.")
        return experiment_id

    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        file_path = EXPERIMENTS_DIR / f"{experiment_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_experiments(self) -> List[Dict[str, Any]]:
        experiments = []
        for file in EXPERIMENTS_DIR.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                experiments.append({
                    "id": data["experiment_id"],
                    "name": data["name"],
                    "timestamp": data["timestamp"]
                })
        return sorted(experiments, key=lambda x: x["timestamp"], reverse=True)
