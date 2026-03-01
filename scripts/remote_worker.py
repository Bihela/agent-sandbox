import requests
import time
import os
import sys

# Simulation logic for remote workers
# This worker will connect to the local backend, acquire a job, run it locally on the remote machine, 
# and submit results back.

# --- PATH FIX FOR COLAB/REMOTE ---
# We need to make sure we can find the project modules (world, agents, etc.)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Parent of scripts/
if project_root not in sys.path:
    sys.path.append(project_root)
# ---------------------------------

BACKEND_URL = "http://YOUR_LOCAL_IP:8000" # User will need to replace this

def run_worker():
    print(f"Remote Worker started. Connecting to {BACKEND_URL}")
    
    # To keep it simple, we'll try to import the local project if available, 
    # but for a Colab notebook, we might need a standalone runner.
    
    try:
        from world.world_manager import WorldManager
        from simulation_queue.worker import SimulationWorker
    except ImportError as e:
        print(f"Error: Project modules not found. sys.path is: {sys.path}")
        print(f"Exception: {e}")
        return

    world_manager = WorldManager()
    worker = SimulationWorker(world_manager)

    while True:
        try:
            print("Requesting job...")
            response = requests.post(f"{BACKEND_URL}/queue/acquire")
            if response.status_code == 404:
                print("No jobs available. Waiting 10s...")
                time.sleep(10)
                continue
            
            if response.status_code != 200:
                print(f"Error acquiring job: {response.text}")
                time.sleep(10)
                continue
            
            data = response.json()
            job_data = data["job"]
            job_id = job_data["id"]
            
            print(f"Acquired job {job_id}. Running simulation...")
            
            config = worker._reconstruct_config(job_data["config_json"])
            
            # This is where the actual LLM calls happen
            # Remote worker must have its own GROQ_API_KEY or local Ollama
            
            from scenarios.price_negotiation import PriceNegotiationScenario
            scenario = PriceNegotiationScenario(
                buyer_max=config.buyer_max,
                seller_min=config.seller_min,
                max_turns=config.max_turns
            )
            
            result = world_manager.start_simulation(scenario, config)
            
            print(f"Job {job_id} complete. Submitting results...")
            
            submit_data = {
                "status": "completed",
                "sim_id": result["simulation_id"],
                "result_data": {
                    "simulation_id": result["simulation_id"],
                    "agent_a": result["agent_a"], 
                    "agent_b": result["agent_b"],
                    "status": "agreement" if result["final_price"] else "failure",
                    "turns": result["turns"],
                    "final_price": result["final_price"]
                }
            }
            
            requests.post(f"{BACKEND_URL}/queue/submit/{job_id}", json=submit_data)
            print(f"Results submitted for job {job_id}.")
            
        except Exception as e:
            print(f"Error in remote worker: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BACKEND_URL = sys.argv[1]
    run_worker()
