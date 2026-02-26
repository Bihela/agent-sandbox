from typing import List, Optional
from world.messages import NegotiationMessage, MessageType

class Mediator:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.turn_count = 0
        self.history: List[NegotiationMessage] = []

    def check_turn(self, current_action_dict: dict) -> dict:
        """
        Validates an agent's action to ensure the negotiation rules are being followed.
        Returns {"stop": True/False, "reason": "...", "status": "..."}
        """
        self.turn_count += 1
        
        # 1. Validate the structure of the message
        try:
            msg = NegotiationMessage(**current_action_dict)
            self.history.append(msg)
        except Exception as e:
            return {"stop": True, "reason": f"Invalid message format: {e}", "status": "error"}

        # 2. Check for agreement or rejection
        if msg.type == MessageType.ACCEPT:
            return {"stop": True, "reason": "Agreement reached", "status": "success"}
        elif msg.type == MessageType.REJECT:
            return {"stop": True, "reason": "Offer rejected", "status": "failure"}

        # 3. Check for timeout / max turns
        if self.turn_count >= self.max_turns:
            return {"stop": True, "reason": f"Maximum of {self.max_turns} turns exceeded", "status": "timeout"}

        # 4. Check for loop / same offer repeated
        # If the same agent offers the identical price they offered in their previous turn
        if len(self.history) >= 3:
            # history[-1] is current agent's turn, history[-3] is their *previous* turn.
            curr_msg = self.history[-1]
            prev_self_msg = self.history[-3]
            if curr_msg.type == prev_self_msg.type and curr_msg.price == prev_self_msg.price:
                return {"stop": True, "reason": "Repetitive behavior detected (agents stuck)", "status": "error"}

        return {"stop": False, "reason": "", "status": "ongoing"}
