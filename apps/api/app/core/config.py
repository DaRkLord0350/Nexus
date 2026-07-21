from pathlib import Path
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

VALID_ENVIRONMENTS = {"development", "staging", "production"}


class Settings(BaseSettings):
    """Single configuration source for the whole application.

    Every setting is environment-driven (see .env.example / .env.development /
    .env.production). Nothing here should ever hardcode a real secret — those
    come from the process environment or, in staging/production, from AWS
    Secrets Manager (see app/core/secrets.py), which overrides plain
    environment variables when USE_AWS_SECRETS_MANAGER is enabled.
    """

    project_name: str = "CommerceOS API"
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("text", env="LOG_FORMAT")  # text | json

    # --- Datastores ---
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # --- Auth ---
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret: str = Field("", env="JWT_SECRET")  # falls back to secret_key when unset
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(30, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # --- URLs / CORS ---
    app_url: AnyHttpUrl = Field("http://localhost:3000", env="APP_URL")
    frontend_url: AnyHttpUrl = Field("http://localhost:3000", env="FRONTEND_URL")
    api_url: AnyHttpUrl = Field("http://localhost:8000", env="API_URL")
    cors_origins: str = Field("", env="CORS_ORIGINS")  # comma-separated, in addition to frontend_url

    # --- Email ---
    mail_from: str = Field("CommerceOS <no-reply@commerceos.local>", env="MAIL_FROM")
    email_provider: str = Field("smtp", env="EMAIL_PROVIDER")  # smtp | ses — smtp is a development-only fallback
    ses_region: str = Field("", env="SES_REGION")  # falls back to aws_region when unset
    ses_from_email: str = Field("", env="SES_FROM_EMAIL")  # falls back to mail_from when unset
    smtp_host: str = Field("", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str = Field("", env="SMTP_USER")
    smtp_password: str = Field("", env="SMTP_PASSWORD")

    # --- File storage (Amazon S3 in staging/production, local disk in development only) ---
    storage_provider: str = Field("local", env="STORAGE_PROVIDER")  # local | s3
    local_upload_path: Path = Field(default_factory=lambda: BASE_DIR / "storage")
    s3_bucket: str = Field("commerceos", env="S3_BUCKET")
    s3_endpoint: str = Field("", env="S3_ENDPOINT")  # optional: only for S3-compatible endpoints in dev/test
    s3_region: str = Field("us-east-1", env="S3_REGION")
    file_upload_max_bytes: int = Field(20 * 1024 * 1024, env="FILE_UPLOAD_MAX_BYTES")
    allowed_file_mime_types: list[str] = Field(default_factory=lambda: ["image/jpeg", "image/png", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"])
    virus_scan_command: str = Field("", env="VIRUS_SCAN_COMMAND")
    image_optimization_enabled: bool = Field(True, env="IMAGE_OPTIMIZATION_ENABLED")
    image_optimization_quality: int = Field(85, env="IMAGE_OPTIMIZATION_QUALITY")

    # --- AWS ---
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    # Leave these empty on EC2 — boto3 falls back to the instance's IAM role
    # automatically. Only set them for local development against a real AWS
    # account, or when running under temporary STS credentials.
    aws_access_key_id: str = Field("", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: str = Field("", env="AWS_SESSION_TOKEN")
    use_aws_secrets_manager: bool = Field(False, env="USE_AWS_SECRETS_MANAGER")
    aws_secrets_manager_prefix: str = Field("", env="AWS_SECRETS_MANAGER_PREFIX")

    # --- Security ---
    force_https: bool = Field(False, env="FORCE_HTTPS")

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_staging(self) -> bool:
        return self.environment.lower() == "staging"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production_like(self) -> bool:
        """True in staging and production — used for security defaults (HSTS,
        JSON logs, secure cookies) that should match production posture in
        staging too, without being tied to the separate DEBUG flag."""
        return self.environment.lower() in {"staging", "production"}

    @property
    def effective_jwt_secret(self) -> str:
        return self.jwt_secret or self.secret_key

    @property
    def effective_ses_region(self) -> str:
        return self.ses_region or self.aws_region

    @property
    def effective_ses_from_email(self) -> str:
        return self.ses_from_email or self.mail_from

    @property
    def cors_allowed_origins(self) -> list[str]:
        origins = {str(self.frontend_url).rstrip("/"), str(self.app_url).rstrip("/")}
        if self.cors_origins:
            origins.update(origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip())
        return sorted(origins)

    @property
    def aws_credentials_kwargs(self) -> dict:
        """boto3 client kwargs for explicit credentials. Empty values are
        omitted so boto3's default credential chain (IAM instance role,
        environment, shared config, etc.) takes over — this is deliberate:
        never force explicit (possibly blank) credentials over the instance
        role in production."""
        kwargs: dict = {}
        if self.aws_access_key_id:
            kwargs["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            kwargs["aws_secret_access_key"] = self.aws_secret_access_key
        if self.aws_session_token:
            kwargs["aws_session_token"] = self.aws_session_token
        return kwargs


def _bootstrap_settings() -> Settings:
    import os

    environment = os.environ.get("ENVIRONMENT", "development").lower()
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(f"ENVIRONMENT must be one of {sorted(VALID_ENVIRONMENTS)}, got {environment!r}")

    if os.environ.get("USE_AWS_SECRETS_MANAGER", "").lower() in {"1", "true", "yes"}:
        from app.core.secrets import load_secrets_into_environment

        load_secrets_into_environment(
            prefix=os.environ.get("AWS_SECRETS_MANAGER_PREFIX", ""),
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )

    return Settings()


settings = _bootstrap_settings()
