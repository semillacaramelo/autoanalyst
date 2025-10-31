from typing import Dict
import pandas as pd
from src.strategies.base_strategy import TradingStrategy
from src.config.settings import settings

class RSIBreakoutStrategy(TradingStrategy):
    name = "rsi_breakout"
    description = "RSI Breakout: Buy on RSI(14) > 30, Sell on RSI(14) < 70, with volume, ADX, and 50 SMA confirmations"
    min_bars_required = 50 + 2

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        close = df['close']
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        sma_50 = close.rolling(window=50).mean()
        return {
            "rsi": rsi,
            "sma_50": sma_50
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        indicators = self.calculate_indicators(df)
        rsi = indicators["rsi"].iloc[-1]
        rsi_prev = indicators["rsi"].iloc[-2] if len(df) > 1 else rsi
        sma_50 = indicators["sma_50"].iloc[-1]
        price = df['close'].iloc[-1]

        signal = "HOLD"
        if rsi_prev < 30 and rsi >= 30:
            signal = "BUY"
        elif rsi_prev > 70 and rsi <= 70:
            signal = "SELL"

        return {
            "signal": signal,
            "rsi": float(rsi),
            "sma_50": float(sma_50),
            "current_price": float(price),
            "timestamp": str(df.index[-1])
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        from src.tools.analysis_tools import TechnicalAnalysisTools
        volume_conf = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        trend_conf = TechnicalAnalysisTools.calculate_trend_strength(df)
        price_above_sma = signal["current_price"] > signal["sma_50"]
        valid = (
            signal["signal"] != "HOLD"
            and volume_conf["confirmed"]
            and trend_conf["has_strong_trend"]
            and price_above_sma
        )
        return {
            "valid": valid,
            "volume_confirmation": volume_conf,
            "trend_confirmation": trend_conf,
            "price_above_50sma": price_above_sma,
            "original_signal": signal
        }
