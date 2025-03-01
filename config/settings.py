import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "BU DocCloud Document Classification Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default=False)
    
    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # LLM settings
    OPENAI_API_KEY: str = Field(default="")
    LLM_MODEL: str = Field(default="gpt-4o")
    LLM_TEMPERATURE: float = Field(default=0.0)
    
    # Upload settings
    MAX_UPLOAD_SIZE: int = Field(default=50_000_000)  # 50MB
    SUPPORTED_FILE_TYPES: list = Field(
        default=[
            ".pdf", ".jpg", ".jpeg", ".png", ".tiff", 
            ".txt", ".doc", ".docx", ".csv"
        ]
    )
    
    # Storage settings
    TEMP_FILE_DIR: str = Field(default="/tmp/doc_classification")
    
    # BU DocCloud settings
    BU_DOCCLOUD_API_URL: str = Field(default="https://api.doccloud.BU.com/v1")
    BU_DOCCLOUD_API_KEY: str = Field(default="")
    BU_DOCCLOUD_CLIENT_ID: str = Field(default="")
    BU_DOCCLOUD_CLIENT_SECRET: str = Field(default="")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure temporary directory exists
os.makedirs(settings.TEMP_FILE_DIR, exist_ok=True)