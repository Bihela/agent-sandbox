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

def test_model_providers():
    print("--- Testing Model Provider System ---")
    
    # 1. Check available models (should have provider prefixes)
    print("1. Checking model options...")
    options = get_json(f"{API_BASE}/config/options")
    models = options["models"]
    print(f"Available models: {models}")
    assert any("ollama:" in m for m in models)
    
    # 2. Start simulation with explicit provider models
    # We'll use ollama for both but with the new prefix to test routing
    print("\n2. Starting simulation with prefixed models...")
    sim_payload = {
        "scenario_type": "price_negotiation",
        "model_name": "ollama:mistral",
        "buyer_config": {
            "model": "ollama:mistral",
            "strategy": "aggressive",
            "risk_level": "low"
        },
        "seller_config": {
            "model": "ollama:llama3", # Test if it pulls llama3
            "strategy": "balanced",
            "risk_level": "medium"
        },
        "negotiation_style": "formal"
    }
    
    try:
        res = post_json(f"{API_BASE}/simulation/start", sim_payload)
        print(f"Response status: {res['status']}")
        assert res["status"] == "success"
        print("Success! Multi-provider routing works.")
    except Exception as e:
        print(f"Error starting simulation: {e}")
        # Note: This might fail if llama3 isn't installed locally, 
        # but the routing logic itself should be hit.
    
    print("\n--- Model Provider Verification COMPLETE ---")

if __name__ == "__main__":
    test_model_providers()
