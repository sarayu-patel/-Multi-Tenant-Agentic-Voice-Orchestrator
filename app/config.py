from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "voice_agent"

    VAPI_API_KEY: str
    VAPI_PHONE_NUMBER_ID: str  # the outbound phone number from your Vapi dashboard

    OPENAI_API_KEY: str=""
    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
