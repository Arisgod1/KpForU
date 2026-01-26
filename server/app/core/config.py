from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "KpForU API"
    debug: bool = True
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/kpforu",
        description="SQLAlchemy database URL",
    )
    jwt_secret_key: str = Field(default="dev-secret", description="JWT secret key")
    dashscope_api_key: str | None = Field(
        default="sk-107de5e29e0c4436b82afdf0d82c315c",  # 非生产环境默认值，生产请用环境变量覆盖
        description="DashScope / Qwen API key",
    )
    jwt_algorithm: str = "HS256"
    jwt_expires_seconds: int = 7 * 24 * 3600
    leitner_intervals: dict[int, int] = Field(
        default_factory=lambda: {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}
    )
    timezone_header: str = "X-Client-Timezone"
    upload_dir: str = "storage/voice"
    upload_max_mb: int = 20
    qwen_model: str = Field(default="qwen3-omni-flash", description="Qwen omni model name")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="OpenAI-compatible endpoint for Qwen",
    )
    qwen_audio_voice: str = Field(default="Cherry", description="Voice used when requesting audio output")
    qwen_audio_format: str = Field(default="wav", description="Audio format for Qwen responses")
    ai_summary_audio_enabled: bool = Field(default=False, description="Return audio for AI summaries")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
