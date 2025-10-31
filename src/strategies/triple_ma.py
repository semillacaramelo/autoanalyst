from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict
from src.config.settings import settings
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class TripleMovingAverageStrategy(TradingStrategy):
    name = "3ma"
    description = "Triple Moving Average Crossover Strategy"
    min_bars_required = settings.ma_slow_period + 2

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for 3MA."""
        return {
            "fast_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_fast_period),
            "medium_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_medium_period),
            "slow_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_slow_period),
            "volume": df['volume'],
            "adx": TechnicalAnalysisTools.calculate_adx(df, 14),
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trading signal using Triple Moving Average strategy."""
        indicators = self.calculate_indicators(df)
        fast_ma = indicators["fast_ma"]
        medium_ma = indicators["medium_ma"]
        slow_ma = indicators["slow_ma"]

        # Get latest values
        fast = fast_ma.iloc[-1]
        medium = medium_ma.iloc[-1]
        slow = slow_ma.iloc[-1]

        # Previous values for crossover detection
        fast_prev = fast_ma.iloc[-2]
        medium_prev = medium_ma.iloc[-2]

        # Detect crossovers
        fast_crossed_above_medium = (fast > medium) and (fast_prev <= medium_prev)
        fast_crossed_below_medium = (fast < medium) and (fast_prev >= medium_prev)

        # Generate signal
        signal = "HOLD"
        confidence = 0

        if fast_crossed_above_medium and medium > slow:
            signal = "BUY"
<<<<<<< HEAD
            confidence = 0.7
=======
            confidence = 0.7
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
            logger.info("🟢 BUY signal generated (3MA crossover)")
        elif fast_crossed_below_medium and medium < slow:
            signal = "SELL"
            confidence = 0.7
            logger.info("🔴 SELL signal generated (3MA crossover)")

        return {
            "signal": signal,
            "confidence": confidence,
            "details": {
                "fast_ma": float(fast),
                "medium_ma": float(medium),
                "slow_ma": float(slow),
                "current_price": float(df['close'].iloc[-1]),
                "timestamp": str(df.index[-1])
            }
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        """Apply confirmation layers."""
        volume_confirm = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        trend_confirm = TechnicalAnalysisTools.calculate_trend_strength(df)

        if signal["signal"] != "HOLD":
            if volume_confirm["confirmed"] and trend_confirm["has_strong_trend"]:
                signal["confidence"] = min(1.0, signal["confidence"] + 0.2)
                signal["validation"] = "Full confirmation"
            elif volume_confirm["confirmed"]:
                signal["confidence"] = min(1.0, signal["confidence"] + 0.1)
                signal["validation"] = "Volume confirmation only"
            elif trend_confirm["has_strong_trend"]:
                signal["confidence"] = min(1.0, signal["confidence"] + 0.1)
                signal["validation"] = "Trend confirmation only"
            else:
                signal["confidence"] = max(0.0, signal["confidence"] - 0.3)
                signal["validation"] = "No confirmation"

        return signal
