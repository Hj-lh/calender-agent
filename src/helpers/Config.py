from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_MODEL_NAME: str
    OLLAMA_URL: str
    TEMPERATURE: float

    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: str

    GOOGLE_CALENDAR_CREDENTIALS_PATH: str
    GOOGLE_CALENDAR_TOKEN_PATH: str
    TIMEZONE: str = "UTC"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()

