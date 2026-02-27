import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

LEADERBOARD_FILE = Path("data/leaderboard.json")

class Leaderboard:
    def __init__(self):
        self.data_dir = LEADERBOARD_FILE.parent
        self.data_dir.mkdir(exist_ok=True)
        self._load()

    def _load(self):
        if LEADERBOARD_FILE.exists():
            try:
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except:
                self.stats = {"strategies": {}, "models": {}, "h2h_strategies": {}, "h2h_models": {}, "last_updated": None}
        else:
            self.stats = {"strategies": {}, "models": {}, "h2h_strategies": {}, "h2h_models": {}, "last_updated": None}

        # Initialize missing fields for backward compatibility
        if "h2h_strategies" not in self.stats: self.stats["h2h_strategies"] = {}
        if "h2h_models" not in self.stats: self.stats["h2h_models"] = {}

    def _save(self):
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

    def record_simulation(self, buyer_strategy: str, seller_strategy: str, model: str, result: dict):
        """Record a single simulation result for the leaderboard."""
        status = result.get("status")
        turns = result.get("turns", 0)
        final_price = result.get("final_price")

        # 1. Update general strategy stats
        for strat in [buyer_strategy, seller_strategy]:
            if strat not in self.stats["strategies"]:
                self.stats["strategies"][strat] = {
                    "runs": 0, "agreements": 0, "total_turns": 0
                }
            s_obj = self.stats["strategies"][strat]
            s_obj["runs"] += 1
            s_obj["total_turns"] += turns
            if status == "agreement":
                s_obj["agreements"] += 1

        # 2. Update model stats
        if model not in self.stats["models"]:
            self.stats["models"][model] = {"runs": 0, "agreements": 0, "avg_latency_ms": 0}
        
        m_obj = self.stats["models"][model]
        m_obj["runs"] += 1
        if status == "agreement":
            m_obj["agreements"] += 1
            
        latency = result.get("telemetry", {}).get("avg_decision_latency_ms", 0)
        if latency:
            m_obj["avg_latency_ms"] = (m_obj["avg_latency_ms"] * (m_obj["runs"]-1) + latency) / m_obj["runs"]

        # 3. Update H2H Strategy Stats (Buyer vs Seller)
        h2h_strat_key = f"{buyer_strategy}_vs_{seller_strategy}"
        if h2h_strat_key not in self.stats["h2h_strategies"]:
            self.stats["h2h_strategies"][h2h_strat_key] = {"runs": 0, "agreements": 0}
        self.stats["h2h_strategies"][h2h_strat_key]["runs"] += 1
        if status == "agreement":
            self.stats["h2h_strategies"][h2h_strat_key]["agreements"] += 1

        self._save()

    def get_rankings(self) -> Dict[str, Any]:
        """Return formatted rankings for the UI."""
        strategy_list = []
        for name, data in self.stats["strategies"].items():
            runs = data["runs"]
            strategy_list.append({
                "name": name,
                "win_rate": round((data["agreements"] / runs * 100), 1) if runs > 0 else 0,
                "avg_turns": round(data["total_turns"] / runs, 1) if runs > 0 else 0,
                "total_runs": runs
            })
        
        # Sort by win rate then runs
        strategy_list.sort(key=lambda x: (x["win_rate"], x["total_runs"]), reverse=True)

        model_list = []
        for name, data in self.stats.get("models", {}).items():
            runs = data["runs"]
            model_list.append({
                "name": name,
                "win_rate": round((data["agreements"] / runs * 100), 1) if runs > 0 else 0,
                "avg_latency": round(data.get("avg_latency_ms", 0), 1),
                "total_runs": runs
            })
        model_list.sort(key=lambda x: x["win_rate"], reverse=True)
        
        return {
            "strategies": strategy_list,
            "models": model_list,
            "h2h_strategies": self.stats.get("h2h_strategies", {}),
            "last_updated": self.stats["last_updated"]
        }
