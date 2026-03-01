import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_research_pivot():
    print("--- Testing Research Pivot Features ---")
    
    # 1. Enqueue a batch
    payload = {
        "scenario_type": "price_negotiation",
        "count": 2,
        "config": {
            "buyer_max": 150.0,
            "seller_min": 100.0,
            "max_turns": 3,
            "seed": 42
        }
    }
    print(f"Enqueuing batch of 2 simulations with seed 42...")
    resp = requests.post(f"{BASE_URL}/simulation/schedule", json=payload)
    if resp.status_code != 200:
        print(f"FAILED to enqueue: {resp.text}")
        return
    
    data = resp.json()
    batch_id = data.get("batch_id")
    print(f"SUCCESS! Batch ID: {batch_id}")
    
    # 2. Check progress
    print(f"Checking progress for batch {batch_id}...")
    time.sleep(2) # Give it a second to start
    progress_resp = requests.get(f"{BASE_URL}/batch/{batch_id}/progress")
    if progress_resp.status_code == 200:
        print("Progress Data:", json.dumps(progress_resp.json()["data"], indent=2))
    else:
        print(f"FAILED to get progress: {progress_resp.text}")

if __name__ == "__main__":
    test_research_pivot()
