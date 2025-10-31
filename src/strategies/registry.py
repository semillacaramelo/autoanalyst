from src.strategies.triple_ma import TripleMovingAverageStrategy
from src.strategies.rsi_breakout import RSIBreakoutStrategy
from src.strategies.macd_crossover import MACDCrossoverStrategy
from src.strategies.bollinger_bands_reversal import BollingerBandsReversalStrategy

AVAILABLE_STRATEGIES = {
    "3ma": TripleMovingAverageStrategy,
    "rsi_breakout": RSIBreakoutStrategy,
    "macd": MACDCrossoverStrategy,
    "bollinger": BollingerBandsReversalStrategy
}

def get_strategy(name: str):
    """Factory function for strategy instantiation"""
    cls = AVAILABLE_STRATEGIES.get(name)
    if not cls:
        raise ValueError(f"Strategy '{name}' not found. Available: {list(AVAILABLE_STRATEGIES.keys())}")
    return cls()
