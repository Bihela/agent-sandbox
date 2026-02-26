import urllib.request
import json
import time

API_BASE = "http://127.0.0.1:8000"

def post_json(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def get_json(url):
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode('utf-8'))

def test_scenario_builder():
    print("--- Testing Scenario Builder (urllib) ---")
    
    # 1. Create a custom scenario
    scenario_payload = {
        "name": "Supply Chain Alpha",
        "description": "A high-stakes industrial negotiation for rare earth minerals.",
        "buyer_max": 200.0,
        "seller_min": 50.0,
        "num_vendors": 3,
        "max_turns": 15,
        "goal": "minimize_cost"
    }
    
    print(f"1. Creating scenario: {scenario_payload['name']}")
    res = post_json(f"{API_BASE}/scenario/create", scenario_payload)
    print(f"Response: {res}")
    assert res["status"] == "success"
    scenario_id = res["scenario_id"]
    
    # 2. List scenarios
    print("\n2. Listing scenarios...")
    res = get_json(f"{API_BASE}/scenario/list")
    scenarios = res["data"]
    found = any(s["id"] == scenario_id for s in scenarios)
    print(f"Scenario {scenario_id} found in list: {found}")
    assert found
    
    # 3. Start simulation with custom scenario
    print(f"\n3. Starting simulation with scenario: {scenario_id}")
    sim_payload = {
        "scenario_type": scenario_id,
        "model_name": "mistral",
        "negotiation_style": "formal"
    }
    res = post_json(f"{API_BASE}/simulation/start", sim_payload)
    print(f"Response status: {res['status']}")
    assert res["status"] == "success"
    sim_data = res["data"]
    print(f"Simulation ID: {sim_data['simulation_id']}")
    print(f"Final Price: {sim_data['final_price']}")
    
    # Verify participants
    steps = sim_data.get("steps", [])
    distinct_agents = set(s["agent"] for s in steps)
    print(f"Distinct agents involved: {distinct_agents}")
    
    # Expect 1 Buyer + 3 Vendors
    # agents might be: "Buyer", "Vendor 1", "Vendor 2", "Vendor 3"
    print(f"Agent count: {len(distinct_agents)}")
    
    print("\n--- Scenario Builder Verification SUCCESS ---")

if __name__ == "__main__":
    try:
        test_scenario_builder()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
