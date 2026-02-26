import os
from openai import OpenAI # Groq uses OpenAI-compatible SDK
from typing import List, Dict, Any
from agents.providers.base_provider import BaseProvider

class GroqProvider(BaseProvider):
    """Provider for ultra-fast Groq-hosted models."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key
        ) if self.api_key else None

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("Groq API key not set.")
            
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return {
            "content": content,
            "tokens_used": tokens,
            "raw_response": response
        }

    def get_available_models(self) -> List[str]:
        return ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
