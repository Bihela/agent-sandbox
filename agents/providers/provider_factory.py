from typing import Dict, List, Optional
from agents.providers.base_provider import BaseProvider

class ProviderFactory:
    _instances: Dict[str, BaseProvider] = {}

    @classmethod
    def get_provider(cls, name: str) -> BaseProvider:
        """Get or create a provider instance by name (ollama, openai, gemini, groq)."""
        name = name.lower()
        if name not in cls._instances:
            if name == "ollama":
                from agents.providers.ollama_provider import OllamaProvider
                cls._instances[name] = OllamaProvider()
            elif name == "openai":
                from agents.providers.openai_provider import OpenAIProvider
                cls._instances[name] = OpenAIProvider()
            elif name == "gemini":
                from agents.providers.gemini_provider import GeminiProvider
                cls._instances[name] = GeminiProvider()
            elif name == "groq":
                from agents.providers.groq_provider import GroqProvider
                cls._instances[name] = GroqProvider()
            else:
                from agents.providers.ollama_provider import OllamaProvider
                cls._instances[name] = OllamaProvider()
        
        return cls._instances[name]

    @classmethod
    def get_provider_for_model(cls, model_name: str) -> BaseProvider:
        """Infer provider from model name prefixed with provider name (e.g. 'openai:gpt-4')."""
        if ":" in model_name:
            provider_name, _ = model_name.split(":", 1)
            return cls.get_provider(provider_name)
        
        # Default for unprefixed models
        return cls.get_provider("ollama")
