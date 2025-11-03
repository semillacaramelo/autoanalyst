"""
Gemini connector and adapter

Provides a centralized factory for creating Gemini LLM adapters that:
- normalize model identifiers to a provider-prefixed form (google/...)
- rotate API keys with health tracking and backoff
- perform smart model fallback
- handle transient API errors with a robust retry mechanism
- perform simple rate-limiting checks

This is intentionally lightweight — it wraps the LangChain `ChatGoogleGenerativeAI`
client and exposes a thin adapter with provider metadata so CrewAI can detect
the provider reliably.
"""

from __future__ import annotations
import logging
import threading
import time
from collections import deque
from typing import List, Optional, Dict

from src.config.settings import settings

logger = logging.getLogger(__name__)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Using a generic exception to catch potential API errors during health checks
    from google.api_core.exceptions import GoogleAPICallError
except Exception:
    # Defer import errors until instantiation time; allow tests to import module
    ChatGoogleGenerativeAI = None  # type: ignore
    GoogleAPICallError = None  # type: ignore


class KeyHealthTracker:
    def __init__(self, api_keys: List[str], health_threshold: float):
        self.keys = api_keys
        self.health_threshold = health_threshold
        self.key_health: Dict[str, Dict] = {
            key: {"success": 0, "failure": 0, "last_used": 0, "backoff_until": 0} for key in api_keys
        }

    def _calculate_health_score(self, key: str) -> float:
        stats = self.key_health[key]
        total = stats["success"] + stats["failure"]
        if total == 0:
            return 1.0  # Optimistically assume new keys are healthy
        return stats["success"] / total

    def record_success(self, key: str):
        self.key_health[key]["success"] += 1
        self.key_health[key]["last_used"] = time.time()
        # Reset backoff on success
        self.key_health[key]["backoff_until"] = 0

    def record_failure(self, key: str):
        stats = self.key_health[key]
        stats["failure"] += 1
        stats["last_used"] = time.time()
        # Increase backoff exponentially, max 60 seconds
        backoff_duration = min(60, (2 ** (stats["failure"] - 1)))
        stats["backoff_until"] = time.time() + backoff_duration
        # Mask key for security logging - only show last 4 chars
        safe_key = f"...{key[-4:]}" if len(key) > 4 else "***"
        logger.warning(f"Key {safe_key} failed. Backing off for {backoff_duration}s.")

    def get_available_keys_sorted(self) -> List[str]:
        now = time.time()
        available_keys = [
            key
            for key, health in self.key_health.items()
            if now >= health["backoff_until"] and self._calculate_health_score(key) >= self.health_threshold
        ]

        if not available_keys:
            return []

        # Sort by health score, descending
        return sorted(available_keys, key=lambda k: self._calculate_health_score(k), reverse=True)


class RateLimiter:
    def __init__(self, rpm: int, rpd: int):
        self.rpm = rpm
        self.rpd = rpd
        self.minute_window = deque()
        self.day_window = deque()

    def wait_if_needed(self):
        now = time.time()
        # Clean up old entries
        while self.minute_window and now - self.minute_window[0] > 60:
            self.minute_window.popleft()
        while self.day_window and now - self.day_window[0] > 86400:
            self.day_window.popleft()

        if len(self.minute_window) >= self.rpm:
            oldest = self.minute_window[0]
            sleep_time = 60 - (now - oldest) + 0.5
            logger.warning("RPM rate limit reached, sleeping %.1fs", sleep_time)
            time.sleep(sleep_time)

        if len(self.day_window) >= self.rpd:
            raise RuntimeError("Daily API request limit reached")

        # Record this planned request
        self.minute_window.append(now)
        self.day_window.append(now)


