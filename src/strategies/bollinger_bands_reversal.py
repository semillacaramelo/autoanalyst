from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict, Optional
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class BollingerBandsReversalStrategy(TradingStrategy):
    name = "bollinger"
    description = "Bollinger Bands Mean Reversal Strategy"
    min_bars_required = 21  # For Bollinger Bands calculation
    
    def __init__(self, asset_class: Optional[str] = None):
        """
        Initialize Bollinger Bands strategy with asset-class-specific parameters.
        
        Args:
            asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None)
        """
        super().__init__(asset_class)

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for Bollinger Bands Reversal."""
        upper_band, middle_band, lower_band = TechnicalAnalysisTools.calculate_bollinger_bands(df)
        atr_period = self.params['atr_period']
        
        return {
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "rsi": TechnicalAnalysisTools.calculate_rsi(df, 14),
            "volume": df['volume'],
            "bb_width": TechnicalAnalysisTools.calculate_bollinger_band_width(df),
            "atr": TechnicalAnalysisTools.calculate_atr(df, atr_period),
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate BUY/SELL/HOLD signal based on Bollinger Bands and RSI."""
        indicators = self.calculate_indicators(df)
        price = df['close'].iloc[-1]
        lower_band = indicators["lower_band"].iloc[-1]
        upper_band = indicators["upper_band"].iloc[-1]
        rsi = indicators["rsi"].iloc[-1]

        signal = "HOLD"
        confidence = 0

        # BUY: Price touches lower band and RSI is oversold
        if price <= lower_band and rsi < 30:
            signal = "BUY"
            confidence = 0.7
            logger.info("🟢 BUY signal generated (Bollinger Lower Band touch + RSI oversold)")

        # SELL: Price touches upper band and RSI is overbought
        elif price >= upper_band and rsi > 70:
            signal = "SELL"
            confidence = 0.7
            logger.info("🔴 SELL signal generated (Bollinger Upper Band touch + RSI overbought)")

        return {
            "signal": signal,
            "confidence": confidence,
            "details": {
                "price": float(price),
                "lower_band": float(lower_band),
                "upper_band": float(upper_band),
                "rsi": float(rsi),
                "timestamp": str(df.index[-1])
            }
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict, _data_feed: str) -> Dict:
        """Apply volatility and advanced candlestick pattern confirmation with asset-class awareness."""
        # Note: This strategy is not volume-dependent, so the _data_feed parameter is unused
        # but required by the interface contract.
        if signal["signal"] == "HOLD":
            return signal

        indicators = self.calculate_indicators(df)
        bb_width = indicators["bb_width"]

        # Volatility check: Look for a recent squeeze
        volatility_confirm = bb_width.iloc[-1] > bb_width.rolling(10).min().iloc[-1]

        # Candlestick pattern recognition
        pattern_info = TechnicalAnalysisTools.recognize_candlestick_patterns(df)
        pattern_confirm = (pattern_info["type"] == "bullish" and signal["signal"] == "BUY") or \
                          (pattern_info["type"] == "bearish" and signal["signal"] == "SELL")

        confirmations = []
        confidence_boost = 0.0
        
        if volatility_confirm:
            confirmations.append("Volatility Expansion")
            confidence_boost += 0.1
            
        if pattern_confirm:
            confirmations.append(f"Candlestick Pattern ({pattern_info['pattern']})")
            confidence_boost += 0.2
            signal["details"]["candlestick_pattern"] = pattern_info['pattern']

        # Apply minimum confidence threshold
        min_confidence = self.params['min_confidence']
        if confirmations:
            signal["confidence"] = min(1.0, signal["confidence"] + confidence_boost)
            signal["validation"] = f"{' and '.join(confirmations)} confirmed ({self.asset_class})"
        else:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.3)
            signal["validation"] = f"No confirmation ({self.asset_class})"
        
        # Apply minimum confidence filter
        if signal["confidence"] < min_confidence:
            logger.info(f"Signal confidence {signal['confidence']:.2f} below minimum {min_confidence} for {self.asset_class}")
            signal["signal"] = "HOLD"
            signal["validation"] += f" (Below min confidence for {self.asset_class})"

        return signal
