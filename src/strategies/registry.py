from typing import Dict, Type, Optional
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


def get_strategy(name: str, asset_class: Optional[str] = None) -> TradingStrategy:
    """
    Factory function for strategy instantiation with asset-class awareness.

    Args:
        name: Strategy name ('3ma', 'rsi_breakout', 'macd', 'bollinger')
        asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None for US_EQUITY)

    Returns:
        Initialized strategy instance with asset-class-specific parameters

    Raises:
        ValueError: If strategy name is not found
    """
    strategy_class = AVAILABLE_STRATEGIES.get(name)
    if not strategy_class:
        raise ValueError(f"Strategy '{name}' not found.")
    return strategy_class(asset_class=asset_class)
