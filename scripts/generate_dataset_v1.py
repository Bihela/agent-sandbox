import requests
import json
import time
import argparse

BASE_URL = "http://localhost:8000"

SCENARIOS = ["price_negotiation", "multi_vendor", "adversarial"]
STRATEGIES = ["aggressive", "balanced", "conservative", "adaptive"]
MODELS = ["mistral", "llama3"]

def run_sweep(runs_per_config=1000, is_test=False):
    print(f"🚀 Starting Research Dataset Generation Sweep (v1)")
    print(f"Dimensions: {len(SCENARIOS)} Scenarios × {len(STRATEGIES)} Strategies × {len(MODELS)} Models")
    print(f"Target: {len(SCENARIOS) * len(STRATEGIES) * len(MODELS) * runs_per_config:,} Simulations\n")

    if not is_test:
        confirm = input(f"⚠️ This will enqueue {len(SCENARIOS) * len(STRATEGIES) * len(MODELS) * runs_per_config:,} simulations. Proceed? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    batch_ids = []

    for scenario_type in SCENARIOS:
        for strategy in STRATEGIES:
            for model in MODELS:
                # Configure the specific run
                config = {
                    "model_name": model,
                    "seed": 42, # Standard seed for v1 dataset
                }

                # Strategy-specific agent config
                agent_cfg = {
                    "strategy": strategy,
                    "risk_level": "medium",
                    "temperature": 0.7
                }

                if scenario_type == "price_negotiation":
                    config["buyer_config"] = agent_cfg
                    config["seller_config"] = agent_cfg # Balanced match
                elif scenario_type == "multi_vendor":
                    config["buyer_config"] = agent_cfg
                    config["agents_configs"] = [agent_cfg, agent_cfg] # Multi-vendor competition
                elif scenario_type == "adversarial":
                    scenario_type = "price_negotiation" # It's a flavor of price neg
                    config["buyer_config"] = agent_cfg
                    config["seller_config"] = agent_cfg
                    config["red_team_config"] = {"enabled": True, "attack_probability": 0.5}

                payload = {
                    "scenario_type": scenario_type,
                    "count": runs_per_config,
                    "priority": 10 if is_test else 0,
                    "config": config
                }

                print(f"  Enqueuing: {scenario_type} | {strategy} | {model} ({runs_per_config} runs)...")
                try:
                    resp = requests.post(f"{BASE_URL}/simulation/schedule", json=payload)
                    if resp.status_code == 200:
                        batch_ids.append(resp.json()["batch_id"])
                    else:
                        print(f"    ❌ Error: {resp.text}")
                except Exception as e:
                    print(f"    ❌ Connection Error: {e}")

    print(f"\n✅ Sweep initialization complete!")
    print(f"Total Batches Enqueued: {len(batch_ids)}")
    print(f"Use 'GET /batch/{{batch_id}}/progress' to track individual sweeps.")
    print(f"Or use 'GET /queue/status' to see overall system load.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Sandbox Dataset Generator v1")
    parser.add_argument("--runs", type=int, default=1000, help="Runs per configuration (default: 1000)")
    parser.add_argument("--test", action="store_true", help="Run a quick test sweep (5 runs each)")
    args = parser.parse_args()

    run_count = 5 if args.test else args.runs
    run_sweep(run_count, is_test=args.test)
