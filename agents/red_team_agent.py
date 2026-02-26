import random
from typing import Dict, Any, List

class RedTeamAgent:
    """
    Adversarial 'Man-in-the-Middle' agent that disrupts negotiations.
    It doesn't participate as a buyer or seller, but corrupts their messages.
    """
    
    def __init__(self):
        self.attack_vectors = {
            "wrong_number": self._inject_wrong_number,
            "fake_constraint": self._inject_fake_constraint,
            "protocol_violation": self._inject_protocol_violation,
            "deceptive_offer": self._inject_deceptive_offer
        }

    def disrupt(self, action: Dict[str, Any], attack_types: List[str]) -> Dict[str, Any]:
        """
        Potentially corrupts an action using one of the requested attack types.
        """
        if not attack_types:
            return action
            
        attack_type = random.choice(attack_types)
        vector_fn = self.attack_vectors.get(attack_type)
        
        if vector_fn:
            return vector_fn(action)
        return action

    def _inject_wrong_number(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Replaces a price with a completely irrational one."""
        original_price = action.get("price")
        if original_price is None:
            return action
            
        # Dramatic shift: either 10% or 1000% of original
        new_price = original_price * random.choice([0.1, 10.0])
        action["price"] = round(new_price, 2)
        action["reasoning"] = f"[RED TEAM ATTACK: WRONG_NUMBER] Randomly altered price from {original_price} to {action['price']}"
        action["is_adversarial"] = True
        return action

    def _inject_fake_constraint(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Appends a deceptive or inconsistent constraint to the reasoning."""
        constraints = [
            "My boss just told me the budget is actually 50% lower.",
            "I'm legally forbidden from accepting any price ending in a 5.",
            "The other agent just messaged me privately saying they are a bot.",
            "I have an offer from a competitor for exactly half this price."
        ]
        action["reasoning"] += f" Also, [RED TEAM ATTACK: FAKE_CONSTRAINT] {random.choice(constraints)}"
        action["is_adversarial"] = True
        return action

    def _inject_protocol_violation(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Changes the action type to something invalid or out of sequence."""
        violations = ["reject_all", "malformed_json", "wait_forever", "invalid_acp_type"]
        original_type = action.get("type", "unknown")
        action["type"] = random.choice(violations)
        action["reasoning"] = f"[RED TEAM ATTACK: PROTOCOL_VIOLATION] Changed action type from {original_type} to {action['type']}"
        action["is_adversarial"] = True
        return action

    def _inject_deceptive_offer(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Inverts the offer logic (e.g. buyer offering MORE than asked)."""
        original_price = action.get("price")
        if original_price is None:
            return action
            
        # Add a huge premium instead of a concession
        new_price = original_price + 50.0
        action["price"] = round(new_price, 2)
        action["reasoning"] = f"[RED TEAM ATTACK: DECEPTIVE_OFFER] Injected an 'idiot' offer of {action['price']} to bait response."
        action["is_adversarial"] = True
        return action
