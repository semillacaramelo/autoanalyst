from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict, Optional
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class RSIBreakoutStrategy(TradingStrategy):
    name = "rsi_breakout"
    description = "RSI Breakout Strategy"
    min_bars_required = 52  # For 50 SMA
    
    def __init__(self, asset_class: Optional[str] = None):
        """
        Initialize RSI Breakout strategy with asset-class-specific parameters.
        
        Args:
            asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None)
        """
        super().__init__(asset_class)

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for RSI Breakout."""
        atr_period = self.params['atr_period']
        
        return {
            "rsi": TechnicalAnalysisTools.calculate_rsi(df, 14),
            "adx": TechnicalAnalysisTools.calculate_adx(df, 14),
            "sma_50": TechnicalAnalysisTools.calculate_sma(df, 50),
            "volume": df['volume'],
            "atr": TechnicalAnalysisTools.calculate_atr(df, atr_period),
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate BUY/SELL/HOLD signal based on RSI breakouts."""
        indicators = self.calculate_indicators(df)
        rsi = indicators["rsi"]

        rsi_latest = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-2]

        signal = "HOLD"
        confidence = 0

        # BUY: RSI crosses above 30
        if rsi_latest > 30 and rsi_prev <= 30:
            signal = "BUY"
            confidence = 0.6
            logger.info("🟢 BUY signal generated (RSI oversold recovery)")

        # SELL: RSI crosses below 70
        elif rsi_latest < 70 and rsi_prev >= 70:
            signal = "SELL"
            confidence = 0.6
            logger.info("🔴 SELL signal generated (RSI overbought exhaustion)")

        return {
            "signal": signal,
            "confidence": confidence,
            "details": {
                "rsi": float(rsi_latest),
                "current_price": float(df['close'].iloc[-1]),
                "timestamp": str(df.index[-1])
            }
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict, data_feed: str) -> Dict:
        """Apply confirmation layers with asset-class-aware adjustments."""
        if signal["signal"] == "HOLD":
            return signal

        indicators = self.calculate_indicators(df)
        adx_latest = indicators["adx"].iloc[-1]
        price_latest = df['close'].iloc[-1]
        sma_50_latest = indicators["sma_50"].iloc[-1]

        volume_confirm = TechnicalAnalysisTools.calculate_volume_confirmation(df)

        # Asset-specific ADX threshold
        adx_threshold = self.params['adx_threshold']
        adx_confirm = adx_latest > adx_threshold
        
        price_confirm = price_latest > sma_50_latest if signal["signal"] == "BUY" else price_latest < sma_50_latest

        confirmations = []
        confidence_boost = 0.0

        # Asset-class-aware volume confirmation
        volume_weight = self.params['volume_weight']
        if volume_confirm["confirmed"] and volume_weight > 0:
            if data_feed == 'sip':
                confidence_boost += volume_weight
                confirmations.append(f"Volume (SIP, {self.asset_class})")
            elif data_feed == 'iex' and self.asset_class != 'CRYPTO':
                confidence_boost += volume_weight * 0.33
                confirmations.append(f"Volume (IEX, {self.asset_class})")
            elif self.asset_class == 'CRYPTO':
                confidence_boost += volume_weight
                confirmations.append(f"Volume ({self.asset_class})")

        if adx_confirm:
            confidence_boost += 0.10
            confirmations.append(f"ADX Trend (>{adx_threshold})")

        if price_confirm:
            confidence_boost += 0.10
            confirmations.append("Price vs SMA50")

        # Apply minimum confidence threshold
        min_confidence = self.params['min_confidence']
        if confirmations:
            signal["confidence"] = min(1.0, signal["confidence"] + confidence_boost)
            signal["validation"] = ", ".join(confirmations)
        else:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.2)
            signal["validation"] = f"No confirmations met ({self.asset_class})"
        
        # Apply minimum confidence filter
        if signal["confidence"] < min_confidence:
            logger.info(f"Signal confidence {signal['confidence']:.2f} below minimum {min_confidence} for {self.asset_class}")
            signal["signal"] = "HOLD"
            signal["validation"] += f" (Below min confidence for {self.asset_class})"

        return signal
