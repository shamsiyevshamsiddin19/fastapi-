from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = True
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    environment: str = "development"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()