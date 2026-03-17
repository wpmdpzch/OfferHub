from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "offerhub"
    postgres_user: str = "offerhub"
    # 无默认值：必须通过环境变量注入，防止硬编码凭证（CWE-798）
    postgres_password: str

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # 无默认值：必须通过环境变量注入
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    app_env: str = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"

    github_token: str = ""

    # 投稿审核开关：False = 直接发布，True = 进入 pending 等待审核
    review_enabled: bool = False

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
