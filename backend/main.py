"""
Agent Sandbox Backend
----------------------
Core API server for the Agent Sandbox ecosystem. This module provides endpoints for 
simulation orchestration, tournament management, and research-grade analytics.
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from world.world_manager import WorldManager
from agents.llm_agent import LLMBuyerAgent, LLMSellerAgent
from configs.simulation_config import SimulationConfig, AgentConfig, StrategyType, RiskLevel, NegotiationStyle, RedTeamConfig
from scenarios.price_negotiation import PriceNegotiationScenario
from scenarios.multi_vendor_negotiation import MultiVendorNegotiationScenario
from scenarios.dynamic_scenario import DynamicScenario
from tournaments.tournament_runner import TournamentRunner
from tournaments.leaderboard import Leaderboard
from experiments.experiment_runner import ExperimentRunner
from telemetry_module.telemetry import tracer, collector
from simulation_queue.queue_manager import QueueManager
from simulation_queue.worker import SimulationWorker
import logging
import threading
import json
import os
from dotenv import load_dotenv

load_dotenv()

SCENARIOS_FILE = "data/scenarios.json"

app = FastAPI()
world_manager = WorldManager()
tournament_runner = TournamentRunner(world_manager)
leaderboard = Leaderboard()
experiment_runner = ExperimentRunner(world_manager)

worker = None

@app.on_event("startup")
def startup_event():
    """Initializes background workers and logging on application startup."""
    global worker
    worker = SimulationWorker(world_manager)
    worker.start()
    logging.info("Background simulation worker initialized.")

@app.on_event("shutdown")
def shutdown_event():
    """Gracefully shuts down background workers on application exit."""
    if worker:
        worker.stop()
    if worker:
        worker.stop()


class AgentConfigRequest(BaseModel):
    """Request model for defining a single agent's configuration."""
    name: Optional[str] = None
    role: str = "negotiator"
    strategy: str = "adaptive"
    risk_level: str = "medium"
    model_name: Optional[str] = None
    temperature: float = 0.7


class RedTeamConfigRequest(BaseModel):
    enabled: bool = False
    attack_probability: float = 0.2

class SimulationRequest(BaseModel):
    """Parameters for initiating a new negotiation simulation."""
    scenario_type: str = "price_negotiation"
    buyer_max: Optional[float] = 150.0
    seller_min: Optional[float] = 100.0
    num_vendors: Optional[int] = 2
    max_turns: Optional[int] = 20
    negotiation_style: Optional[str] = "formal"
    model_name: Optional[str] = "mistral"
    temperature: Optional[float] = 0.7
    buyer_config: Optional[AgentConfigRequest] = None
    seller_config: Optional[AgentConfigRequest] = None
    agents_configs: Optional[List[AgentConfigRequest]] = None
    red_team_config: Optional[RedTeamConfigRequest] = None

class ScheduleRequest(BaseModel):
    scenario_type: str = "price_negotiation"
    count: int = 1
    priority: int = 0
    config: SimulationRequest

class BattleRequest(BaseModel):
    buyer_config: AgentConfigRequest
    seller_config: AgentConfigRequest
    model_name: str = "mistral"
    buyer_max: float = 150.0
    seller_min: float = 100.0
    negotiation_style: str = "formal"

class ScenarioCreateRequest(BaseModel):
    name: str
    description: str
    buyer_max: float = 150.0
    seller_min: float = 100.0
    num_vendors: int = 1
    max_turns: int = 20
    goal: str = "maximize_efficiency"
    custom_params: Dict[str, Any] = {}

ScenarioCreateRequest.model_rebuild()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}


# ─── Tournament Endpoints ───

