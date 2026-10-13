"""Runtime configuration. Production refuses the shortcuts that local development uses."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_OPTIONAL = (
    "clerk_jwks_url",
    "clerk_issuer",
    "clerk_webhook_secret",
    "stripe_secret_key",
    "stripe_webhook_secret",
    "stripe_price_pro",
    "stripe_price_research",
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "langfuse_public_key",
    "langfuse_secret_key",
    "otel_endpoint",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_env: str = Field(default="development", alias="APP_ENV")
    dev_auth: bool | None = Field(default=None, alias="DEV_AUTH")
    database_url: str = Field(
        default="postgresql+psycopg://mentor:mentor@localhost:5432/mentor",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="memory", alias="QDRANT_URL")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001", alias="CORS_ORIGINS"
    )
    clerk_jwks_url: str | None = Field(default=None, alias="CLERK_JWKS_URL")
    clerk_issuer: str | None = Field(default=None, alias="CLERK_ISSUER")
    clerk_webhook_secret: str | None = Field(default=None, alias="CLERK_WEBHOOK_SECRET")
    stripe_secret_key: str | None = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_pro: str | None = Field(default=None, alias="STRIPE_PRICE_PRO")
    stripe_price_research: str | None = Field(default=None, alias="STRIPE_PRICE_RESEARCH")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-haiku-latest", alias="ANTHROPIC_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    otel_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    ai_rate_limit_per_minute: int = Field(default=20, alias="AI_RATE_LIMIT_PER_MINUTE")

    @model_validator(mode="before")
    @classmethod
    def blank_optional(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        for key in _OPTIONAL:
            if data.get(key) == "":
                data[key] = None
        return data

    @property
    def resolved_dev_auth(self) -> bool:
        if self.dev_auth is not None:
            return self.dev_auth
        return self.app_env in {"development", "test"}

    @model_validator(mode="after")
    def production_guard(self) -> Settings:
        if self.app_env != "production":
            return self
        if self.resolved_dev_auth:
            raise ValueError("DEV_AUTH must be disabled in production")
        if not self.clerk_jwks_url or not self.clerk_issuer:
            raise ValueError("CLERK_JWKS_URL and CLERK_ISSUER are required in production")
        if not self.database_url.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be PostgreSQL in production")
        if not self.qdrant_url.startswith("http"):
            raise ValueError("QDRANT_URL must be an HTTP server in production")
        return self

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def external_models(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key or self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
