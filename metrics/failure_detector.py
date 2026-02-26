"""
Failure Taxonomy Engine for Agent Negotiation Simulations.

Detects 5 categories of negotiation failure:
  - loop_failure:         Repeated identical prices or stagnant price movement
  - deadlock:             Diverging prices or gap not narrowing
  - irrational_concession: Agent acts against own interests (buyer overpays, seller undersells)
  - invalid_action:       Unrecognized action type or malformed message structure
  - protocol_violation:   Breaks negotiation protocol rules (e.g. accept with no price on table)
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class FailureSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FailureType(str, Enum):
    LOOP_FAILURE = "loop_failure"
    DEADLOCK = "deadlock"
    IRRATIONAL_CONCESSION = "irrational_concession"
    INVALID_ACTION = "invalid_action"
    PROTOCOL_VIOLATION = "protocol_violation"


VALID_ACTIONS = {"proposal", "counter_proposal", "acceptance", "rejection", "information", "challenge"}


class FailureDetector:
    """
    Analyzes a completed negotiation transcript and produces a FailureReport
    containing all detected failures and an overall risk score.
    """

    def __init__(self):
        self._failures: List[Dict[str, Any]] = []

    # ───────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────

    def analyze(self, steps: List[dict], buyer_max: float, seller_min: float) -> dict:
        """
        Run all 5 detectors over the full step history.

        Args:
            steps:      List of step dicts from the world manager
                        [{"turn": int, "agent": str, "action": {...}}, ...]
            buyer_max:  The buyer's maximum budget
            seller_min: The seller's minimum acceptable price

        Returns:
            FailureReport dict:
            {
                "failures": [...],
                "risk_score": float (0-100),
                "summary": str
            }
        """
        self._failures = []

        self._detect_invalid_actions(steps)
        self._detect_protocol_violations(steps)
        self._detect_loop_failures(steps)
        self._detect_deadlocks(steps)
        self._detect_irrational_concessions(steps, buyer_max, seller_min)

        risk_score = self._calculate_risk_score()
        summary = self._build_summary()

        return {
            "failures": self._failures,
            "risk_score": risk_score,
            "summary": summary,
        }

    def check_action_realtime(self, action: dict, turn: int, agent: str, history: list) -> Optional[dict]:
        """
        Lightweight real-time check for invalid_action and protocol_violation.
        Called by the Mediator during the negotiation loop.

        Returns a failure dict if a critical issue is found, else None.
        """
        action_type = action.get("type") or action.get("action")

        # Invalid action type
        if action_type and action_type not in VALID_ACTIONS:
            return self._make_failure(
                FailureType.INVALID_ACTION, FailureSeverity.HIGH,
                turn, agent,
                f"Unrecognized action '{action_type}'. Expected one of: {', '.join(VALID_ACTIONS)}"
            )

        # Accept/rejection with a price attached
        if action_type in ("acceptance", "rejection") and action.get("price") is not None:
            return self._make_failure(
                FailureType.INVALID_ACTION, FailureSeverity.MEDIUM,
                turn, agent,
                f"Action '{action_type}' should not include a price (got ${action['price']})"
            )

        # Protocol: first action must be proposal
        if len(history) == 0 and action_type not in ("proposal",):
            return self._make_failure(
                FailureType.PROTOCOL_VIOLATION, FailureSeverity.HIGH,
                turn, agent,
                f"First action must be 'proposal', got '{action_type}'"
            )

        # Protocol: acceptance when no price on table
        if action_type == "acceptance" and len(history) == 0:
            return self._make_failure(
                FailureType.PROTOCOL_VIOLATION, FailureSeverity.HIGH,
                turn, agent,
                "Cannot accept when no price has been proposed"
            )

        return None

    # ───────────────────────────────────────────────
    # Detector 1: Invalid Actions
    # ───────────────────────────────────────────────

    def _detect_invalid_actions(self, steps: List[dict]):
        for step in steps:
            action = step.get("action", {})
            action_type = action.get("type") or action.get("action")

            if action_type and action_type not in VALID_ACTIONS:
                self._failures.append(self._make_failure(
                    FailureType.INVALID_ACTION, FailureSeverity.HIGH,
                    step["turn"], step["agent"],
                    f"Unrecognized action '{action_type}'"
                ))

            # Acceptance/rejection should not carry a price
            if action_type in ("acceptance", "rejection") and action.get("price") is not None:
                self._failures.append(self._make_failure(
                    FailureType.INVALID_ACTION, FailureSeverity.MEDIUM,
                    step["turn"], step["agent"],
                    f"Action '{action_type}' should not include a price (got ${action['price']})"
                ))

    # ───────────────────────────────────────────────
    # Detector 2: Protocol Violations
    # ───────────────────────────────────────────────

    def _detect_protocol_violations(self, steps: List[dict]):
        if not steps:
            return

        # Rule: first action must be a proposal
        first_action = (steps[0].get("action", {}).get("type")
                        or steps[0].get("action", {}).get("action"))
        if first_action not in ("proposal",):
            self._failures.append(self._make_failure(
                FailureType.PROTOCOL_VIOLATION, FailureSeverity.HIGH,
                steps[0]["turn"], steps[0]["agent"],
                f"Negotiation must begin with 'proposal', got '{first_action}'"
            ))

        # Rule: acceptance when no price has been set yet
        prices_seen = False
        for step in steps:
            action = step.get("action", {})
            action_type = action.get("type") or action.get("action")
            if action.get("price") is not None:
                prices_seen = True
            if action_type == "acceptance" and not prices_seen:
                self._failures.append(self._make_failure(
                    FailureType.PROTOCOL_VIOLATION, FailureSeverity.HIGH,
                    step["turn"], step["agent"],
                    "Accepted with no price ever proposed"
                ))

    # ───────────────────────────────────────────────
    # Detector 3: Loop Failures
    # ───────────────────────────────────────────────

    def _detect_loop_failures(self, steps: List[dict]):
        # Track per-agent consecutive identical prices
        agent_prices: Dict[str, List[float]] = {}

        for step in steps:
            action = step.get("action", {})
            price = action.get("price")
            agent = step["agent"]

            if price is None:
                continue

            if agent not in agent_prices:
                agent_prices[agent] = []

            prev = agent_prices[agent]

            # Identical price repeated ≥2 consecutive times by same agent
            if len(prev) >= 1 and prev[-1] == price:
                self._failures.append(self._make_failure(
                    FailureType.LOOP_FAILURE, FailureSeverity.HIGH,
                    step["turn"], agent,
                    f"Repeated identical price ${price:.2f} (stuck in loop)"
                ))

            # Stagnant movement: price delta below $0.50
            if len(prev) >= 1 and abs(price - prev[-1]) < 0.50 and price != prev[-1]:
                self._failures.append(self._make_failure(
                    FailureType.LOOP_FAILURE, FailureSeverity.MEDIUM,
                    step["turn"], agent,
                    f"Near-stagnant price change: ${prev[-1]:.2f} → ${price:.2f} (Δ < $0.50)"
                ))

            prev.append(price)

    # ───────────────────────────────────────────────
    # Detector 4: Deadlocks
    # ───────────────────────────────────────────────

    def _detect_deadlocks(self, steps: List[dict]):
        # Extract buyer and seller price sequences
        buyer_prices = []
        seller_prices = []

        for step in steps:
            action = step.get("action", {})
            price = action.get("price")
            if price is None:
                continue
            if "buyer" in step["agent"].lower():
                buyer_prices.append((step["turn"], price))
            else:
                seller_prices.append((step["turn"], price))

        if len(buyer_prices) < 2 or len(seller_prices) < 2:
            return

        # Check if gap is increasing (diverging) over last 3 paired rounds
        gaps = []
        min_len = min(len(buyer_prices), len(seller_prices))
        for i in range(min_len):
            gap = abs(seller_prices[i][1] - buyer_prices[i][1])
            gaps.append(gap)

        if len(gaps) >= 3:
            recent = gaps[-3:]
            if all(recent[i] >= recent[i - 1] for i in range(1, len(recent))):
                self._failures.append(self._make_failure(
                    FailureType.DEADLOCK, FailureSeverity.HIGH,
                    steps[-1]["turn"], "Both agents",
                    f"Price gap widening over last 3 rounds: {' → '.join(f'${g:.2f}' for g in recent)}"
                ))

        # Check if gap hasn't narrowed in last 4 actions
        if len(gaps) >= 4:
            recent4 = gaps[-4:]
            initial_gap = recent4[0]
            if all(g >= initial_gap for g in recent4[1:]):
                self._failures.append(self._make_failure(
                    FailureType.DEADLOCK, FailureSeverity.MEDIUM,
                    steps[-1]["turn"], "Both agents",
                    f"Gap not narrowing in last 4 rounds (stuck at ~${recent4[-1]:.2f} apart)"
                ))

    # ───────────────────────────────────────────────
    # Detector 5: Irrational Concessions
    # ───────────────────────────────────────────────

    def _detect_irrational_concessions(self, steps: List[dict], buyer_max: float, seller_min: float):
        prev_prices: Dict[str, float] = {}

        for step in steps:
            action = step.get("action", {})
            price = action.get("price")
            agent = step["agent"]

            if price is None:
                continue

            is_buyer = "buyer" in agent.lower()

            # Buyer offering above their max budget
            if is_buyer and price > buyer_max:
                self._failures.append(self._make_failure(
                    FailureType.IRRATIONAL_CONCESSION, FailureSeverity.HIGH,
                    step["turn"], agent,
                    f"Buyer offered ${price:.2f} which exceeds max budget of ${buyer_max:.2f}"
                ))

            # Seller accepting below their min price
            if not is_buyer and price < seller_min:
                self._failures.append(self._make_failure(
                    FailureType.IRRATIONAL_CONCESSION, FailureSeverity.HIGH,
                    step["turn"], agent,
                    f"Seller offered ${price:.2f} which is below min acceptable ${seller_min:.2f}"
                ))

            # Large single-step concession (>30% jump)
            if agent in prev_prices:
                prev = prev_prices[agent]
                if prev > 0:
                    change_pct = abs(price - prev) / prev * 100
                    if change_pct > 30:
                        direction = "up" if price > prev else "down"
                        self._failures.append(self._make_failure(
                            FailureType.IRRATIONAL_CONCESSION, FailureSeverity.MEDIUM,
                            step["turn"], agent,
                            f"Extreme {change_pct:.0f}% price jump {direction}: ${prev:.2f} → ${price:.2f}"
                        ))

            prev_prices[agent] = price

    # ───────────────────────────────────────────────
    # Helpers
    # ───────────────────────────────────────────────

    def _make_failure(self, ftype: FailureType, severity: FailureSeverity,
                      turn: int, agent: str, description: str) -> dict:
        return {
            "type": ftype.value,
            "severity": severity.value,
            "turn": turn,
            "agent": agent,
            "description": description,
        }

    def _calculate_risk_score(self) -> float:
        """
        Weighted risk score from 0 (clean) to 100 (critical).
        HIGH=15pts, MEDIUM=8pts, LOW=3pts. Capped at 100.
        """
        weights = {"high": 15, "medium": 8, "low": 3}
        total = sum(weights.get(f["severity"], 0) for f in self._failures)
        return min(round(total, 1), 100.0)

    def _build_summary(self) -> str:
        if not self._failures:
            return "Clean run — no failures detected."

        counts = {}
        for f in self._failures:
            counts[f["type"]] = counts.get(f["type"], 0) + 1

        parts = [f"{count}× {ftype}" for ftype, count in counts.items()]
        high_count = sum(1 for f in self._failures if f["severity"] == "high")

        summary = f"Detected {len(self._failures)} issue(s): {', '.join(parts)}."
        if high_count > 0:
            summary += f" ({high_count} high severity)"

        return summary
