import os
import google.generativeai as genai
from typing import List, Dict, Any
from agents.providers.base_provider import BaseProvider

class GeminiProvider(BaseProvider):
    """
    Provider for Google Gemini models.
    Requires a 'GEMINI_API_KEY' environment variable.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, seed: int = None) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Gemini API key not set.")
            
        # Convert messages to Gemini format
        # Note: Gemini usually expects a specific prompt or chat history
        # For simplicity, we'll combine history or use the latest
        gen_model = genai.GenerativeModel(model)
        
        # Simple implementation: pass the last message as prompt, others as context if needed
        # Robust implementation would use gen_model.start_chat(history=...)
        prompt = messages[-1]["content"]
        
        response = gen_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        
        return {
            "content": response.text,
            "tokens_used": 0, # Gemini API token count is separate
            "raw_response": response
        }

    def get_available_models(self) -> List[str]:
        return ["gemini-1.5-pro", "gemini-1.5-flash"]
