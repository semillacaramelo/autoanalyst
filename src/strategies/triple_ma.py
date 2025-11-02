from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict, Optional
from src.config.settings import settings
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class TripleMovingAverageStrategy(TradingStrategy):
    name = "3ma"
    description = "Triple Moving Average Crossover Strategy"
    min_bars_required = settings.ma_slow_period + 2
    
    def __init__(self, asset_class: Optional[str] = None):
        """
        Initialize Triple MA strategy with asset-class-specific parameters.
        
        Args:
            asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None)
        """
        super().__init__(asset_class)

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for 3MA."""
        # Use asset-specific ATR period
        atr_period = self.params['atr_period']
        
        return {
            "fast_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_fast_period),
            "medium_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_medium_period),
            "slow_ma": TechnicalAnalysisTools.calculate_ema(df, settings.ma_slow_period),
            "volume": df['volume'],
            "adx": TechnicalAnalysisTools.calculate_adx(df, 14),
            "atr": TechnicalAnalysisTools.calculate_atr(df, atr_period),
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
            confidence = 0.7
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

    def validate_signal(self, df: pd.DataFrame, signal: Dict, data_feed: str) -> Dict:
        """Apply confirmation layers with asset-class-aware adjustments."""
        if signal["signal"] == "HOLD":
            return signal

        volume_confirm = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        trend_confirm = TechnicalAnalysisTools.calculate_trend_strength(df)

        validation_notes = []
        confidence_boost = 0.0

        # Asset-class-aware volume confirmation
        volume_weight = self.params['volume_weight']
        if volume_confirm["confirmed"] and volume_weight > 0:
            if data_feed == 'sip':
                # SIP data: Full weight
                confidence_boost += volume_weight
                validation_notes.append(f"Volume (SIP, {self.asset_class})")
            elif data_feed == 'iex' and self.asset_class != 'CRYPTO':
                # IEX data for equities: Reduced weight
                confidence_boost += volume_weight * 0.33  # ~5% for equity
                validation_notes.append(f"Volume (IEX, {self.asset_class})")
            elif self.asset_class == 'CRYPTO':
                # Crypto: Even lower weight (24/7 volume varies)
                confidence_boost += volume_weight
                validation_notes.append(f"Volume ({self.asset_class})")

        # Trend confirmation with asset-specific ADX threshold
        adx_threshold = self.params['adx_threshold']
        if trend_confirm["has_strong_trend"]:
            adx_value = TechnicalAnalysisTools.calculate_adx(df, 14).iloc[-1]
            if adx_value > adx_threshold:
                confidence_boost += 0.15
                validation_notes.append(f"Trend Strength (ADX>{adx_threshold})")

        # Apply minimum confidence threshold
        min_confidence = self.params['min_confidence']
        if not validation_notes:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.3)
            signal["validation"] = f"No confirmation ({self.asset_class})"
        else:
            signal["confidence"] = min(1.0, signal["confidence"] + confidence_boost)
            signal["validation"] = ", ".join(validation_notes)
        
        # Apply minimum confidence filter
        if signal["confidence"] < min_confidence:
            logger.info(f"Signal confidence {signal['confidence']:.2f} below minimum {min_confidence} for {self.asset_class}")
            signal["signal"] = "HOLD"
            signal["validation"] += f" (Below min confidence for {self.asset_class})"

        return signal
