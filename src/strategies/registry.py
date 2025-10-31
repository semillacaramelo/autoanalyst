from typing import Dict, Type
from src.strategies.base_strategy import TradingStrategy
from src.strategies.triple_ma import TripleMovingAverageStrategy
from src.strategies.rsi_breakout import RSIBreakoutStrategy
from src.strategies.macd_crossover import MACDCrossoverStrategy
from src.strategies.bollinger_bands_reversal import BollingerBandsReversalStrategy


AVAILABLE_STRATEGIES: Dict[str, Type[TradingStrategy]] = {
    "3ma": TripleMovingAverageStrategy,
    "rsi_breakout": RSIBreakoutStrategy,
    "macd": MACDCrossoverStrategy,
    "bollinger": BollingerBandsReversalStrategy,
}

def get_strategy(name: str) -> TradingStrategy:
    """Factory function for strategy instantiation"""
    strategy_class = AVAILABLE_STRATEGIES.get(name)
    if not strategy_class:
        raise ValueError(f"Strategy '{name}' not found.")
    return strategy_class()
