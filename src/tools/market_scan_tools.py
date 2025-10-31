"""
Market Scanning Tools
Provides functions for scanning a universe of assets to identify trading opportunities.
"""
import pandas as pd
from typing import List, Dict
from src.connectors.alpaca_connector import alpaca_manager
from src.tools.analysis_tools import TechnicalAnalysisTools
import logging

logger = logging.getLogger(__name__)

# S&P 100 as the default universe
SP_100_SYMBOLS = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'NVDA', 'TSLA', 'META', 'BRK-B', 'JNJ',
    'V', 'JPM', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'CVX', 'LLY', 'XOM',
    'AVGO', 'PFE', 'COST', 'MRK', 'PEP', 'ABBV', 'KO', 'ADBE', 'CSCO', 'TMO',
    'WMT', 'MCD', 'DIS', 'ACN', 'CRM', 'ABT', 'VZ', 'NFLX', 'CMCSA', 'NKE',
    'PM', 'NEE', 'TXN', 'HON', 'UPS', 'AMD', 'ORCL', 'LIN', 'QCOM', 'BMY',
    'WFC', 'DHR', 'INTC', 'CAT', 'LOW', 'COP', 'GS', 'IBM', 'RTX', 'MDT',
    'UNP', 'AMGN', 'BA', 'SBUX', 'GE', 'DE', 'NOW', 'T', 'AXP', 'BLK',
    'MS', 'PLD', 'AMT', 'EL', 'GILD', 'ADP', 'C', 'TJX', 'SCHW', 'ZTS',
    'ANTM', 'MO', 'DUK', 'SPGI', 'ISRG', 'CVS', 'SO', 'MMC', 'CB', 'CI',
    'FISV', 'PYPL', 'TMUS', 'SYK', 'USB', 'LMT', 'BDX', 'TGT', 'MDLZ'
]

class MarketScanTools:

    @staticmethod
    def get_sp100_symbols() -> List[str]:
        """Returns the list of S&P 100 symbols."""
        return SP_100_SYMBOLS

    @staticmethod
    def fetch_universe_data(symbols: List[str], timeframe: str = '1Day', limit: int = 100) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for a universe of symbols."""
        universe_data = {}
        for symbol in symbols:
            result = alpaca_manager.get_bars(symbol, timeframe, limit)
            if result['success']:
                universe_data[symbol] = result['data']
        return universe_data

    @staticmethod
    def analyze_volatility(symbol_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Analyze the volatility of each symbol."""
        volatility_results = []
        for symbol, df in symbol_data.items():
            if len(df) > 14:
                atr = TechnicalAnalysisTools.calculate_atr(df, 14)
                atr_percentile = (atr.iloc[-1] / atr.mean()) * 100 if atr.mean() > 0 else 0
                volatility_results.append({
                    "symbol": symbol,
                    "atr": atr.iloc[-1],
                    "volatility_score": min(100, atr_percentile) # Cap score at 100
                })
        return volatility_results

    @staticmethod
    def analyze_technical_setup(symbol_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Analyze the technical setup of each symbol."""
        technical_results = []
        for symbol, df in symbol_data.items():
            if len(df) < 50:
                continue

            # Indicators
            rsi = TechnicalAnalysisTools.calculate_rsi(df, 14).iloc[-1]
            macd_line, signal_line, _ = TechnicalAnalysisTools.calculate_macd(df)
            sma_20 = TechnicalAnalysisTools.calculate_sma(df, 20).iloc[-1]
            sma_50 = TechnicalAnalysisTools.calculate_sma(df, 50).iloc[-1]
            price = df['close'].iloc[-1]

            # Scoring
            score = 0
            reasons = []

            # Trend and Momentum
            if sma_20 > sma_50 and price > sma_20:
                score += 30
                reasons.append("Strong Uptrend (Price > 20SMA > 50SMA)")
            elif sma_20 < sma_50 and price < sma_20:
                score += 30
                reasons.append("Strong Downtrend (Price < 20SMA < 50SMA)")

            if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
                score += 25
                reasons.append("Bullish MACD Crossover")
            elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
                score += 25
                reasons.append("Bearish MACD Crossover")

            # Overbought/Oversold
            if rsi < 30:
                score += 20
                reasons.append("RSI Oversold (< 30)")
            elif rsi > 70:
                score -= 10 # Penalize overbought in a generic scan
                reasons.append("RSI Overbought (> 70)")

            technical_results.append({
                "symbol": symbol,
                "technical_score": max(0, min(100, score)), # Normalize to 0-100
                "reason": ", ".join(reasons) if reasons else "Neutral"
            })
        return technical_results

    @staticmethod
    def filter_by_liquidity(symbol_data: Dict[str, pd.DataFrame], min_volume: int = 1_000_000) -> List[Dict]:
        """Filter symbols by their average trading volume."""
        liquidity_results = []
        for symbol, df in symbol_data.items():
            if df.empty or 'volume' not in df.columns:
                continue
            avg_volume = df['volume'].mean()

            liquidity_results.append({
                "symbol": symbol,
                "liquidity_score": min(100, (avg_volume / min_volume) * 100), # Score relative to minimum
                "is_liquid": avg_volume >= min_volume
            })
        return liquidity_results

market_scan_tools = MarketScanTools()
