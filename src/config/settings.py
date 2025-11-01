
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SkipValidation
from typing import List, Literal
import os
import threading


class Settings(BaseSettings):
    """Application configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Gemini Configuration
    gemini_api_keys: str = Field(..., description="Comma-separated API keys")
    
    # Alpaca Configuration
    alpaca_api_key: str = Field(..., description="Alpaca API key")
    alpaca_secret_key: str = Field(..., description="Alpaca secret key")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL"
    )
    alpaca_data_feed: Literal['iex', 'sip'] = Field(
        default='iex',
        description="Alpaca data feed type ('iex' for free, 'sip' for paid)"
    )
    
    # Trading Parameters
    trading_symbol: str = Field(default="SPY", description="Trading symbol")
    ma_fast_period: int = Field(default=8, ge=1, description="Fast MA period")
    ma_medium_period: int = Field(default=13, ge=1)
    ma_slow_period: int = Field(default=21, ge=1)
    volume_threshold: float = Field(default=1.5, ge=1.0)
    adx_threshold: float = Field(default=25.0, ge=0, le=100)
    
    # Risk Management
    max_risk_per_trade: float = Field(default=0.02, ge=0, le=1)
    max_open_positions: int = Field(default=3, ge=1, le=10)
    daily_loss_limit: float = Field(default=0.05, ge=0, le=1)
    
    # System Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/trading_crew.log")
    rate_limit_rpm: int = Field(default=9, ge=1, le=15)
    rate_limit_rpd: int = Field(default=200, ge=1, le=1000)

    # LLM Configuration
    default_llm_model: str = Field(default="google/gemini-2.5-flash")
    llm_provider: str = Field(default="gemini")
    primary_llm_models: List[str] = Field(default=["gemini-2.5-flash"])
    fallback_llm_models: List[str] = Field(default=["gemini-2.5-pro"])
    key_health_threshold: float = Field(default=0.7)

    # Autonomous Operation
    autonomous_mode_enabled: bool = Field(default=False)
    auto_close_on_error: bool = Field(default=True)
    max_daily_trades: int = Field(default=10)
    target_markets: List[str] = Field(default=["US_EQUITY", "CRYPTO"])
    scan_interval_minutes: int = Field(default=15)
    adaptive_interval: bool = Field(default=True)
    
    # Development
    dry_run: bool = Field(default=True, description="Don't place real orders")
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=300, ge=0)
    
    def __init__(self, **data):
        """Initialize settings and thread-safe lock for caching."""
        super().__init__(**data)
        self._keys_lock = threading.Lock()
    
    @field_validator("gemini_api_keys")
    @classmethod
    def validate_api_keys(cls, v):
        """Ensure at least one API key is provided."""
        keys = [k.strip() for k in v.split(',') if k.strip()]
        if not keys:
            raise ValueError("At least one Gemini API key required")
        return v
    
    @field_validator("ma_slow_period")
    @classmethod
    def validate_ma_periods(cls, v, info):
        """Ensure MA periods are in correct order."""
        values = info.data
        if "ma_fast_period" in values and "ma_medium_period" in values:
            if not (values["ma_fast_period"] < values["ma_medium_period"] < v):
                raise ValueError(
                    "MA periods must be: fast < medium < slow"
                )
        return v
    
    def get_gemini_keys_list(self) -> List[str]:
        """
        Return Gemini API keys as a list.
        
        Parses comma-separated API keys from configuration.
        Results are cached since keys don't change during runtime.
        Thread-safe implementation.
        
        Returns:
            List of API key strings, with whitespace stripped
        """
        # Cache the parsed keys to avoid repeated string processing
        if not hasattr(self, '_cached_keys'):
            with self._keys_lock:
                # Double-check: another thread might have cached while we waited
                if not hasattr(self, '_cached_keys'):
                    self._cached_keys = [k.strip() for k in self.gemini_api_keys.split(',') if k.strip()]
        
        return self._cached_keys

    @field_validator("default_llm_model")
    @classmethod
    def validate_default_model_format(cls, v):
        """Ensure default LLM model uses provider-prefixed format to help LiteLLM routing."""
        if not v:
            raise ValueError("default_llm_model cannot be empty")
        if not v.startswith("google/"):
            raise ValueError("default_llm_model must be provider-prefixed (e.g. 'google/gemini-1.5-flash-latest')")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.dry_run

# Global settings instance
settings = Settings()
