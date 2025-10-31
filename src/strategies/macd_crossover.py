from typing import Dict
import pandas as pd
from src.strategies.base_strategy import TradingStrategy

class MACDCrossoverStrategy(TradingStrategy):
    name = "macd"
    description = "MACD Crossover: Buy when MACD crosses above signal and histogram positive, Sell when crosses below and histogram negative, with divergence and volume confirmation"
    min_bars_required = 35

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        close = df['close']
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict:
        indicators = self.calculate_indicators(df)
        macd = indicators["macd_line"].iloc[-1]
        signal = indicators["signal_line"].iloc[-1]
        hist = indicators["histogram"].iloc[-1]
        macd_prev = indicators["macd_line"].iloc[-2] if len(df) > 1 else macd
        signal_prev = indicators["signal_line"].iloc[-2] if len(df) > 1 else signal
        hist_prev = indicators["histogram"].iloc[-2] if len(df) > 1 else hist

        trade_signal = "HOLD"
        if macd_prev < signal_prev and macd > signal and hist > 0:
            trade_signal = "BUY"
        elif macd_prev > signal_prev and macd < signal and hist < 0:
            trade_signal = "SELL"

        return {
            "signal": trade_signal,
            "macd": float(macd),
            "signal_line": float(signal),
            "histogram": float(hist),
            "timestamp": str(df.index[-1])
        }

    def validate_signal(self, df: pd.DataFrame, signal: Dict) -> Dict:
        from src.tools.analysis_tools import TechnicalAnalysisTools
        # Divergence check (simple: price vs MACD direction last 3 bars)
        price = df['close']
        macd = self.calculate_indicators(df)["macd_line"]
        price_trend = price.iloc[-1] - price.iloc[-4]
        macd_trend = macd.iloc[-1] - macd.iloc[-4]
        divergence = (price_trend > 0 and macd_trend < 0) or (price_trend < 0 and macd_trend > 0)
        volume_conf = TechnicalAnalysisTools.calculate_volume_confirmation(df)
        valid = (
            signal["signal"] != "HOLD"
            and volume_conf["confirmed"]
            and not divergence
        )
        return {
            "valid": valid,
            "volume_confirmation": volume_conf,
            "divergence": divergence,
            "original_signal": signal
        }
