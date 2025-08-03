import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/rbac_db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Encryption key for data at rest
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # SSO Configuration
    OAUTH2_CLIENT_ID = os.environ.get('OAUTH2_CLIENT_ID')
    OAUTH2_CLIENT_SECRET = os.environ.get('OAUTH2_CLIENT_SECRET')
    SAML_ENTITY_ID = os.environ.get('SAML_ENTITY_ID')
    LDAP_SERVER = os.environ.get('LDAP_SERVER')
    LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN')

    # --- CONSOLIDATED AI/LLM SETTINGS ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", "gemini")
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    AUDIT_LOG_RETENTION_DAYS = 365
    
class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    
class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ENCRYPTION_KEY = 'CejMECLCNMP2gbV7ugfAxH6zwo_WKqeF5WHx2_FFRZI='
    # Set dummy keys for testing
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "test-gemini-key")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "test-groq-key")