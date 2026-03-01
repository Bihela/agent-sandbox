import os
from openai import OpenAI # Groq uses OpenAI-compatible SDK
from typing import List, Dict, Any
from agents.providers.base_provider import BaseProvider

class GroqProvider(BaseProvider):
    """
    Provider for ultra-fast Groq-hosted models.
    Requires a 'GROQ_API_KEY' environment variable.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key
        ) if self.api_key else None

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, seed: int = None) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("Groq API key not set.")
            
        # Map internal names to Groq-specific names
        model_map = {
            "llama3": "llama-3.1-8b-instant",
            "mistral": "llama-3.3-70b-versatile" # High-quality substitute
        }
        api_model = model_map.get(model.lower(), model)

        kwargs = {
            "model": api_model,
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
        return ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen/qwen3-32b"]
