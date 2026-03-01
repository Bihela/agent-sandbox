import os
from openai import OpenAI
from typing import List, Dict, Any
from agents.providers.base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    """
    Provider for OpenAI GPT models.
    Requires an 'OPENAI_API_KEY' environment variable.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, seed: int = None) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("OpenAI API key not set.")
            
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if seed is not None:
            kwargs["seed"] = seed

        response = self.client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return {
            "content": content,
            "tokens_used": tokens,
            "raw_response": response
        }

    def get_available_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
