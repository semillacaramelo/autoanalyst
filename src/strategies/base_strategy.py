from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict

class TradingStrategy(ABC):
    """
    Abstract base class for a trading strategy.
    """
    name: str
    description: str
    min_bars_required: int

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
