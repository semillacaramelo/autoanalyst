"""
Gemini LLM Connector with Rate Limiting and Key Rotation
Optimized for free tier: 10 RPM, 250 RPD (Flash model)
"""

from itertools import cycle
from typing import List, Optional
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from src.config.settings import settings
import os # Import os for environment variables
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI  # Import LangChain wrapper

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rpm: int, rpd: int):
        self.rpm = rpm
        self.rpd = rpd
        self.minute_window = deque(maxlen=rpm)
        self.day_window = deque(maxlen=rpd)
    
    def wait_if_needed(self):
        """Block if rate limits would be exceeded."""
        now = datetime.now()
        
        # Check RPM (requests per minute)
        if len(self.minute_window) >= self.rpm:
            # oldest_request should be the timestamp stored at the left-most
            # position of the deque (index 0), not the deque itself.
            oldest_request = self.minute_window[0]
            time_since_oldest = (now - oldest_request).total_seconds()
            if time_since_oldest < 60:
                sleep_time = 60 - time_since_oldest + 1  # +1 for safety
                logger.warning(f"RPM limit reached. Sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        # Check RPD (requests per day)
        if len(self.day_window) >= self.rpd:
            # Use the first element (oldest timestamp) from the deque
            oldest_request = self.day_window[0]
            time_since_oldest = (now - oldest_request).total_seconds()
            if time_since_oldest < 86400:  # 24 hours
                logger.error("RPD limit reached. Cannot proceed.")
                raise Exception("Daily API request limit exceeded")
        
        # Clean old requests from windows
        minute_ago = now - timedelta(seconds=60)
        day_ago = now - timedelta(hours=24)
        
        # Remove timestamps older than the rolling windows by comparing the
        # oldest stored timestamp (left-most element) to the cutoff times.
        while self.minute_window and self.minute_window[0] < minute_ago:
            self.minute_window.popleft()

        while self.day_window and self.day_window[0] < day_ago:
            self.day_window.popleft()
        
        # Record this request
        self.minute_window.append(now)
        self.day_window.append(now)


class GeminiConnectionManager:
    """
    Manages Gemini API connections with:
    - Round-robin key rotation
    - Rate limiting (RPM/RPD)
    - Error handling with exponential backoff
    - Request counting for monitoring
    """
    
    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        model_name: str = "gemini-1.0-pro",  # Flash for better limits
        temperature: float = 0.1
    ):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured")

        # Set the GOOGLE_API_KEY environment variable globally for litellm and genai
        os.environ["GOOGLE_API_KEY"] = self.api_keys[0]
        genai.configure(api_key=self.api_keys[0])

        # Discover models
        self.pro_model = None
        self.flash_model = None

        try:
            print("DEBUG: Calling genai.list_models()")
            models_list = list(genai.list_models())
            print(f"DEBUG: Raw models_list: {models_list}")
            logger.info(f"Discovered {len(models_list)} models")
            if not models_list:
                print("DEBUG: models_list is empty.")
            for model in models_list:
                model_name_only = model.name  # Get just the model name
                print(f"DEBUG: Checking model: {model_name_only}")
                logger.debug(f"Checking model: {model_name_only}")
                if self.pro_model is None and "pro" in model_name_only.lower():
                    self.pro_model = model_name_only
                    logger.info(f"Found pro model: {self.pro_model}")
                    print(f"DEBUG: Set pro_model: {self.pro_model}")
                elif self.flash_model is None and "flash" in model_name_only.lower():
                    self.flash_model = model_name_only
                    logger.info(f"Found flash model: {self.flash_model}")
                    print(f"DEBUG: Set flash_model: {self.flash_model}")
        except Exception as e:
            logger.error(f"Failed to discover models: {e}", exc_info=True)
            print(f"DEBUG: Model discovery failed with exception: {e}") # Immediate print for debugging
            # Initialize with empty values if discovery fails
            self.pro_model = None
            self.flash_model = None

        # Set the default model with fallback strategy
        if self.pro_model:
            self.model_name = self.pro_model
        elif self.flash_model:
            self.model_name = self.flash_model
        else:
            logger.warning("No suitable models found via discovery. Attempting known models.")
            print("DEBUG: No suitable models found via discovery. Attempting known models.")
            KNOWN_MODELS = ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
            found_working_model = False
            for known_model in KNOWN_MODELS:
                print(f"DEBUG: Trying known model: {known_model}")
                try:
                    # Attempt to create a GenerativeModel instance to validate the model name
                    genai.GenerativeModel(
                        model_name=known_model,
                        generation_config={"temperature": self.temperature}
                    )
                    self.model_name = known_model
                    logger.info(f"Successfully set fallback model to: {self.model_name}")
                    print(f"DEBUG: Successfully set fallback model to: {self.model_name}")
                    found_working_model = True
                    break
                except Exception as e:
                    logger.warning(f"Known model '{known_model}' failed to initialize: {e}")
                    print(f"DEBUG: Known model '{known_model}' failed to initialize with exception: {e}")
            
            if not found_working_model:
                print("DEBUG: No working Gemini model could be found after discovery and fallback attempts. Raising ValueError.")
                raise ValueError("No working Gemini model could be found after discovery and fallback attempts.")

        self.temperature = temperature
        self._key_cycler = cycle(self.api_keys)
        self.active_key = None

        # Rate limiting
        self.rate_limiter = RateLimiter(
            rpm=settings.rate_limit_rpm,
            rpd=settings.rate_limit_rpd
        )

        # Monitoring
        self.request_count = 0
        self.error_count = 0

        logger.info(
            f"GeminiManager initialized with {len(self.api_keys)} key(s), "
            f"model={self.model_name}, pro_model={self.pro_model}, flash_model={self.flash_model}"
        )
    
    def _get_next_key(self) -> str:
        """Rotate to the next API key."""
        self.active_key = next(self._key_cycler)
        masked = f"{self.active_key[:8]}...{self.active_key[-4:]}"
        logger.debug(f"Using API key: {masked}")
        return self.active_key
    
    def get_llm(self):
        """
        Get a configured LLM instance with rate limiting.

        Returns:
            LiteLLM-compatible model string or LLM instance

        Raises:
            Exception: If rate limits exceeded or API error
        """
        # Wait if necessary to respect rate limits
        self.rate_limiter.wait_if_needed()

        api_key = self._get_next_key()
        self.request_count += 1

        logger.debug(
            f"Creating LLM instance (request #{self.request_count})"
        )

        try:
            # For CrewAI, return LangChain ChatGoogleGenerativeAI instance
            model_clean = self.model_name.replace("models/", "")  # Remove prefix for LangChain
            print(f"DEBUG: Instantiating ChatGoogleGenerativeAI with model: {model_clean}")
            llm_instance = ChatGoogleGenerativeAI(
                model=model_clean,
                temperature=self.temperature,
                googleApiKey=api_key
            )
            logger.info(f"Returning ChatGoogleGenerativeAI instance for model: {model_clean}")
            return llm_instance

        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to create LLM instance: {e}")
            raise
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "active_keys": len(self.api_keys),
            "rpm_used": len(self.rate_limiter.minute_window),
            "rpm_limit": self.rate_limiter.rpm,
            "rpd_used": len(self.rate_limiter.day_window),
            "rpd_limit": self.rate_limiter.rpd
        }


# Global singleton instance
gemini_manager = GeminiConnectionManager()
