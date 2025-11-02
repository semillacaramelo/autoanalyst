from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict, Optional
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class MACDCrossoverStrategy(TradingStrategy):
    name = "macd"
    description = "MACD Crossover Strategy"
    min_bars_required = 34  # For the slow EMA in MACD
    
    def __init__(self, asset_class: Optional[str] = None):
        """
        Initialize MACD strategy with asset-class-specific parameters.
        
        Args:
            asset_class: Asset class ('US_EQUITY', 'CRYPTO', 'FOREX', or None)
        """
        super().__init__(asset_class)

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for MACD Crossover."""
        macd_line, signal_line, histogram = TechnicalAnalysisTools.calculate_macd(df)
        atr_period = self.params['atr_period']
        
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
            "volume": df['volume'],
            "rsi": TechnicalAnalysisTools.calculate_rsi(df, 14),
            "atr": TechnicalAnalysisTools.calculate_atr(df, atr_period),
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate BUY/SELL/HOLD signal based on MACD crossovers."""
        indicators = self.calculate_indicators(df)
        macd_line = indicators["macd_line"]
        signal_line = indicators["signal_line"]
        histogram = indicators["histogram"]

        macd_latest = macd_line.iloc[-1]
        signal_latest = signal_line.iloc[-1]
        histo_latest = histogram.iloc[-1]

        macd_prev = macd_line.iloc[-2]
        signal_prev = signal_line.iloc[-2]

        signal = "HOLD"
        confidence = 0

        # BUY: MACD crosses above Signal line and histogram is positive
        if macd_latest > signal_latest and macd_prev <= signal_prev and histo_latest > 0:
            signal = "BUY"
            confidence = 0.65
            logger.info("🟢 BUY signal generated (MACD Crossover)")

        # SELL: MACD crosses below Signal line and histogram is negative
        elif macd_latest < signal_latest and macd_prev >= signal_prev and histo_latest < 0:
            signal = "SELL"
            confidence = 0.65
            logger.info("🔴 SELL signal generated (MACD Crossover)")

        return {
            "signal": signal,
            "confidence": confidence,
            "details": {
                "macd_line": float(macd_latest),
                "signal_line": float(signal_latest),
                "histogram": float(histo_latest),
                "current_price": float(df['close'].iloc[-1]),
                "timestamp": str(df.index[-1])
            }
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict, data_feed: str) -> Dict:
        """Apply volume, RSI, and MACD divergence confirmation with asset-class awareness."""
        if signal["signal"] == "HOLD":
            return signal

        indicators = self.calculate_indicators(df)
        rsi_latest = indicators["rsi"].iloc[-1]
        histogram = indicators["histogram"]
        volume_confirm = TechnicalAnalysisTools.calculate_volume_confirmation(df)

        # Divergence check
        divergence = TechnicalAnalysisTools.detect_macd_divergence(df, histogram)
        divergence_confirm = (divergence["type"] == "bullish" and signal["signal"] == "BUY") or \
                             (divergence["type"] == "bearish" and signal["signal"] == "SELL")

        # Momentum check
        rsi_confirm = (rsi_latest > 50) if signal["signal"] == "BUY" else (rsi_latest < 50)

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

        if rsi_confirm:
            confidence_boost += 0.10
            confirmations.append("RSI Momentum")

        if divergence_confirm:
            confidence_boost += 0.25
            confirmations.append(f"MACD {divergence['type'].capitalize()} Divergence")
            signal["details"]["divergence_description"] = divergence["description"]

        # Apply minimum confidence threshold
        min_confidence = self.params['min_confidence']
        if confirmations:
            signal["confidence"] = min(1.0, signal["confidence"] + confidence_boost)
            signal["validation"] = ", ".join(confirmations)
        else:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.3)
            signal["validation"] = f"No confirmation ({self.asset_class})"
        
        # Apply minimum confidence filter
        if signal["confidence"] < min_confidence:
            logger.info(f"Signal confidence {signal['confidence']:.2f} below minimum {min_confidence} for {self.asset_class}")
            signal["signal"] = "HOLD"
            signal["validation"] += f" (Below min confidence for {self.asset_class})"

        return signal