class GeminiConnectionManager:
    def __init__(self, api_keys: Optional[List[str]] = None, temperature: float = 0.1):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured in settings")

        self.primary_models = settings.primary_llm_models
        self.fallback_models = settings.fallback_llm_models
        self.key_health_tracker = KeyHealthTracker(self.api_keys, settings.key_health_threshold)
        self.temperature = temperature
        self.rate_limiter = RateLimiter(rpm=settings.rate_limit_rpm, rpd=settings.rate_limit_rpd)
        self.request_count = 0
        # Thread lock for ensuring atomic rate limit checking and client creation during parallel execution.
        # Prevents race conditions when multiple trading crews run concurrently and attempt to access
        # the Gemini API simultaneously. This ensures only one thread can check and consume rate limit
        # quota at a time, preventing 429 RESOURCE_EXHAUSTED errors.
        self._lock = threading.Lock()

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """
        Mask API key for secure logging.
        Only shows last 4 characters, never the full key.

        This function is designed to prevent accidental logging of sensitive data.
        Static analysis tools may flag usage of the api_key parameter in logging
        statements, but this is a false positive since only the last 4 characters
        are ever logged - the full key is never exposed.

        Args:
            api_key: The API key to mask (full key is never logged)

        Returns:
            Masked key string showing only last 4 chars (e.g., "...XYZ123")
        """
        if len(api_key) <= 4:
            return "***"
        # Only return last 4 characters for logging - full key is never exposed
        return f"...{api_key[-4:]}"

    def get_client(self, skip_health_check: bool = False, model: str = None):
        """
        Return a LangChain ChatGoogleGenerativeAI instance with failover and key rotation.

        Args:
            skip_health_check: If True, skip the API health check (useful for testing/help commands)
            model: Specific model to use (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro").
                   If None, tries primary models first, then fallback models.

        This method includes a health check by making a real API call unless skip_health_check is True.
        Thread-safe: Uses a lock to ensure atomic rate limit checking during parallel execution.
        """
        with self._lock:
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError("langchain_google_genai not available — install dependency or mock in tests")

            models_to_try = [model] if model else (self.primary_models + self.fallback_models)
            last_exception = None
            MAX_CYCLES = 3

            for cycle_num in range(MAX_CYCLES):
                logger.info(f"Starting connection attempt cycle {cycle_num + 1}/{MAX_CYCLES}")
                available_keys = self.key_health_tracker.get_available_keys_sorted()

                if not available_keys:
                    logger.warning("All API keys are in backoff or unhealthy. Waiting 10s...")
                    time.sleep(10)
                    continue

                for api_key in available_keys:
                    for model_name in models_to_try:
                        self.rate_limiter.wait_if_needed()
                        try:
                            # Use the model name directly without "gemini/" prefix
                            # LangChain expects just the model name like "gemini-2.0-flash-exp"
                            clean_model_name = model_name.replace("gemini/", "")

                            client = ChatGoogleGenerativeAI(
                                model=clean_model_name,
                                google_api_key=api_key,
                                temperature=self.temperature,
                                verbose=(settings.log_level == "DEBUG"),
                            )

                            # Health check: Make a real, lightweight API call (unless skipped)
                            if not skip_health_check:
                                client.invoke("hello")

                            self.key_health_tracker.record_success(api_key)
                            self.request_count += 1
                            # Only log last 4 chars of API key for security
                            logger.info(
                                f"Successfully created and verified Gemini client with model {clean_model_name} and key {self.mask_api_key(api_key)}"
                            )
                            return client

                        except GoogleAPICallError as e:
                            # Mask API key for security
                            logger.warning(
                                f"API call failed for model {model_name} with key {self.mask_api_key(api_key)}: {e.message if hasattr(e, 'message') else str(e)}"
                            )
                            last_exception = e
                            # Always record failure for health tracking, regardless of error code
                            self.key_health_tracker.record_failure(api_key)
                            if e.code in [401, 403, 429]:
                                logger.error(
                                    f"Key {self.mask_api_key(api_key)} is invalid or rate-limited. Moving to next key."
                                )
                                break  # Breaks from the inner model-loop, proceeds to next key
                            # Otherwise, model might be unavailable, so try next model with same key.
                            continue
                        except Exception as e:
                            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
                            self.key_health_tracker.record_failure(api_key)
                            last_exception = e
                            # Break to try a new key on unexpected errors
                            break

                logger.warning(f"Exhausted all available keys in cycle {cycle_num + 1}. Waiting 60s before retrying.")
                time.sleep(60)

            raise RuntimeError(
                f"Failed to get a working Gemini client after {MAX_CYCLES} cycles. Last error: {last_exception}"
            )


# Global singleton
gemini_manager = GeminiConnectionManager()
