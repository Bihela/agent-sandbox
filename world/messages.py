from enum import Enum
from pydantic import BaseModel
from typing import Optional, Literal

class MessageType(str, Enum):
    PROPOSAL = "proposal"
    COUNTER_PROPOSAL = "counter_proposal"
    ACCEPTANCE = "acceptance"
    REJECTION = "rejection"
    INFORMATION = "information"
    CHALLENGE = "challenge"

    # Legacy mappings (for backward compatibility if needed temporarily)
    OFFER = "proposal"
    COUNTER_OFFER = "counter_proposal"
    ACCEPT = "acceptance"
    REJECT = "rejection"

class NegotiationMessage(BaseModel):
    """
    Standard ACP-like message format for agent negotiation.
    """
    sender: str
    receiver: str
    type: MessageType
    price: Optional[float] = None
    reasoning: Optional[str] = None
    metadata: dict = {}
