from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:@host.docker.internal:5432/bigdata"
    debug: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
