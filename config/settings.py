"""Application settings and configuration."""
import os
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

def clean_env_value(value):
    """Clean environment variable value by removing comments and whitespace."""
    if value and '#' in value:
        value = value.split('#')[0]
    return value.strip() if value else value

def get_env_var(name, default=None):
    """Get environment variable with cleaning."""
    return clean_env_value(os.getenv(name, default))

# Flask Configuration
DEBUG = get_env_var('FLASK_DEBUG', 'False').lower() == 'true'
SECRET_KEY = get_env_var('FLASK_SECRET_KEY', 'your-secret-key-here')

# OANDA Configuration
OANDA_API_KEY = get_env_var('OANDA_API_KEY')
OANDA_ACCOUNT_ID = get_env_var('OANDA_ACCOUNT_ID')
OANDA_ENVIRONMENT = get_env_var('OANDA_ENVIRONMENT', 'practice')

# Requesty Configuration
ROUTER_API_KEY = get_env_var('ROUTER_API_KEY')
REQUESTY_BASE_URL = get_env_var('ROUTER_BASE_URL', 'https://router.requesty.ai/v1')

# Trading Configuration
DEFAULT_TIMEFRAME = 'M5'  # 5-minute candles
DEFAULT_COUNT = 100  # Number of candles to fetch

# AI Model Configuration
MODELS = {
    'gpt4': {
        'id': 'openai/gpt-4o',  # Changed from gpt-4-vision-preview to gpt-4o
        'max_tokens': int(get_env_var('ROUTER_MAX_TOKENS', '2000')),
        'temperature': float(get_env_var('ROUTER_TEMPERATURE', '0.7'))
    },
    'claude': {
        'id': 'anthropic/claude-3-7-sonnet-latest',  # Updated based on user input
        'max_tokens': 4000,
        'temperature': 0.5
    },
    'perplexity': {
        'id': 'perplexity/sonar',  # Updated based on user input
        'max_tokens': 1000,
        'temperature': 0.3
    }
}

# Default model settings
DEFAULT_MODEL = MODELS['gpt4']['id']
MAX_TOKENS = MODELS['gpt4']['max_tokens']
TEMPERATURE = MODELS['gpt4']['temperature']

# OpenAI API Configuration
MODEL_NAME_OPENAI = get_env_var('MODEL_NAME_OPENAI', 'gpt-4-vision-preview')
MAX_RETRIES = int(get_env_var('MAX_RETRIES', '3'))
RETRY_DELAY = int(get_env_var('RETRY_DELAY', '2'))  # seconds

# Claude API Configuration
CLAUDE_MODEL_NAME = get_env_var('CLAUDE_MODEL_NAME', 'claude-3-sonnet-20240229')
ANTHROPIC_MODEL = get_env_var('ANTHROPIC_MODEL', 'claude-3-7-sonnet-latest')
ANTHROPIC_API_TEMPERATURE = float(get_env_var('ANTHROPIC_TEMPERATURE', '0.5'))

def validate_requesty_settings():
    """Validate Requesty-specific settings."""
    if not ROUTER_API_KEY:
        raise RuntimeError("Missing required Requesty API key (ROUTER_API_KEY)")

def validate_oanda_settings():
    """Validate OANDA-specific settings."""
    if not all([OANDA_API_KEY, OANDA_ACCOUNT_ID]):
        raise RuntimeError("Missing required OANDA credentials (OANDA_API_KEY and/or OANDA_ACCOUNT_ID)")
    
    valid_environments = ['practice', 'live']
    if OANDA_ENVIRONMENT.lower() not in valid_environments:
        raise ValueError(f"OANDA_ENVIRONMENT must be either 'practice' or 'live'. Got: '{OANDA_ENVIRONMENT}'")

# Only validate when not testing
if not os.getenv('TESTING'):
    validate_requesty_settings()
    validate_oanda_settings()