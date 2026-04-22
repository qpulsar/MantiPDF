import keyring
import logging

class SecurityManager:
    """Handles secure storage of API keys using system keyring."""
    
    SERVICE_NAME = "MantiPDF_AI_Service"
    
    @staticmethod
    def set_api_key(provider, api_key):
        """
        Stores an API key for a specific provider.
        
        Args:
            provider (str): Provider name (e.g., 'openai', 'anthropic', 'gemini')
            api_key (str): The API key to store
        """
        try:
            keyring.set_password(SecurityManager.SERVICE_NAME, provider, api_key)
            return True
        except Exception as e:
            logging.error(f"Error storing API key for {provider}: {e}")
            return False

    @staticmethod
    def get_api_key(provider):
        """
        Retrieves an API key for a specific provider.
        
        Args:
            provider (str): Provider name
            
        Returns:
            str: The API key or None if not found
        """
        try:
            return keyring.get_password(SecurityManager.SERVICE_NAME, provider)
        except Exception as e:
            logging.error(f"Error retrieving API key for {provider}: {e}")
            return None

    @staticmethod
    def delete_api_key(provider):
        """
        Removes an API key for a specific provider.
        
        Args:
            provider (str): Provider name
        """
        try:
            keyring.delete_password(SecurityManager.SERVICE_NAME, provider)
            return True
        except Exception as e:
            logging.error(f"Error deleting API key for {provider}: {e}")
            return False

    @staticmethod
    def has_api_key(provider):
        """Checks if an API key exists for a specific provider."""
        return SecurityManager.get_api_key(provider) is not None
