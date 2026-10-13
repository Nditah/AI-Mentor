"""Runtime configuration. Production refuses the shortcuts that local development uses."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_OPTIONAL = (
    "clerk_jwks_url",
    "clerk_issuer",
    "clerk_audience",
    "clerk_authorized_parties",
    "clerk_webhook_secret",
    "clerk_secret_key",
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
    "qdrant_api_key",
    "redis_url",
    "studio_origins",
    "learner_origins",
    "institution_origins",
    "app_origins",
)


def _split(value: str | None) -> list[str]:
    return [item.strip().rstrip("/") for item in (value or "").split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_env: str = Field(default="development", alias="APP_ENV")
    dev_auth: bool | None = Field(default=None, alias="DEV_AUTH")
    database_url: str = Field(
        default="postgresql+psycopg://mentor:mentor@localhost:5432/mentor",
        alias="DATABASE_URL",
    )
    qdrant_url: str = Field(default="memory", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    cors_origins: str = Field(
        default=(
            "http://localhost:3000,http://localhost:3001,"
            "http://localhost:3002,http://localhost:3003,http://localhost:3004,"
            "http://localhost:3005"
        ),
        alias="CORS_ORIGINS",
    )
    studio_origins: str | None = Field(default=None, alias="STUDIO_ORIGINS")
    learner_origins: str | None = Field(default=None, alias="LEARNER_ORIGINS")
    institution_origins: str | None = Field(default=None, alias="INSTITUTION_ORIGINS")
    app_origins: str | None = Field(default=None, alias="APP_ORIGINS")
    clerk_jwks_url: str | None = Field(default=None, alias="CLERK_JWKS_URL")
    clerk_issuer: str | None = Field(default=None, alias="CLERK_ISSUER")
    clerk_audience: str | None = Field(default=None, alias="CLERK_AUDIENCE")
    clerk_authorized_parties: str | None = Field(default=None, alias="CLERK_AUTHORIZED_PARTIES")
    clerk_webhook_secret: str | None = Field(default=None, alias="CLERK_WEBHOOK_SECRET")
    clerk_secret_key: str | None = Field(default=None, alias="CLERK_SECRET_KEY")
    jwt_leeway_seconds: int = Field(default=5, ge=0, le=60, alias="JWT_LEEWAY_SECONDS")
    require_staff_mfa: bool | None = Field(default=None, alias="REQUIRE_STAFF_MFA")
    lab_enabled: bool | None = Field(default=None, alias="LAB_ENABLED")
    content_self_approval: bool = Field(default=False, alias="CONTENT_SELF_APPROVAL")
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
    llm_timeout_seconds: float = Field(default=20.0, gt=0, le=120, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=1, ge=0, le=3, alias="LLM_MAX_RETRIES")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    otel_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    ai_rate_limit_per_minute: int = Field(default=20, alias="AI_RATE_LIMIT_PER_MINUTE")
    upload_rate_limit_per_hour: int = Field(default=10, alias="UPLOAD_RATE_LIMIT_PER_HOUR")
    anonymous_rate_limit_per_minute: int = Field(
        default=120, alias="ANONYMOUS_RATE_LIMIT_PER_MINUTE"
    )

    @model_validator(mode="before")
    @classmethod
    def blank_optional(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        for key in _OPTIONAL:
            for name in (key, key.upper()):
                if data.get(name) == "":
                    data[name] = None
        return data

    @property
    def production(self) -> bool:
        return self.app_env == "production"

    @property
    def resolved_dev_auth(self) -> bool:
        if self.dev_auth is not None:
            return self.dev_auth
        return self.app_env in {"development", "test"}

    @property
    def resolved_staff_mfa(self) -> bool:
        if self.require_staff_mfa is not None:
            return self.require_staff_mfa
        return self.production

    @property
    def resolved_lab_enabled(self) -> bool:
        if self.lab_enabled is not None:
            return self.lab_enabled
        return not self.production

    @model_validator(mode="after")
    def production_guard(self) -> Settings:
        if not self.production:
            return self
        if self.resolved_dev_auth:
            raise ValueError("DEV_AUTH must be disabled in production")
        if not self.clerk_jwks_url or not self.clerk_issuer:
            raise ValueError("CLERK_JWKS_URL and CLERK_ISSUER are required in production")
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY is required in production for account deletion")
        if not self.database_url.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be PostgreSQL in production")
        if not self.qdrant_url.startswith("https://"):
            raise ValueError("QDRANT_URL must be an https:// server in production")
        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY is required in production")
        if not self.redis_url:
            raise ValueError("REDIS_URL is required in production for shared rate limits")
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required in production: hash embeddings are for local use only"
            )
        if self.resolved_lab_enabled:
            raise ValueError(
                "LAB_ENABLED must stay off in production until learner code runs in an "
                "isolated, secret-free, network-less runner"
            )
        if not self.resolved_staff_mfa:
            raise ValueError("REQUIRE_STAFF_MFA cannot be disabled in production")
        for origin in [*self.origins, *self.billing_return_origins, *self.authorized_parties]:
            if origin == "*" or urlsplit(origin).scheme != "https":
                raise ValueError(f"Origin {origin!r} must be an explicit https:// origin")
        return self

    @property
    def origins(self) -> list[str]:
        return _split(self.cors_origins)

    @property
    def app_origin_map(self) -> dict[str, str]:
        """Code name to origin: learner, admin, instructor, institution, studio."""

        codes = ("learner", "admin", "instructor", "institution", "studio")
        if self.app_origins:
            mapping: dict[str, str] = {}
            for item in _split(self.app_origins):
                if "=" not in item:
                    continue
                code, url = item.split("=", 1)
                mapping[code.strip()] = url.strip().rstrip("/")
            if mapping:
                return mapping
        return {code: origin for code, origin in zip(codes, self.origins, strict=False)}

    @property
    def billing_return_origins(self) -> list[str]:
        """Checkout may only return to the Learner App or Institution App."""

        learner = _split(self.learner_origins) or _split(self.studio_origins)
        institution = _split(self.institution_origins)
        configured = [*learner, *institution]
        if configured:
            return configured
        mapping = self.app_origin_map
        fallback = [mapping[code] for code in ("learner", "institution") if code in mapping]
        return fallback or self.origins[:1]

    @property
    def authorized_parties(self) -> list[str]:
        return _split(self.clerk_authorized_parties) or self.origins

    @property
    def external_models(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key or self.gemini_api_key)

    @property
    def qdrant_enabled(self) -> bool:
        return self.qdrant_url.startswith(("http://", "https://"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
