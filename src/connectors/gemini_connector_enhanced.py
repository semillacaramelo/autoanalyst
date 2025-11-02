"""
Enhanced Gemini Connector with Dynamic Model Discovery and Intelligent Quota Management

This connector is specifically designed for free tier usage and implements:
- Dynamic model discovery via Google Gemini API
- Intelligent fallback: Flash (preferred) -> Pro -> Next key
- Per-key, per-model quota tracking
- Automatic model and key rotation based on quota exhaustion
- Free tier optimized rate limits (Flash: 10 RPM/250 RPD, Pro: 2 RPM/50 RPD)

Reference: https://ai.google.dev/gemini-api/docs/rate-limits
"""

from __future__ import annotations
import logging
import threading
import time
from collections import deque, defaultdict
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from src.config.settings import settings

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai.types import Model
except ImportError:
    genai = None
    Model = None


class ModelTier(Enum):
    """Model tier classification for quota management"""

    FLASH = "flash"  # Preferred: Higher quota (10 RPM, 250 RPD)
    PRO = "pro"  # Fallback: Lower quota (2 RPM, 50 RPD)


@dataclass
class ModelQuota:
    """Quota limits for a specific model tier (free tier)"""

    rpm: int  # Requests per minute
    rpd: int  # Requests per day
    tpm: int  # Tokens per minute


# Free tier quotas from official documentation
FREE_TIER_QUOTAS = {
    ModelTier.FLASH: ModelQuota(rpm=10, rpd=250, tpm=250000),
    ModelTier.PRO: ModelQuota(rpm=2, rpd=50, tpm=125000),
}


class ModelQuotaTracker:
    """
    Tracks quota usage per API key per model tier.
    Implements per-key, per-model quota tracking for intelligent fallback.
    """

    def __init__(self):
        # key -> tier -> deque of timestamps
        self.minute_windows: Dict[str, Dict[ModelTier, deque]] = defaultdict(
            lambda: {ModelTier.FLASH: deque(), ModelTier.PRO: deque()}
        )
        self.day_windows: Dict[str, Dict[ModelTier, deque]] = defaultdict(
            lambda: {ModelTier.FLASH: deque(), ModelTier.PRO: deque()}
        )

    def can_use_model(self, api_key: str, tier: ModelTier) -> bool:
        """Check if we can make a request with this key+tier combination"""
        now = time.time()
        quota = FREE_TIER_QUOTAS[tier]

        # Clean old entries
        minute_window = self.minute_windows[api_key][tier]
        day_window = self.day_windows[api_key][tier]

        while minute_window and now - minute_window[0] > 60:
            minute_window.popleft()
        while day_window and now - day_window[0] > 86400:
            day_window.popleft()

        # Check limits
        if len(minute_window) >= quota.rpm:
            return False
        if len(day_window) >= quota.rpd:
            return False

        return True

    def record_request(self, api_key: str, tier: ModelTier):
        """Record that a request was made with this key+tier"""
        now = time.time()
        self.minute_windows[api_key][tier].append(now)
        self.day_windows[api_key][tier].append(now)

    def get_wait_time(self, api_key: str, tier: ModelTier) -> Optional[float]:
        """Get seconds to wait before next request is allowed, or None if ready"""
        now = time.time()
        quota = FREE_TIER_QUOTAS[tier]

        minute_window = self.minute_windows[api_key][tier]
        day_window = self.day_windows[api_key][tier]

        # Check RPM limit
        if len(minute_window) >= quota.rpm and minute_window:
            oldest = minute_window[0]
            wait_time = 60 - (now - oldest) + 0.5
            if wait_time > 0:
                return wait_time

        # Check RPD limit
        if len(day_window) >= quota.rpd:
            # Quota exhausted for the day
            return None  # Indicates need to switch key or tier

        return 0  # Ready to go


