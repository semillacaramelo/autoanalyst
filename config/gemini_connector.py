import os
from itertools import cycle
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import GEMINI_API_KEYS  # Import keys from config

class GeminiConnectionManager:
    """
    Manages the connection to the Gemini API, including API key rotation
    and model selection.
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

    def get_llm(self, model_name: str = "gemini-pro", temperature: float = 0.1) -> ChatGoogleGenerativeAI:
        """
        Provides a configured ChatGoogleGenerativeAI instance with a rotated API key.

        Args:
            model_name (str): The name of the Gemini model to use.
            temperature (float): The temperature for the model's responses.

        Returns:
            An instance of ChatGoogleGenerativeAI.
        """
        api_key = self._get_next_key()
        print(f"--- Using Gemini model: {model_name} with a rotated API key. ---")

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            verbose=True,
            temperature=temperature,
            google_api_key=api_key,
            convert_system_message_to_human=True # Recommended for CrewAI compatibility
        )
        return llm

# Singleton instance to be used across the application
gemini_manager = GeminiConnectionManager()
