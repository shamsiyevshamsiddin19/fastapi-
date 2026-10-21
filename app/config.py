from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = True
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    environment: str = "development"

    # Email (ixtiyoriy)
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()