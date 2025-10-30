"""
Gemini connector and adapter

Provides a centralized factory for creating Gemini LLM adapters that:
- normalize model identifiers to a provider-prefixed form (google/...)
- rotate API keys
- perform simple rate-limiting checks
- expose minimal metadata required by CrewAI/LiteLLM (provider, model, model_name)

This is intentionally lightweight — it wraps the LangChain `ChatGoogleGenerativeAI`
client and exposes a thin adapter with provider metadata so CrewAI can detect
the provider reliably.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from itertools import cycle
from typing import List, Optional

from src.config.settings import settings
import os

logger = logging.getLogger(__name__)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    # Defer import errors until instantiation time; allow tests to import module
    ChatGoogleGenerativeAI = None  # type: ignore


class RateLimiter:
    def __init__(self, rpm: int, rpd: int):
        self.rpm = rpm
        self.rpd = rpd
        self.minute_window = deque()
        self.day_window = deque()

    def wait_if_needed(self):
        now = time.time()
        # Clean up
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
    def __init__(self,
                 api_keys: Optional[List[str]] = None,
                 model_name: Optional[str] = None,
                 temperature: float = 0.1):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured in settings")

        self._key_cycler = cycle(self.api_keys)
        self.temperature = temperature
        self.model_name = model_name or settings.default_llm_model
        self.rate_limiter = RateLimiter(rpm=settings.rate_limit_rpm, rpd=settings.rate_limit_rpd)
        self.request_count = 0

    def _get_next_key(self) -> str:
        return next(self._key_cycler)

    def _normalize_model(self, model: str) -> str:
        # Ensure provider prefix exists (google/...)
        # Normalize provider prefix to the configured provider token (e.g. 'gemini').
        # Accept incoming values like 'google/gemini-2.5-flash' or bare ids and
        # return them as '<provider>/<model-id>' where provider is
        # `settings.llm_provider` (typically 'gemini').
        if "/" in model:
            # Split existing provider and model; replace with configured token
            _, short = model.split("/", 1)
            return f"{settings.llm_provider}/{short}"
        # Accept bare model ids like 'gemini-1.5-flash-latest' or 'models/gemini-...'
        if model.startswith("gemini") or model.startswith("models/"):
            short = model
            if model.startswith("models/"):
                short = model.split("/", 1)[1]
            return f"{settings.llm_provider}/{short}"
        # Fallback: prefix with provider
        return f"{settings.llm_provider}/{model}"

    def get_llm(self):
        """Return a LangChain ChatGoogleGenerativeAI instance."""
        self.rate_limiter.wait_if_needed()
        api_key = self._get_next_key()
        self.request_count += 1

        if ChatGoogleGenerativeAI is None:
            raise RuntimeError("langchain_google_genai not available — install dependency or mock in tests")

        try:
            # Create the LangChain wrapper client
            client = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=api_key,
                temperature=self.temperature,
                verbose=(settings.log_level == "DEBUG")
            )
            return client
        except Exception as e:
            logger.error("Failed to instantiate ChatGoogleGenerativeAI: %s", e)
            raise

# Global singleton
gemini_manager = GeminiConnectionManager()
