from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Adfire API'
    auth_secret: str
    database_url: str

    model_config = SettingsConfigDict(env_file='.env.local')


@lru_cache
def get_settings():
    return Settings()
