
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import List
import os


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
    
    # Development
    dry_run: bool = Field(default=True, description="Don't place real orders")
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=300, ge=0)
    
    @validator("gemini_api_keys")
    def validate_api_keys(cls, v):
        """Ensure at least one API key is provided."""
        keys = [k.strip() for k in v.split(',') if k.strip()]
        if not keys:
            raise ValueError("At least one Gemini API key required")
        return v
    
    @validator("ma_slow_period")
    def validate_ma_periods(cls, v, values):
        """Ensure MA periods are in correct order."""
        if "ma_fast_period" in values and "ma_medium_period" in values:
            if not (values["ma_fast_period"] < values["ma_medium_period"] < v):
                raise ValueError(
                    "MA periods must be: fast < medium < slow"
                )
        return v
    
    def get_gemini_keys_list(self) -> List[str]:
        """Return Gemini API keys as a list."""
        return [k.strip() for k in self.gemini_api_keys.split(',') if k.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.dry_run


# Global settings instance
settings = Settings()
