"""Helper functions for accessing API keys and services."""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

def get_api_key(service_name):
    """
    Securely retrieve API keys for various services.
    
    Args:
        service_name (str): Name of the service ('openai', 'anthropic', 'oanda', 'perplexity')
        
    Returns:
        str: API key for the specified service or None if not found
    """
    key_mapping = {
        'oanda': 'OANDA_API_KEY',
        # All LLMs (openai, anthropic, perplexity) must use the router key (ROUTER_API_KEY) via the router endpoint.
    }
    
    env_var_name = key_mapping.get(service_name.lower())
    if not env_var_name:
        logger.error(f"Unknown service name: {service_name}")
        return None
    
    api_key = os.environ.get(env_var_name)
    if not api_key:
        logger.warning(f"API key for {service_name} not found in environment variables")
        return None
        
    return api_key

def get_oanda_account_id():
    """
    Retrieve the OANDA account ID from environment variables.
    
    Returns:
        str: OANDA account ID or None if not found
    """
    account_id = os.environ.get('OANDA_ACCOUNT_ID')
    if not account_id:
        logger.warning("OANDA account ID not found in environment variables")
    return account_id

def check_api_keys_availability():
    """
    Check which API keys are available and return their status.
    
    Returns:
        dict: Status of each API key (True if available, False if not)
    """
    return {
        'openai': bool(get_api_key('openai')),
        'anthropic': bool(get_api_key('anthropic')),
        'oanda': bool(get_api_key('oanda')),
        'oanda_account': bool(get_oanda_account_id()),
        'perplexity': bool(get_api_key('perplexity')),
    }