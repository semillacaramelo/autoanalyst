from src.strategies.base_strategy import TradingStrategy
import pandas as pd
from typing import Dict
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

class BollingerBandsReversalStrategy(TradingStrategy):
    name = "bollinger"
    description = "Bollinger Bands Mean Reversal Strategy"
    min_bars_required = 21  # For Bollinger Bands calculation

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required indicators for Bollinger Bands Reversal."""
        upper_band, middle_band, lower_band = TechnicalAnalysisTools.calculate_bollinger_bands(df)
        return {
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "rsi": TechnicalAnalysisTools.calculate_rsi(df, 14),
            "volume": df['volume'],
            "bb_width": TechnicalAnalysisTools.calculate_bollinger_band_width(df),
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

    def _is_bullish_candle(self, ohlc: pd.Series) -> bool:
        return ohlc['close'] > ohlc['open'] and (ohlc['close'] - ohlc['open']) > (ohlc['high'] - ohlc['low']) * 0.6

    def _is_bearish_candle(self, ohlc: pd.Series) -> bool:
        return ohlc['open'] > ohlc['close'] and (ohlc['open'] - ohlc['close']) > (ohlc['high'] - ohlc['low']) * 0.6

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        """Apply volume, volatility, and candlestick pattern confirmation."""
        if signal["signal"] == "HOLD":
            return signal

        indicators = self.calculate_indicators(df)
        bb_width = indicators["bb_width"]

        # Volatility check: Look for a recent squeeze
        volatility_confirm = bb_width.iloc[-1] > bb_width.rolling(10).min().iloc[-1]

        # Candlestick check
        last_candle = df.iloc[-1]
        candle_confirm = False
        if signal["signal"] == "BUY" and self._is_bullish_candle(last_candle):
            candle_confirm = True
        elif signal["signal"] == "SELL" and self._is_bearish_candle(last_candle):
            candle_confirm = True

        confirmations = []
        if volatility_confirm:
            confirmations.append("Volatility Expansion")
            signal["confidence"] = min(1.0, signal["confidence"] + 0.1)
        if candle_confirm:
            confirmations.append("Candlestick Pattern")
            signal["confidence"] = min(1.0, signal["confidence"] + 0.15)

        if confirmations:
            signal["validation"] = f"{' and '.join(confirmations)} confirmed"
        else:
            signal["confidence"] = max(0.0, signal["confidence"] - 0.3)
            signal["validation"] = "No confirmation"

        return signal
