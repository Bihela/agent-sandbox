import urllib.request
import json

API_BASE = "http://127.0.0.1:8000"

def post_json(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def get_json(url):
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode('utf-8'))

print("--- POST /scenario/create ---")
try:
    res = post_json(f"{API_BASE}/scenario/create", {
        "name": "Industrial Hub",
        "description": "Custom stakes.",
        "buyer_max": 300,
        "seller_min": 50
    })
    print(res)
except Exception as e:
    print(f"Error: {e}")

print("\n--- GET /scenario/list ---")
try:
    res = get_json(f"{API_BASE}/scenario/list")
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Error: {e}")
