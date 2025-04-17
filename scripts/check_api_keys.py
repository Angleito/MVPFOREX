#!/usr/bin/env python
"""Test script to verify API key configuration."""
import sys
import logging
from app.utils.api_helpers import check_api_keys_availability

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check API key availability and print results."""
    logger.info("Checking API key configuration...")
    
    # Get status of all API keys
    api_status = check_api_keys_availability()
    
    # Print status
    print("\nAPI Key Configuration Status:")
    print("-----------------------------")
    
    all_available = True
    for service, available in api_status.items():
        status = "✓ Available" if available else "✗ Missing or Empty"
        print(f"{service.upper():15}: {status}")
        if not available and service != 'perplexity':  # Perplexity is optional
            all_available = False
    
    print("\nConfiguration status: ", end="")
    if all_available:
        print("✓ All required API keys are configured")
        return 0
    else:
        print("✗ Some required API keys are missing")
        print("\nPlease set the missing API keys in your .env file")
        return 1

if __name__ == "__main__":
    sys.exit(main())