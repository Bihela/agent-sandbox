"""
Simulation Configuration System.

Centralizes all tunable parameters for negotiation simulations,
making experiments repeatable and easy to tweak without code changes.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class StrategyType(str, Enum):
    """Agent negotiation strategy presets."""
    AGGRESSIVE = "aggressive"       # Push hard, small concessions
    BALANCED = "balanced"           # Moderate, adaptive approach
    CONSERVATIVE = "conservative"   # Risk-averse, fast agreement
    # Legacy aliases (still valid in API)
    COOPERATIVE = "cooperative"     # → maps to conservative strategy
    ANALYTICAL = "analytical"       # → maps to balanced strategy
    ADAPTIVE = "adaptive"           # → maps to balanced strategy


class RiskLevel(str, Enum):
    """How much risk an agent is willing to take."""
    LOW = "low"           # Conservative, accepts safe deals early
    MEDIUM = "medium"     # Balanced approach
    HIGH = "high"         # Holds out for best possible deal


class NegotiationStyle(str, Enum):
    """The overall tone / approach of the negotiation."""
    FORMAL = "formal"             # Professional, structured offers
    CASUAL = "casual"             # Relaxed, flexible back-and-forth
    COMPETITIVE = "competitive"   # Zero-sum mindset, win at all costs
    COLLABORATIVE = "collaborative"  # Win-win, mutual value seeking


class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    strategy: StrategyType = Field(default=StrategyType.ADAPTIVE, description="Negotiation strategy preset")
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk tolerance")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature (0=deterministic, 2=creative)")


class RedTeamConfig(BaseModel):
    """Configuration for adversarial testing."""
    enabled: bool = Field(default=False, description="Whether to enable Red Team attacks")
    attack_probability: float = Field(default=0.2, ge=0.0, le=1.0, description="Chance of attack per turn")
    attack_types: list[str] = Field(
        default=["wrong_number", "fake_constraint", "protocol_violation", "deceptive_offer"],
        description="List of enabled attack types"
    )


class SimulationConfig(BaseModel):
    """
    Master configuration for a negotiation simulation.
    All fields have sensible defaults so the system works out-of-the-box.
    """

    # ─── Core Settings ───
    buyer_max: float = Field(default=150.0, description="Buyer's maximum budget")
    seller_min: float = Field(default=100.0, description="Seller's minimum acceptable price")
    max_turns: int = Field(default=20, ge=1, le=100, description="Maximum negotiation rounds")

    # ─── Agent Behavior ───
    negotiation_style: NegotiationStyle = Field(
        default=NegotiationStyle.FORMAL,
        description="Overall negotiation tone"
    )
    buyer_config: AgentConfig = Field(default_factory=AgentConfig, description="Buyer agent config")
    seller_config: AgentConfig = Field(default_factory=AgentConfig, description="Seller agent config")
    red_team_config: RedTeamConfig = Field(default_factory=RedTeamConfig, description="Red Team attack config")

    # ─── LLM Settings ───
    model_name: str = Field(default="mistral", description="Ollama model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Global LLM temperature (overridden by per-agent)")

    def get_strategy_prompt(self, strategy: StrategyType) -> str:
        """Returns a prompt modifier based on strategy type."""
        prompts = {
            StrategyType.AGGRESSIVE: "You negotiate aggressively. Make small concessions and push hard for the best deal. Never give more than 5% at a time.",
            StrategyType.COOPERATIVE: "You are a cooperative negotiator. Seek quick agreement and show willingness to meet halfway. Value the relationship.",
            StrategyType.ANALYTICAL: "You are an analytical negotiator. Make calculated, data-driven moves. Take your time and evaluate each offer carefully before responding.",
            StrategyType.ADAPTIVE: "Adapt your strategy based on the opponent's behavior. If they concede, push harder. If they hold firm, show flexibility.",
        }
        return prompts.get(strategy, "")

    def get_risk_prompt(self, risk: RiskLevel) -> str:
        """Returns a prompt modifier based on risk level."""
        prompts = {
            RiskLevel.LOW: "You are risk-averse. Accept reasonable deals early rather than risking a breakdown.",
            RiskLevel.MEDIUM: "You have a balanced risk tolerance. Push for a good deal but know when to settle.",
            RiskLevel.HIGH: "You are a high-risk negotiator. Hold out for the absolute best deal, even if it means the negotiation might fail.",
        }
        return prompts.get(risk, "")

    def get_style_prompt(self) -> str:
        """Returns a prompt modifier based on negotiation style."""
        prompts = {
            NegotiationStyle.FORMAL: "Maintain a professional, structured tone. Be precise with your offers.",
            NegotiationStyle.CASUAL: "Keep it relaxed and conversational. Be flexible in your approach.",
            NegotiationStyle.COMPETITIVE: "This is a zero-sum game. Focus on winning and maximizing your advantage.",
            NegotiationStyle.COLLABORATIVE: "Seek a win-win outcome. Look for mutual value and build trust.",
        }
        return prompts.get(self.negotiation_style, "")


# Default config instance for quick access
DEFAULT_CONFIG = SimulationConfig()
