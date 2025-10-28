from itertools import cycle
from typing import List, Optional, Dict, Any
from config.config import GEMINI_API_KEYS

class GeminiConnectionManager:
    """
    Manages the connection configuration for the Gemini API, including
    API key rotation.
    """
    def __init__(self, api_keys: Optional[List[str]] = None):
        if not api_keys:
            api_keys = GEMINI_API_KEYS
        if not api_keys:
            raise ValueError("GEMINI_API_KEYS are not configured in .env or config.py")

        self._api_key_cycler = cycle(api_keys)
        self.active_key = None

    def _get_next_key(self) -> str:
        """Rotates to the next available API key."""
        self.active_key = next(self._api_key_cycler)
        return self.active_key

    def get_llm_config(self, model_name: str = "gemini-pro", temperature: float = 0.1) -> Dict[str, Any]:
        """
        Provides a configuration dictionary for the Gemini LLM.

        Args:
            model_name (str): The name of the Gemini model to use.
            temperature (float): The temperature for the model's responses.

        Returns:
            A dictionary with the LLM configuration for CrewAI.
        """
        api_key = self._get_next_key()
        print(f"--- Using Gemini model: {model_name} with a rotated API key. ---")

        return {
            "model": f"google/{model_name}",
            "api_key": api_key,
            "temperature": temperature,
        }

# Singleton instance to be used across the application
gemini_manager = GeminiConnectionManager()
