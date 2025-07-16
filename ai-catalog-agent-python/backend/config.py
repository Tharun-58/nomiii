import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Base configuration"""
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change')
    
    # Application settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    WORKERS = int(os.getenv('WORKERS', 1))
    
    # Database configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    DB_NAME = os.getenv('DB_NAME', 'catalogdb')
    MONGO_CONNECT_TIMEOUT = 30000  # 30 seconds
    MONGO_SOCKET_TIMEOUT = 30000   # 30 seconds
    
    # Google Cloud Services
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
    
    # AI Services Configuration
    AI_MODEL_CACHE_DIR = os.getenv('AI_MODEL_CACHE_DIR', './model_cache')
    AI_MODEL_DEVICE = os.getenv('AI_MODEL_DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')
    
    # Rate Limiting
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100 per minute')
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def validate(cls):
        """Validate required configurations"""
        required = [
            'MONGO_URI',
            'GOOGLE_CREDENTIALS_PATH'
        ]
        
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required configuration: {missing}")

class DevelopmentConfig(Config):
    """Development specific configuration"""
    DEBUG = True
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing specific configuration"""
    TESTING = True
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/testdb')
    DB_NAME = 'testdb'

class ProductionConfig(Config):
    """Production specific configuration"""
    DEBUG = False
    MONGO_URI = os.getenv('MONGO_URI')  # Required in production
    LOG_LEVEL = 'WARNING'

def get_config(env=None):
    """Get appropriate configuration class based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    
    return configs.get(env.lower(), DevelopmentConfig)

# Initialize configuration
config = get_config()
try:
    config.validate()
except ValueError as e:
    import sys
    print(f"Configuration Error: {str(e)}", file=sys.stderr)
    sys.exit(1)