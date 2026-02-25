from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Agent Sandbox"
    debug: bool = True

settings = Settings()
