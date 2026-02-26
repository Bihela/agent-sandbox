from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Agent Sandbox"
    debug: bool = True
    
    # Hugging Face Config (Replace with real key)
    HF_API_KEY: str = "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"
    MODEL_NAME: str = "Qwen/Qwen2.5-72B-Instruct"

settings = Settings()
