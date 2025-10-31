from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class TradingStrategy(ABC):
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
    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        """Apply confirmation layers"""
        pass
