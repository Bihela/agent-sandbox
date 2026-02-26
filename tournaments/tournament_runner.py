import asyncio
from typing import Any, Optional
from world.world_manager import WorldManager
from scenarios.price_negotiation import PriceNegotiationScenario
from configs.simulation_config import SimulationConfig, AgentConfig, StrategyType, RiskLevel, NegotiationStyle
from tournaments.leaderboard import Leaderboard

class TournamentRunner:
    def __init__(self, world_manager: WorldManager):
        self.world_manager = world_manager
        self.leaderboard = Leaderboard()

    async def run_tournament(self, 
                               strategies: list[str], 
                               models: list[str], 
                               runs_per_match: int = 1,
                               buyer_max: float = 150.0,
                               seller_min: float = 100.0) -> dict[str, Any]:
        """
        Runs a round-robin tournament between all strategy combinations.
        """
        results = []
        total_simulations = len(strategies) * len(strategies) * len(models) * runs_per_match
        
        # Scenario setup
        scenario = PriceNegotiationScenario(buyer_max=buyer_max, seller_min=seller_min, max_turns=20)
        
        for model in models:
            for b_strat in strategies:
                for s_strat in strategies:
                    print(f"DEBUG: Matchup: Buyer({b_strat}) vs Seller({s_strat}) on {model}")
                    for i in range(runs_per_match):
                        print(f"DEBUG: Run {i+1}/{runs_per_match}")
                        # Create config
                        config = SimulationConfig(
                            buyer_max=buyer_max,
                            seller_min=seller_min,
                            max_turns=20,
                            negotiation_style=NegotiationStyle.FORMAL,
                            buyer_config=AgentConfig(
                                strategy=StrategyType(b_strat),
                                risk_level=RiskLevel.MEDIUM,
                                temperature=0.7
                            ),
                            seller_config=AgentConfig(
                                strategy=StrategyType(s_strat),
                                risk_level=RiskLevel.MEDIUM,
                                temperature=0.7
                            ),
                            model_name=model,
                            temperature=0.7
                        )
                        
                        # run simulation (sync call in WorldManager)
                        # In a real async environment we might wrap this, 
                        # but WorldManager.start_simulation is currently synchronous.
                        res = self.world_manager.start_simulation(scenario, config)
                        
                        # Record in leaderboard
                        self.leaderboard.record_simulation(b_strat, s_strat, model, res)
                        
                        results.append({
                            "buyer": b_strat,
                            "seller": s_strat,
                            "model": model,
                            "status": res["status"],
                            "final_price": res["final_price"],
                            "turns": res["turns"]
                        })
        
        return {
            "total_simulations": len(results),
            "matchups": results,
            "rankings": self.leaderboard.get_rankings()
        }
