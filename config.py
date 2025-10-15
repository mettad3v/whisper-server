"""
Centralized configuration using python-dotenv.
Load .env file once and define all configuration variables here.
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file once, globally
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/3')

# Celery Worker Configuration
CELERY_CONCURRENCY = int(os.getenv('CELERY_CONCURRENCY', '4'))

# API Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Display configuration on import (for development)
if os.getenv('ENVIRONMENT', 'development') == 'development':
    print("🔧 Configuration loaded:")
    print(f"  Redis URL: {REDIS_URL}")
    print(f"  Celery Concurrency: {CELERY_CONCURRENCY}")
    print(f"  API Host: {HOST}:{PORT}")
    print(f"  Log Level: {LOG_LEVEL}")
    print()