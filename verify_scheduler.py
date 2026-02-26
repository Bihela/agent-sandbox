import http.client
import json
import time

payload = {
    "scenario_type": "price_negotiation",
    "count": 10,
    "priority": 1,
    "config": {
        "scenario_type": "price_negotiation",
        "buyer_max": 150.0,
        "seller_min": 100.0,
        "model_name": "mistral"
    }
}

def call_api(method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    headers = {"Content-type": "application/json"}
    conn.request(method, path, json.dumps(body) if body else None, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return json.loads(data)

try:
    print("Scheduling 10 simulations...")
    res = call_api("POST", "/simulation/schedule", payload)
    print(f"Response: {res}")

    print("\nMonitoring queue status...")
    for _ in range(12):  # Monitor for 1 minute
        stats = call_api("GET", "/queue/status")
        print(f"Queue Status: {stats['data']}")
        if stats['data']['pending'] == 0 and stats['data']['running'] == 0:
            print("\nAll jobs completed!")
            break
        time.sleep(5)

    print("\nRecent Job Details:")
    recent = call_api("GET", "/queue/recent?limit=5")
    for job in recent['data']:
        print(f"Job {job['id']}: {job['status']} (Sim: {job['sim_id']})")

except Exception as e:
    print(f"Error: {e}")
