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


import threading
import random
from collections import defaultdict

class GeminiConnectionManager:
    def __init__(self,
                 api_keys: Optional[List[str]] = None,
                 temperature: float = 0.1):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured in settings")
        self.temperature = temperature
        self.primary_models = settings.primary_llm_models
        self.fallback_models = settings.fallback_llm_models
        self.key_health_threshold = settings.key_health_threshold
        self.rate_limiter = RateLimiter(rpm=settings.rate_limit_rpm, rpd=settings.rate_limit_rpd)
        self.lock = threading.Lock()

        # Key health tracking
        self.key_stats = {k: {"success": 0, "fail": 0, "last_error": None, "backoff": 0} for k in self.api_keys}
        self.key_order = list(self.api_keys)
        self.key_index = 0

    def _normalize_model(self, model: str) -> str:
        if "/" in model:
            _, short = model.split("/", 1)
            return f"{settings.llm_provider}/{short}"
        if model.startswith("gemini") or model.startswith("models/"):
            short = model
            if model.startswith("models/"):
                short = model.split("/", 1)[1]
            return f"{settings.llm_provider}/{short}"
        return f"{settings.llm_provider}/{model}"

    def _get_next_key(self) -> str:
        with self.lock:
            healthy_keys = self._get_healthy_keys()
            if not healthy_keys:
                # All keys unhealthy, use best available (lowest fail count)
                sorted_keys = sorted(self.api_keys, key=lambda k: self.key_stats[k]["fail"])
                return sorted_keys[0]
            # Round-robin among healthy keys
            key = healthy_keys[self.key_index % len(healthy_keys)]
            self.key_index += 1
            return key

    def _get_healthy_keys(self):
        healthy = []
        for k in self.api_keys:
            stats = self.key_stats[k]
            total = stats["success"] + stats["fail"]
            health = stats["success"] / total if total > 0 else 1.0
            if health >= self.key_health_threshold and stats["backoff"] <= time.time():
                healthy.append(k)
        return healthy

    def _mark_key_failure(self, key, error_code):
        stats = self.key_stats[key]
        stats["fail"] += 1
        stats["last_error"] = error_code
        # Exponential backoff: 2^fail seconds, capped at 300s
        backoff = min(2 ** stats["fail"], 300)
        stats["backoff"] = time.time() + backoff
        logger.warning(f"Key {key[:6]}... failed with {error_code}, backoff {backoff}s")

    def _mark_key_success(self, key):
        stats = self.key_stats[key]
        stats["success"] += 1
        stats["backoff"] = 0

    def get_llm(self):
        """Return a LangChain ChatGoogleGenerativeAI instance with cascading fallback and key rotation."""
        self.rate_limiter.wait_if_needed()
        cycles = 0
        max_cycles = 3
        attempt_log = []
        while cycles < max_cycles:
            for key in self.api_keys:
                # Skip key if in backoff
                if self.key_stats[key]["backoff"] > time.time():
                    continue
                for model in self.primary_models + self.fallback_models:
                    model_id = self._normalize_model(model)
                    try:
                        if ChatGoogleGenerativeAI is None:
                            raise RuntimeError("langchain_google_genai not available — install dependency or mock in tests")
                        client = ChatGoogleGenerativeAI(
                            model=model_id,
                            google_api_key=key,
                            temperature=self.temperature,
                            verbose=(settings.log_level == "DEBUG")
                        )
                        # Test instantiation by making a dummy call if needed
                        self._mark_key_success(key)
                        logger.info(f"Gemini LLM instantiated: model={model_id}, key={key[:6]}...")
                        attempt_log.append((model_id, key, "success"))
                        return client
                    except Exception as e:
                        error_code = getattr(e, "status_code", None)
                        logger.error(f"Gemini LLM failed: model={model_id}, key={key[:6]}..., error={e}")
                        attempt_log.append((model_id, key, f"fail:{error_code}"))
                        if error_code in [401, 429, 503]:
                            self._mark_key_failure(key, error_code)
                        continue
            cycles += 1
            logger.warning(f"Gemini LLM: All keys/models failed, cycle {cycles}/{max_cycles}. Waiting 60s before retry.")
            time.sleep(60)
        # After 3 cycles, raise critical exception
        logger.critical(f"Gemini LLM: Exhausted all keys/models after {max_cycles} cycles. Attempts: {attempt_log}")
        raise RuntimeError("Gemini LLM: All keys/models failed after retries.")

# Global singleton
gemini_manager = GeminiConnectionManager()
