"""
Simple configuration for testing
"""

class Settings:
    SECRET_KEY = "test-secret-key-for-development-only"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()