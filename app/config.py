from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='POSTGRES_', env_file='.env', extra='ignore'
    )

    host: str = 'db'
    port: int = 5432
    user: str = 'postgres'
    password: str = 'postgres'
    db: str = 'mydb'

    @property
    def database_url(self) -> str:
        return f'postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}'


settings = Settings()
