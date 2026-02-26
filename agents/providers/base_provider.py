from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        """
        Send a chat request to the provider.
        Returns a dict with:
        - content: str
        - tokens_used: int
        - raw_response: Any
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Return a list of models supported by this provider."""
        pass
