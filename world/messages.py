from enum import Enum
from pydantic import BaseModel
from typing import Optional

class MessageType(str, Enum):
    OFFER = "offer"
    COUNTER_OFFER = "counter_offer"
    ACCEPT = "accept"
    REJECT = "reject"

class NegotiationMessage(BaseModel):
    """
    Standard message format for agent negotiation.
    Example: {"type": "offer", "price": 120.0}
    """
    type: MessageType
    price: Optional[float] = None
