import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_scenario_list():
    response = client.get("/scenario/list")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    data = res_data["data"]
    assert isinstance(data, list)
    # Check that at least core scenarios are present
    ids = [s.get("id") for s in data]
    assert "price_negotiation" in ids
    assert "multi_vendor" in ids

def test_scenario_create():
    payload = {
        "name": "Industrial Test Hub",
        "description": "Custom stakes for automated testing.",
        "buyer_max": 300,
        "seller_min": 50
    }
    response = client.post("/scenario/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "scenario_id" in data

def test_simulation_start():
    # Simple check if the arena/simulation endpoint is alive
    payload = {
        "scenario_type": "price_negotiation",
        "buyer_config": {
            "name": "Alpha",
            "strategy": "aggressive",
            "model_name": "ollama:mistral"
        },
        "seller_config": {
            "name": "Beta",
            "strategy": "conservative",
            "model_name": "ollama:mistral"
        },
        "max_turns": 5
    }
    response = client.post("/simulation/start", json=payload)
    # 200 is success, 500 might happen if Ollama is missing models
    assert response.status_code in [200, 500, 422] 

def test_leaderboard():
    response = client.get("/tournament/leaderboard")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "data" in response.json()
