import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    INDEXER_URL: str = os.getenv('INDEXER_URL', 'http://localhost:8001')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
