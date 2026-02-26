import time
import threading
import logging
import traceback
from simulation_queue.queue_manager import get_next_job, update_job_status
from world.world_manager import WorldManager
from scenarios.price_negotiation import PriceNegotiationScenario
from scenarios.multi_vendor_negotiation import MultiVendorNegotiationScenario
from configs.simulation_config import SimulationConfig, AgentConfig, RedTeamConfig

logger = logging.getLogger("simulation_worker")
logger.setLevel(logging.INFO)

class SimulationWorker(threading.Thread):
    """Background thread that consumes and executes simulation jobs."""

    def __init__(self, world_manager: WorldManager):
        super().__init__(daemon=True, name="SimulationWorker")
        self.world_manager = world_manager
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        logger.info("Simulation worker started.")
        while self.running:
            try:
                job = get_next_job()
                if not job:
                    time.sleep(5)  # Idle wait
                    continue

                logger.info(f"Processing job {job.id}...")
                update_job_status(job.id, "running")

                try:
                    # 1. Reconstruct Scenario and Config
                    config_dict = job.config_json
                    scenario_type = job.scenario_type
                    
                    # Map config dict to SimulationConfig object
                    # We'll use a helper to reconstruct complex nested configs
                    config = self._reconstruct_config(config_dict)
                    
                    if scenario_type == "price_negotiation":
                        scenario = PriceNegotiationScenario(
                            buyer_max=config.buyer_max,
                            seller_min=config.seller_min,
                            max_turns=config.max_turns
                        )
                    elif scenario_type == "multi_vendor":
                        scenario = MultiVendorNegotiationScenario(
                            num_vendors=len([a for a in config.agents_configs if a.role == "seller"]) if config.agents_configs else 1,
                            buyer_max=config.buyer_max,
                            seller_min=config.seller_min
                        )
                    else:
                        raise ValueError(f"Unknown scenario type: {scenario_type}")

                    # 2. Run simulation
                    result = self.world_manager.start_simulation(scenario, config)
                    
                    # 3. Update job status
                    update_job_status(job.id, "completed", sim_id=result["simulation_id"])
                    logger.info(f"Job {job.id} completed successfully.")

                except Exception as e:
                    logger.error(f"Error executing job {job.id}: {str(e)}")
                    # traceback.print_exc()
                    update_job_status(job.id, "failed", error=str(e))

            except Exception as e:
                logger.error(f"Worker critical error: {str(e)}")
                time.sleep(10)

    def _reconstruct_config(self, d: dict) -> SimulationConfig:
        """Deep reconstruct SimulationConfig from dict."""
        kwargs = {
            "buyer_max": d.get("buyer_max", 150.0),
            "seller_min": d.get("seller_min", 100.0),
            "max_turns": d.get("max_turns", 20),
            "negotiation_style": d.get("negotiation_style", "formal"),
            "model_name": d.get("model_name", "mistral"),
            "temperature": d.get("temperature", 0.7),
        }

        if "buyer_config" in d and d["buyer_config"]:
            kwargs["buyer_config"] = AgentConfig(**d["buyer_config"])
        
        if "seller_config" in d and d["seller_config"]:
            kwargs["seller_config"] = AgentConfig(**d["seller_config"])

        if "agents_configs" in d and d["agents_configs"]:
            kwargs["agents_configs"] = [AgentConfig(**a) for a in d["agents_configs"]]

        if "red_team_config" in d and d["red_team_config"]:
            # Handle attack_types list if present
            red_data = d["red_team_config"]
            kwargs["red_team_config"] = RedTeamConfig(**red_data)

        return SimulationConfig(**kwargs)
