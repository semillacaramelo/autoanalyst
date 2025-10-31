from typing import Dict
import pandas as pd
from src.strategies.base_strategy import TradingStrategy

class BollingerBandsReversalStrategy(TradingStrategy):
    name = "bollinger"
    description = "Bollinger Bands Reversal: Buy at lower band + RSI<30 + bullish candle, Sell at upper band + RSI>70 + bearish candle, with volume and volatility confirmation"
    min_bars_required = 22

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        close = df['close']
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + 2 * std20
        lower_band = sma20 - 2 * std20
        rsi = self._calculate_rsi(close, 14)
        return {
            "upper_band": upper_band,
            "lower_band": lower_band,
            "rsi": rsi
        }

    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _is_bullish_candle(self, df: pd.DataFrame) -> bool:
        # Simple bullish: close > open, long lower wick
        last = df.iloc[-1]
        body = last['close'] - last['open']
        lower_wick = min(last['open'], last['close']) - last['low']
        return body > 0 and lower_wick > (body * 0.5)

    def _is_bearish_candle(self, df: pd.DataFrame) -> bool:
        # Simple bearish: close < open, long upper wick
        last = df.iloc[-1]
        body = last['open'] - last['close']
        upper_wick = last['high'] - max(last['open'], last['close'])
        return body > 0 and upper_wick > (body * 0.5)

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        indicators = self.calculate_indicators(df)
        close = df['close'].iloc[-1]
        rsi = indicators["rsi"].iloc[-1]
        lower_band = indicators["lower_band"].iloc[-1]
        upper_band = indicators["upper_band"].iloc[-1]

        signal = "HOLD"
        if close <= lower_band and rsi < 30 and self._is_bullish_candle(df):
            signal = "BUY"
        elif close >= upper_band and rsi > 70 and self._is_bearish_candle(df):
            signal = "SELL"

        return {
            "signal": signal,
            "rsi": float(rsi),
            "lower_band": float(lower_band),
            "upper_band": float(upper_band),
            "current_price": float(close),
            "timestamp": str(df.index[-1])
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        from src.tools.analysis_tools import TechnicalAnalysisTools
        volume_conf = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        volatility_conf = TechnicalAnalysisTools.calculate_volatility_check(df)
        valid = (
            signal["signal"] != "HOLD"
            and volume_conf["confirmed"]
            and volatility_conf["acceptable"]
        )
        return {
            "valid": valid,
            "volume_confirmation": volume_conf,
            "volatility_confirmation": volatility_conf,
            "original_signal": signal
        }
