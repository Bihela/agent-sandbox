import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def verify_tournament():
    print("--- Verifying Tournament API (urllib) ---")
    payload = {
        "strategies": ["aggressive", "balanced"],
        "models": ["mistral"],
        "runs_per_match": 1
    }
    
    try:
        # 1. Run Tournament
        print(f"POST {BASE_URL}/tournament/run ...")
        req = urllib.request.Request(
            f"{BASE_URL}/tournament/run", 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
            print(f"Success! Total simulations: {data['data']['total_simulations']}")
        
        # 2. Check Leaderboard
        print(f"GET {BASE_URL}/tournament/leaderboard ...")
        with urllib.request.urlopen(f"{BASE_URL}/tournament/leaderboard") as response:
            lb_data = json.loads(response.read().decode())
            
        strategies = lb_data['data']['strategies']
        print(f"Leaderboard updated with {len(strategies)} strategies.")
        for s in strategies:
            print(f" - {s['name']}: Win Rate {s['win_rate']}%, Runs {s['total_runs']}")
            
        return True
    except Exception as e:
        print(f"Verification FAILED: {e}")
        return False

if __name__ == "__main__":
    # Wait a moment for server to be ready
    time.sleep(1)
    verify_tournament()
