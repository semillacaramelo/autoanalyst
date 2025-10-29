import os
from itertools import cycle
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import GEMINI_API_KEYS

class GeminiConnectionManager:
    """
    Manages Gemini API connections with automatic key rotation
    and dynamic model selection.
    """
    def __init__(self, api_keys: Optional[List[str]] = None):
        if not api_keys:
            # In a deployed environment, secrets are loaded as environment variables.
            gemini_keys_str = os.environ.get("GEMINI_API_KEYS")
            if gemini_keys_str:
                api_keys = [key.strip() for key in gemini_keys_str.split(',')]
            else:
                # Fallback for local development if .env is used
                api_keys = GEMINI_API_KEYS

        if not api_keys:
            raise ValueError("GEMINI_API_KEYS are not configured.")
        
        self._api_key_cycler = cycle(api_keys)
        self.active_key = None

    def _get_next_key(self) -> str:
        """Rotates to the next available API key."""
        self.active_key = next(self._api_key_cycler)
        return self.active_key

    def get_llm(self, 
                model_name: str = "gemini-1.5-pro-latest", 
                temperature: float = 0.1) -> ChatGoogleGenerativeAI:
        """
        Provides a configured LLM instance with rotated API key.
        
        Args:
            model_name: Gemini model identifier
            temperature: Response creativity (0.0-1.0)
        
        Returns:
            Configured ChatGoogleGenerativeAI instance
        """
        api_key = self._get_next_key()
        print(f"[GeminiManager] Using model: {model_name}")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            verbose=True,
            temperature=temperature,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )

# Singleton instance
gemini_manager = GeminiConnectionManager()

def get_gemini_manager():
  """Factory function to get an instance of the GeminiConnectionManager."""
  return gemini_manager