@app.post("/tournament/run")
async def run_tournament(req: Dict):
    """Orchestrates an automated round-robin tournament between strategies."""
    try:
        # Extract fields from dict
        strategies = req.get("strategies", ["aggressive", "balanced", "conservative", "adaptive"])
        models = req.get("models", ["mistral"])
        runs_per_match = req.get("runs_per_match", 1)
        buyer_max = req.get("buyer_max", 150.0)
        seller_min = req.get("seller_min", 100.0)

        results = await tournament_runner.run_tournament(
            strategies=strategies,
            models=models,
            runs_per_match=runs_per_match,
            buyer_max=buyer_max,
            seller_min=seller_min
        )
        return {"status": "success", "data": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Experiment Endpoints ───

@app.post("/experiment/run")
async def run_experiment(req: Dict):
    """Initiates a parameter sweep experiment across multiple LLM configurations."""
    try:
        experiment_id = await experiment_runner.run_parameter_sweep(
            experiment_name=req.get("name", "Unnamed Experiment"),
            strategies=req.get("strategies", ["balanced"]),
            temperatures=req.get("temperatures", [0.7]),
            models=req.get("models", ["mistral"]),
            runs_per_config=req.get("runs_per_config", 1)
        )
        return {"status": "success", "experiment_id": experiment_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiment/list")
def list_experiments():
    return {"status": "success", "data": experiment_runner.list_experiments()}

@app.get("/experiment/results/{experiment_id}")
def get_experiment_results(experiment_id: str):
    res = experiment_runner.get_experiment_results(experiment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"status": "success", "data": res}

# ─── Scenario Builder Endpoints ───

@app.post("/scenario/create")
def create_scenario(req: ScenarioCreateRequest):
    """Persists a new user-defined negotiation scenario to the library."""
    try:
        scenarios = []
        if os.path.exists(SCENARIOS_FILE):
            with open(SCENARIOS_FILE, "r") as f:
                scenarios = json.load(f)
        
        # Create unique ID from name
        scenario_id = req.name.lower().replace(" ", "_")
        
        new_scenario = {
            "id": scenario_id,
            **req.dict()
        }
        
        # Check if exists and update or append
        existing_idx = next((i for i, s in enumerate(scenarios) if s["id"] == scenario_id), None)
        if existing_idx is not None:
            scenarios[existing_idx] = new_scenario
        else:
            scenarios.append(new_scenario)
            
        with open(SCENARIOS_FILE, "w") as f:
            json.dump(scenarios, f, indent=4)
            
        return {"status": "success", "scenario_id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenario/list")
def list_scenarios():
    core_scenarios = [
        {"id": "price_negotiation", "name": "Standard Price Negotiation", "description": "1-on-1 negotiation", "type": "core"},
        {"id": "multi_vendor", "name": "Multi-Vendor Competition", "description": "1 Buyer vs N Sellers", "type": "core"}
    ]
    custom_scenarios = []
    if os.path.exists(SCENARIOS_FILE):
        try:
            with open(SCENARIOS_FILE, "r") as f:
                custom_scenarios = json.load(f)
                for s in custom_scenarios:
                    s["type"] = "custom"
        except:
            pass
            
    return {"status": "success", "data": core_scenarios + custom_scenarios}

@app.post("/simulation/start")
def start_simulation(req: SimulationRequest):
    """Stateful entry point for starting a real-time negotiation simulation."""
    try:
        if req.scenario_type == "price_negotiation":
            scenario = PriceNegotiationScenario(buyer_max=req.buyer_max, seller_min=req.seller_min, max_turns=req.max_turns)
        elif req.scenario_type == "multi_vendor":
            scenario = MultiVendorNegotiationScenario(buyer_max=req.buyer_max, seller_min=req.seller_min, num_vendors=req.num_vendors)
        else:
            # Check dynamic scenarios
            found_scenario = None
            if os.path.exists(SCENARIOS_FILE):
                with open(SCENARIOS_FILE, "r") as f:
                    scenarios = json.load(f)
                    found_scenario = next((s for s in scenarios if s["id"] == req.scenario_type), None)
            
            if found_scenario:
                scenario = DynamicScenario(
                    name=found_scenario["name"],
                    description=found_scenario["description"],
                    buyer_max=found_scenario.get("buyer_max", 150.0),
                    seller_min=found_scenario.get("seller_min", 100.0),
                    num_vendors=found_scenario.get("num_vendors", 1),
                    max_turns=found_scenario.get("max_turns", 20),
                    goal=found_scenario.get("goal", "maximize_efficiency"),
                    custom_params=found_scenario.get("custom_params", {})
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unknown scenario type: {req.scenario_type}")

        # Build SimulationConfig from request
        temp = req.temperature if req.temperature is not None else 0.7

        agents_list = []
        if req.agents_configs:
            for ac in req.agents_configs:
                agents_list.append(AgentConfig(
                    name=ac.name,
                    role=ac.role,
                    strategy=StrategyType(ac.strategy or "adaptive"),
                    risk_level=RiskLevel(ac.risk_level or "medium"),
                    temperature=ac.temperature if ac.temperature is not None else temp
                ))

        buyer_agent_cfg = None
        if req.buyer_config:
            buyer_agent_cfg = AgentConfig(
                strategy=StrategyType(req.buyer_config.strategy or "adaptive"),
                risk_level=RiskLevel(req.buyer_config.risk_level or "medium"),
                temperature=req.buyer_config.temperature if req.buyer_config.temperature is not None else temp,
            )
        else:
            buyer_agent_cfg = AgentConfig(strategy=StrategyType.ADAPTIVE, risk_level=RiskLevel.MEDIUM, temperature=temp)
            
        seller_agent_cfg = None
        if req.seller_config:
            seller_agent_cfg = AgentConfig(
                strategy=StrategyType(req.seller_config.strategy or "adaptive"),
                risk_level=RiskLevel(req.seller_config.risk_level or "medium"),
                temperature=req.seller_config.temperature if req.seller_config.temperature is not None else temp,
            )
        else:
            seller_agent_cfg = AgentConfig(strategy=StrategyType.ADAPTIVE, risk_level=RiskLevel.MEDIUM, temperature=temp)

        # Red Team Config
        red_team_cfg = RedTeamConfig(
            enabled=req.red_team_config.enabled if req.red_team_config else False,
            attack_probability=req.red_team_config.attack_probability if req.red_team_config else 0.2
        )

        config = SimulationConfig(
            buyer_max=req.buyer_max or 150.0,
            seller_min=req.seller_min or 100.0,
            max_turns=req.max_turns or 20,
            negotiation_style=NegotiationStyle(req.negotiation_style or "formal"),
            buyer_config=buyer_agent_cfg,
            seller_config=seller_agent_cfg,
            agents_configs=agents_list,
            model_name=req.model_name or "mistral",
            temperature=temp,
            red_team_config=red_team_cfg
        )

        result = world_manager.start_simulation(scenario, config)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulation/schedule")
def schedule_simulation(req: ScheduleRequest):
    """Enqueues one or many simulations for background execution."""
    try:
        # Convert Pydantic request to dict for storage
        config_dict = req.config.dict()
        jobs = QueueManager.schedule_simulations(
            scenario_type=req.scenario_type,
            config=config_dict,
            count=req.count,
            priority=req.priority
        )
        return {
            "status": "success", 
            "message": f"Enqueued {len(jobs)} simulations.",
            "job_ids": [j.id for j in jobs]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/status")
def get_queue_status():
    """Returns summarized stats of the simulation queue."""
    return {"status": "success", "data": QueueManager.get_queue_stats()}

@app.get("/queue/recent")
def get_recent_jobs(limit: int = 50):
    """Returns detailed status of recent jobs."""
    return {"status": "success", "data": QueueManager.get_recent_jobs(limit)}


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
def get_available_options():
    try:
        from agents.strategies import list_strategies
        from agents.providers.provider_factory import ProviderFactory
        
        # Aggregate models from all providers
        all_models = []
        providers = ["ollama", "openai", "gemini", "groq"]
        
        for p_name in providers:
            try:
                p = ProviderFactory.get_provider(p_name)
                p_models = p.get_available_models()
                for m in p_models:
                    all_models.append(f"{p_name}:{m}")
            except Exception:
                pass

        if not all_models:
            all_models = ["ollama:mistral", "ollama:llama3"]

        return {
            "models": all_models,
            "strategies": list_strategies(),
            "risk_levels": [r.value for r in RiskLevel],
            "negotiation_styles": [n.value for n in NegotiationStyle]
        }
    except Exception as e:
        return {"error": str(e)}

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

@app.get("/agents/cards")
def get_agent_cards():
    """Agent discovery — returns all registered agent cards."""
    from agents.card_loader import load_all_cards, check_compatibility
    cards = load_all_cards()
    # Auto-generate compatibility report if we have buyer + seller
    buyer = next((c for c in cards if c.get("role") == "buyer"), None)
    seller = next((c for c in cards if c.get("role") == "seller"), None)
    compat = check_compatibility(buyer, seller) if buyer and seller else None
    return {
        "status": "success",
        "agents": cards,
        "compatibility": compat,
    }

# ─── Tournament Endpoints ───

@app.get("/tournament/leaderboard")
def get_leaderboard():
    return {"status": "success", "data": leaderboard.get_rankings()}

@app.post("/tournament/battle")
def start_arena_battle(req: BattleRequest):
    """Runs a single 1v1 battle between specific configs and updates the leaderboard."""
    try:
        # Create Scenario
        scenario = PriceNegotiationScenario(
            buyer_max=req.buyer_max,
            seller_min=req.seller_min,
            max_turns=20
        )
        
        # Extract provider name from model_name (e.g., "ollama:mistral" -> "ollama")
        b_model = req.buyer_config.model_name if req.buyer_config and req.buyer_config.model_name else req.model_name
        s_model = req.seller_config.model_name if req.seller_config and req.seller_config.model_name else req.model_name
        
        b_provider = b_model.split(":")[0] if ":" in b_model else "ollama"
        s_provider = s_model.split(":")[0] if ":" in s_model else "ollama"

        # Create LLM Agents
        buyer = LLMBuyerAgent(
            name="Alice (LLM Buyer)",
            max_price=scenario.buyer_max,
            model=b_model,
            provider_name=b_provider,
            strategy_name=req.buyer_config.strategy,
            risk_prompt=req.buyer_config.risk_level,
            style_prompt=req.negotiation_style
        )
        
        seller = LLMSellerAgent(
            name="Bob (LLM Seller)",
            min_price=scenario.seller_min,
            model=s_model,
            provider_name=s_provider,
            strategy_name=req.seller_config.strategy,
            risk_prompt=req.seller_config.risk_level,
            style_prompt=req.negotiation_style
        )

        # Create Config
        config = SimulationConfig(
            buyer_max=req.buyer_max,
            seller_min=req.seller_min,
            max_turns=20,
            negotiation_style=NegotiationStyle.FORMAL,
            buyer_config=AgentConfig(
                strategy=StrategyType(req.buyer_config.strategy or "balanced"),
                risk_level=RiskLevel(req.buyer_config.risk_level or "medium"),
                temperature=req.buyer_config.temperature
            ),
            seller_config=AgentConfig(
                strategy=StrategyType(req.seller_config.strategy or "balanced"),
                risk_level=RiskLevel(req.seller_config.risk_level or "medium"),
                temperature=req.seller_config.temperature
            ),
            model_name=req.model_name,
            temperature=req.buyer_config.temperature # Defaulting to buyer's if needed, or use model global
        )
        
        # Run Simulation
        result = world_manager.start_simulation(scenario, config)
        
        # Record in Leaderboard
        leaderboard.record_simulation(
            req.buyer_config.strategy, 
            req.seller_config.strategy, 
            req.model_name, 
            result
        )
        
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/play", StaticFiles(directory="frontend", html=True), name="frontend")
