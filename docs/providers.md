# Model Provider Plugin Guide

Agent Sandbox supports a pluggable provider architecture, allowing you to use local models or cloud-based LLMs seamlessly.

## Supported Providers

| Provider | Description | Required Environment Variable | Sample Model |
| :--- | :--- | :--- | :--- |
| **Ollama** | Local offline inference | None (Requires instance) | `mistral`, `llama3` |
| **OpenAI** | Standard cloud models | `OPENAI_API_KEY` | `gpt-4o`, `gpt-3.5-turbo` |
| **Gemini** | Google's generative models | `GEMINI_API_KEY` | `gemini-1.5-pro` |
| **Groq** | Ultra-fast hosted models | `GROQ_API_KEY` | `llama3-70b-8192` |

## Configuration

### Local (Ollama)
Ollama is the default provider. To use it, simply ensure the Ollama daemon is running and you have pulled your desired model:
```bash
ollama pull mistral
```

### Cloud Providers
Add your API keys to a `.env` file in the project root:
```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

## Adding a New Provider

To add a new provider (e.g., Anthropic):

1. **Create the Provider Class**: Create a new file in `agents/providers/anthropic_provider.py`.
   ```python
   from agents.providers.base_provider import BaseProvider
   
- **Anthropic (New Example)**:
```python
class AnthropicProvider(BaseProvider):
    def chat(self, model, messages, temperature, seed=None):
        # Implement your API call here, passing seed for reproducibility if supported
        return {"content": "...", "tokens_used": 0}
```
           
       def get_available_models(self):
           return ["claude-3-opus", "claude-3-sonnet"]
   ```

2. **Register in Factory**: Update `agents/providers/provider_factory.py`.
   ```python
   elif name == "anthropic":
       from agents.providers.anthropic_provider import AnthropicProvider
       cls._instances[name] = AnthropicProvider()
   ```

3. **Use in Simulation**: Set the model as `anthropic:claude-3-opus` in your simulation configuration.
