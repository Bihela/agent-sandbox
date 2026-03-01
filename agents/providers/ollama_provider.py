import ollama
from typing import List, Dict, Any
from agents.providers.base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """
    Provider for local Ollama instances.
    Requires the 'ollama' Python library and a running Ollama daemon.
    """
    
    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, seed: int = None) -> Dict[str, Any]:
        """
        Executes a chat completion request via local Ollama.
        """
        options = {"temperature": temperature}
        if seed is not None:
            options["seed"] = seed

        response = ollama.chat(
            model=model,
            messages=messages,
            options=options
        )
        
        content = response.get("message", {}).get("content", "")
        tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
        
        return {
            "content": content,
            "tokens_used": tokens,
            "raw_response": response
        }

    def get_available_models(self) -> List[str]:
        try:
            models_info = ollama.list()
            return [m['name'] for m in models_info.get('models', [])]
        except:
            return ["mistral", "llama3"] # Fallback defaults
