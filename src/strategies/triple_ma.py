from typing import Dict
import pandas as pd
from src.strategies.base_strategy import TradingStrategy
from src.config.settings import settings

class TripleMovingAverageStrategy(TradingStrategy):
    name = "3ma"
    description = "Triple Moving Average crossover strategy with confirmation"
    min_bars_required = max(settings.ma_fast_period, settings.ma_medium_period, settings.ma_slow_period) + 2

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        fast_ma = df['close'].ewm(span=settings.ma_fast_period, adjust=False).mean()
        medium_ma = df['close'].ewm(span=settings.ma_medium_period, adjust=False).mean()
        slow_ma = df['close'].ewm(span=settings.ma_slow_period, adjust=False).mean()
        return {
            "fast_ma": fast_ma,
            "medium_ma": medium_ma,
            "slow_ma": slow_ma
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        indicators = self.calculate_indicators(df)
        fast = indicators["fast_ma"].iloc[-1]
        medium = indicators["medium_ma"].iloc[-1]
        slow = indicators["slow_ma"].iloc[-1]
        fast_prev = indicators["fast_ma"].iloc[-2] if len(df) > 1 else fast
        medium_prev = indicators["medium_ma"].iloc[-2] if len(df) > 1 else medium

        fast_crossed_above_medium = (fast > medium) and (fast_prev <= medium_prev)
        fast_crossed_below_medium = (fast < medium) and (fast_prev >= medium_prev)

        signal = "HOLD"
        if fast_crossed_above_medium and medium > slow:
            signal = "BUY"
        elif fast_crossed_below_medium and medium < slow:
            signal = "SELL"

        return {
            "signal": signal,
            "fast_ma": float(fast),
            "medium_ma": float(medium),
            "slow_ma": float(slow),
            "current_price": float(df['close'].iloc[-1]),
            "fast_crossed_above": fast_crossed_above_medium,
            "fast_crossed_below": fast_crossed_below_medium,
            "timestamp": str(df.index[-1])
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        # Example confirmation: volume spike + ADX > threshold
        from src.tools.analysis_tools import TechnicalAnalysisTools
        volume_conf = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        trend_conf = TechnicalAnalysisTools.calculate_trend_strength(df)
        valid = signal["signal"] != "HOLD" and volume_conf["confirmed"] and trend_conf["has_strong_trend"]
        return {
            "valid": valid,
            "volume_confirmation": volume_conf,
            "trend_confirmation": trend_conf,
            "original_signal": signal
        }
