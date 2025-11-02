from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Optional

class TradingStrategy(ABC):
    """
    Abstract base class for a trading strategy.
    
    Supports multi-asset trading with asset-class-specific parameter adaptations.
    """
    name: str
    description: str
    min_bars_required: int
    
    def __init__(self, asset_class: Optional[str] = None):
        """
        Initialize strategy with optional asset class.
        
        Args:
            asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None for US_EQUITY)
        """
        self.asset_class = asset_class or 'US_EQUITY'
        self.params = self._get_asset_specific_params()
    
    def _get_asset_specific_params(self) -> Dict:
        """
        Get asset-class-specific parameters for the strategy.
        
        Different asset classes have different characteristics:
        - CRYPTO: 24/7 trading, higher volatility, different volume dynamics
        - US_EQUITY: Market hours, standard volatility, reliable volume
        - FOREX: 23/5 trading, currency-specific patterns
        
        Returns:
            Dictionary with parameter adjustments for the asset class
        """
        base_params = {
            'atr_multiplier': 2.0,
            'volume_weight': 0.15,
            'atr_period': 14,
            'adx_threshold': 25.0,
            'min_confidence': 0.6,
        }
        
        if self.asset_class == 'CRYPTO':
            # Crypto has higher volatility and 24/7 trading
            return {
                'atr_multiplier': 3.0,  # Wider stops for volatility
                'volume_weight': 0.05,  # Less weight on volume (24/7 varies)
                'atr_period': 20,       # Longer period for smoother ATR
                'adx_threshold': 20.0,  # Lower threshold (more choppy)
                'min_confidence': 0.55, # Slightly lower minimum
            }
        elif self.asset_class == 'FOREX':
            # Forex has tight spreads and different dynamics
            return {
                'atr_multiplier': 2.5,  # Medium stops
                'volume_weight': 0.0,   # Volume less relevant in forex
                'atr_period': 14,
                'adx_threshold': 23.0,
                'min_confidence': 0.6,
            }
        else:  # US_EQUITY (default)
            return base_params

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators"""
        pass

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate BUY/SELL/HOLD signal with confidence"""
        pass

    @abstractmethod
    def validate_signal(self, df: pd.DataFrame, signal: Dict, data_feed: str) -> Dict:
        """Apply confirmation layers and adapt to data feed quality."""
        pass
