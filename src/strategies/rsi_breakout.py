from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class RSIBreakoutStrategy(TradingStrategy):
    name = "rsi_breakout"
    description = "RSI Breakout Strategy"
    min_bars_required = 52  # For 50 SMA

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for RSI Breakout."""
        return {
            "rsi": TechnicalAnalysisTools.calculate_rsi(df, 14),
            "adx": TechnicalAnalysisTools.calculate_adx(df, 14),
            "sma_50": TechnicalAnalysisTools.calculate_sma(df, 50),
            "volume": df['volume'],
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
        """Apply confirmation layers: Volume, ADX, and Price vs. 50 SMA."""
        if signal["signal"] == "HOLD":
            return signal

        indicators = self.calculate_indicators(df)
        adx_latest = indicators["adx"].iloc[-1]
        price_latest = df['close'].iloc[-1]
        sma_50_latest = indicators["sma_50"].iloc[-1]

        volume_confirm = TechnicalAnalysisTools.calculate_volume_confirmation(df)

        adx_confirm = adx_latest > 25
        price_confirm = price_latest > sma_50_latest if signal["signal"] == "BUY" else price_latest < sma_50_latest

        confirmations = []
        confidence_boost = 0.0

        if volume_confirm["confirmed"]:
            boost = 0.15 if data_feed == 'sip' else 0.05
            confidence_boost += boost
            confirmations.append(f"Volume ({data_feed.upper()})")

        if adx_confirm:
            confidence_boost += 0.10
            confirmations.append("ADX Trend")

        if price_confirm:
            confidence_boost += 0.10
            confirmations.append("Price vs SMA50")

        if confirmations:
            signal["confidence"] = min(1.0, signal["confidence"] + confidence_boost)
            signal["validation"] = ", ".join(confirmations)
        else:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.2)
            signal["validation"] = "No confirmations met"

        return signal
