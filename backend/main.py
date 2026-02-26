from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from world.world_manager import WorldManager

app = FastAPI()
world_manager = WorldManager()

from scenarios.price_negotiation import PriceNegotiationScenario

class SimulationRequest(BaseModel):
    scenario_type: str = "price_negotiation"
    buyer_max: Optional[float] = 150.0
    seller_min: Optional[float] = 100.0
    max_turns: Optional[int] = 20

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}

@app.post("/simulation/start")
def start_simulation(req: SimulationRequest):
    try:
        if req.scenario_type == "price_negotiation":
            scenario = PriceNegotiationScenario(buyer_max=req.buyer_max, seller_min=req.seller_min, max_turns=req.max_turns)
        else:
            raise ValueError(f"Unknown scenario type: {req.scenario_type}")
        result = world_manager.start_simulation(scenario)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BatchSimulationRequest(SimulationRequest):
    runs: int = 100
    
@app.post("/simulation/batch")
def start_batch_simulation(req: BatchSimulationRequest):
    try:
        if req.scenario_type == "price_negotiation":
            scenario = PriceNegotiationScenario(buyer_max=req.buyer_max, seller_min=req.seller_min, max_turns=req.max_turns)
        else:
            raise ValueError(f"Unknown scenario type: {req.scenario_type}")
        if req.runs <= 0 or req.runs > 1000:
             raise ValueError("Runs must be between 1 and 1000")
        result = world_manager.run_batch_simulations(scenario, req.runs)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulation/replay")
def get_all_replays():
    return {"status": "success", "data": world_manager.get_all_replays()}

@app.get("/simulation/{sim_id}")
def get_simulation(sim_id: str):
    result = world_manager.get_simulation(sim_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"status": "success", "data": result}

app.mount("/play", StaticFiles(directory="frontend", html=True), name="frontend")
