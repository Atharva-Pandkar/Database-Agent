from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Gaming Analytics API"
    openai_api_key: str
    openai_model: str = "gpt-4-1106-preview"
    data_dir: str = str(Path(__file__).parent.parent.parent / "data")

@lru_cache()
def get_settings():
    return Settings()