class DynamicModelManager:
    """
    Manages dynamic model discovery and selection.
    Queries Gemini API for available models and classifies them.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._models_cache: Optional[List[Model]] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 3600  # Cache for 1 hour

    def get_available_models(self, force_refresh: bool = False) -> List[Model]:
        """Query API for available models with caching"""
        now = time.time()

        if (
            not force_refresh
            and self._models_cache
            and (now - self._cache_time) < self._cache_ttl
        ):
            return self._models_cache

        try:
            if genai is None:
                raise RuntimeError("google-genai not available")

            client = genai.Client(api_key=self.api_key)
            models = list(client.models.list())

            self._models_cache = models
            self._cache_time = now

            logger.info(f"Discovered {len(models)} available models from Gemini API")
            return models

        except Exception as e:
            logger.error(f"Failed to query available models: {e}")
            # Return empty list on failure, will fall back to configured defaults
            return []

    def classify_model(self, model_name: str) -> ModelTier:
        """Classify a model into Flash or Pro tier"""
        model_lower = model_name.lower()

        if "flash" in model_lower:
            return ModelTier.FLASH
        elif "pro" in model_lower:
            return ModelTier.PRO
        else:
            # Default to Flash for unknown models
            return ModelTier.FLASH

    def get_preferred_models(self) -> Tuple[List[str], List[str]]:
        """
        Get lists of Flash and Pro models, prioritizing 2.5 versions.
        Returns: (flash_models, pro_models)
        """
        models = self.get_available_models()

        if not models:
            # Fallback to configured defaults
            logger.warning("Using configured default models (API query failed)")
            return (settings.primary_llm_models, settings.fallback_llm_models)

        flash_models = []
        pro_models = []

        for model in models:
            model_name = model.name.replace("models/", "")

            # Skip if not a generative model
            if "generateContent" not in getattr(
                model, "supported_generation_methods", []
            ):
                continue

            if "flash" in model_name.lower():
                flash_models.append(model_name)
            elif "pro" in model_name.lower():
                pro_models.append(model_name)

        # Prioritize 2.5 versions (most recent)
        flash_models.sort(key=lambda x: ("2.5" in x, "2.0" in x, x), reverse=True)
        pro_models.sort(key=lambda x: ("2.5" in x, "2.0" in x, x), reverse=True)

        logger.info(
            f"Classified models - Flash: {len(flash_models)}, Pro: {len(pro_models)}"
        )
        logger.debug(f"Flash models: {flash_models[:3]}")  # Log top 3
        logger.debug(f"Pro models: {pro_models[:3]}")

        # Return top 3 of each for efficiency
        return (
            flash_models[:3] if flash_models else ["gemini-2.5-flash"],
            pro_models[:3] if pro_models else ["gemini-2.5-pro"],
        )


class EnhancedGeminiConnectionManager:
    """
    Enhanced Gemini connector with dynamic model discovery and intelligent quota management.

    Strategy:
    1. Try Flash models with first available key (preferred, higher quota)
    2. If Flash quota exhausted on this key, try Pro on same key
    3. If Pro also exhausted, move to next key and try Flash
    4. Continue until a successful connection or all keys exhausted
    """

    def __init__(self, api_keys: Optional[List[str]] = None):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured")

        self.quota_tracker = ModelQuotaTracker()
        self.model_manager = DynamicModelManager(self.api_keys[0])

        # Get dynamic model lists
        self.flash_models, self.pro_models = self.model_manager.get_preferred_models()

        # Thread lock for ensuring atomic quota checking and model selection during parallel execution.
        # Prevents race conditions when multiple trading crews run concurrently and attempt to access
        # the Gemini API simultaneously. This ensures only one thread can check and consume quota
        # at a time, preventing quota exhaustion and 429 errors.
        self._lock = threading.Lock()

        logger.info(
            f"Enhanced Gemini connector initialized with {len(self.api_keys)} keys"
        )
        logger.info(f"Preferred Flash models: {self.flash_models}")
        logger.info(f"Fallback Pro models: {self.pro_models}")

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """Mask API key for secure logging"""
        if len(api_key) <= 4:
            return "***"
        return f"...{api_key[-4:]}"

    def get_llm_for_crewai(self, estimated_requests: int = 8) -> Tuple[str, str]:
        """
        Get the best available model and API key for CrewAI.

        Args:
            estimated_requests: Estimated number of API calls this crew will make.
                               Default is 8 (conservative estimate that fits within Flash RPM limit of 10).
                               This is used to reserve quota and prevent 429 errors.

        Returns:
            (model_name, api_key): Model name with "gemini/" prefix and API key to use

        Raises:
            RuntimeError: If no model/key combination is available

        Thread-safe: Uses a lock to ensure atomic quota checking during parallel execution.
        
        Note: This method reserves quota for multiple requests (estimated_requests) to prevent
        429 RESOURCE_EXHAUSTED errors. CrewAI makes many API calls per crew execution,
        but we limit to 8 to stay within Flash's 10 RPM limit. The system will automatically
        throttle additional requests through rate limiting.
        """
        with self._lock:
            # Try each key
            for key_idx, api_key in enumerate(self.api_keys):
                masked_key = self.mask_api_key(api_key)

                # Try Flash models first (preferred due to higher quota)
                for model in self.flash_models:
                    tier = ModelTier.FLASH
                    quota = FREE_TIER_QUOTAS[tier]

                    # Check if we have enough quota for estimated requests
                    if self._has_quota_for_requests(api_key, tier, estimated_requests):
                        wait_time = self.quota_tracker.get_wait_time(api_key, tier)

                        if wait_time == 0:
                            # Ready to use - reserve quota for all estimated requests
                            for _ in range(estimated_requests):
                                self.quota_tracker.record_request(api_key, tier)
                            logger.info(
                                f"Selected Flash model {model} with key {masked_key} "
                                f"(reserved {estimated_requests} requests, RPM: {quota.rpm}, RPD: {quota.rpd})"
                            )
                            return (f"gemini/{model}", api_key)
                        elif wait_time and wait_time > 0:
                            # Need to wait for RPM
                            logger.info(
                                f"Waiting {wait_time:.1f}s for Flash RPM limit on key {masked_key}"
                            )
                            time.sleep(wait_time)
                            # Reserve quota for all estimated requests
                            for _ in range(estimated_requests):
                                self.quota_tracker.record_request(api_key, tier)
                            logger.info(
                                f"Selected Flash model {model} with key {masked_key} "
                                f"(reserved {estimated_requests} requests after wait)"
                            )
                            return (f"gemini/{model}", api_key)
                        # else: wait_time is None, quota exhausted, try next

                # Flash exhausted on this key, try Pro
                for model in self.pro_models:
                    tier = ModelTier.PRO
                    quota = FREE_TIER_QUOTAS[tier]

                    # Check if we have enough quota for estimated requests
                    if self._has_quota_for_requests(api_key, tier, estimated_requests):
                        wait_time = self.quota_tracker.get_wait_time(api_key, tier)

                        if wait_time == 0:
                            # Reserve quota for all estimated requests
                            for _ in range(estimated_requests):
                                self.quota_tracker.record_request(api_key, tier)
                            logger.info(
                                f"Flash exhausted, using Pro model {model} with key {masked_key} "
                                f"(reserved {estimated_requests} requests, RPM: {quota.rpm}, RPD: {quota.rpd})"
                            )
                            return (f"gemini/{model}", api_key)
                        elif wait_time and wait_time > 0:
                            logger.info(
                                f"Waiting {wait_time:.1f}s for Pro RPM limit on key {masked_key}"
                            )
                            time.sleep(wait_time)
                            # Reserve quota for all estimated requests
                            for _ in range(estimated_requests):
                                self.quota_tracker.record_request(api_key, tier)
                            logger.info(
                                f"Using Pro model {model} with key {masked_key} "
                                f"(reserved {estimated_requests} requests after wait)"
                            )
                            return (f"gemini/{model}", api_key)

                logger.warning(
                    f"Insufficient quota for {estimated_requests} requests on key {masked_key}, trying next key"
                )

            # All keys and models exhausted
            raise RuntimeError(
                f"All API keys exhausted their quotas for {estimated_requests} requests. "
                f"Flash limit: {FREE_TIER_QUOTAS[ModelTier.FLASH].rpm} RPM (per minute), "
                f"{FREE_TIER_QUOTAS[ModelTier.FLASH].rpd} RPD (per day); "
                f"Pro limit: {FREE_TIER_QUOTAS[ModelTier.PRO].rpm} RPM, "
                f"{FREE_TIER_QUOTAS[ModelTier.PRO].rpd} RPD per key. "
                f"Consider adding more API keys or reducing parallel execution."
            )

    def _has_quota_for_requests(self, api_key: str, tier: ModelTier, num_requests: int) -> bool:
        """
        Check if there's enough quota available for the specified number of requests.
        
        Args:
            api_key: The API key to check
            tier: The model tier (Flash or Pro)
            num_requests: Number of requests to check for
            
        Returns:
            True if enough quota is available, False otherwise
        """
        now = time.time()
        quota = FREE_TIER_QUOTAS[tier]
        
        minute_window = self.quota_tracker.minute_windows[api_key][tier]
        day_window = self.quota_tracker.day_windows[api_key][tier]
        
        # Clean old entries
        while minute_window and now - minute_window[0] > 60:
            minute_window.popleft()
        while day_window and now - day_window[0] > 86400:
            day_window.popleft()
        
        # Check if we have room for num_requests
        return (len(minute_window) + num_requests <= quota.rpm and 
                len(day_window) + num_requests <= quota.rpd)

    def refresh_model_list(self):
        """Manually refresh the list of available models"""
        logger.info("Refreshing available models from Gemini API")
        self.flash_models, self.pro_models = self.model_manager.get_preferred_models()
        logger.info(f"Updated - Flash: {self.flash_models}, Pro: {self.pro_models}")


# Global singleton
enhanced_gemini_manager = EnhancedGeminiConnectionManager()
