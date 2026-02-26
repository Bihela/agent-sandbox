from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from world.world_manager import WorldManager
from configs.simulation_config import SimulationConfig, AgentConfig, StrategyType, RiskLevel, NegotiationStyle

app = FastAPI()
world_manager = WorldManager()

from scenarios.price_negotiation import PriceNegotiationScenario


class AgentConfigRequest(BaseModel):
    strategy: str = "adaptive"
    risk_level: str = "medium"
    temperature: float = 0.7


class SimulationRequest(BaseModel):
    scenario_type: str = "price_negotiation"
    buyer_max: Optional[float] = 150.0
    seller_min: Optional[float] = 100.0
    max_turns: Optional[int] = 20
    # Config fields
    negotiation_style: Optional[str] = "formal"
    model_name: Optional[str] = "mistral"
    temperature: Optional[float] = 0.7
    buyer_config: Optional[AgentConfigRequest] = None
    seller_config: Optional[AgentConfigRequest] = None


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

        # Build SimulationConfig from request
        temp = req.temperature if req.temperature is not None else 0.7

        buyer_agent_cfg = AgentConfig(
            strategy=StrategyType(req.buyer_config.strategy if req.buyer_config else "adaptive"),
            risk_level=RiskLevel(req.buyer_config.risk_level if req.buyer_config else "medium"),
            temperature=req.buyer_config.temperature if (req.buyer_config and req.buyer_config.temperature is not None) else temp,
        )
        seller_agent_cfg = AgentConfig(
            strategy=StrategyType(req.seller_config.strategy if req.seller_config else "adaptive"),
            risk_level=RiskLevel(req.seller_config.risk_level if req.seller_config else "medium"),
            temperature=req.seller_config.temperature if (req.seller_config and req.seller_config.temperature is not None) else temp,
        )

        config = SimulationConfig(
            buyer_max=req.buyer_max or 150.0,
            seller_min=req.seller_min or 100.0,
            max_turns=req.max_turns or 20,
            negotiation_style=NegotiationStyle(req.negotiation_style or "formal"),
            buyer_config=buyer_agent_cfg,
            seller_config=seller_agent_cfg,
            model_name=req.model_name or "mistral",
            temperature=temp,
        )

        result = world_manager.start_simulation(scenario, config)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
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

@app.get("/config/options")
def get_config_options():
    """Returns all available config options for the frontend dropdowns."""
    from agents.strategies import list_strategies
    return {
        "strategies": list_strategies(),
        "risk_levels": [e.value for e in RiskLevel],
        "negotiation_styles": [e.value for e in NegotiationStyle],
    }

@app.get("/telemetry")
def get_telemetry():
    """Returns global telemetry metrics across all simulations."""
    from telemetry_module.telemetry import collector
    return {"status": "success", "data": collector.get_global_metrics()}

@app.get("/dataset/export")
def export_dataset(format: str = "json"):
    """
    Export all simulation data as a flat dataset.
    ?format=json → JSON array of rows
    ?format=csv  → downloadable CSV file
    """
    from fastapi.responses import Response
    from metrics.dataset_exporter import export_to_rows, export_to_csv_string

    replays = world_manager.get_all_replays()
    if not replays:
        raise HTTPException(status_code=404, detail="No simulations to export. Run some first!")

    if format.lower() == "csv":
        csv_data = export_to_csv_string(replays)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=agent_sandbox_dataset.csv"}
        )
    else:
        rows = export_to_rows(replays)
        return {"status": "success", "total_rows": len(rows), "data": rows}

app.mount("/play", StaticFiles(directory="frontend", html=True), name="frontend")
