"""
Market Scanning Tools
Provides functions for scanning a universe of assets to identify trading opportunities.
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from src.connectors.alpaca_connector import alpaca_manager
from src.tools.analysis_tools import TechnicalAnalysisTools
from src.tools.universe_manager import universe_manager
from src.utils.asset_classifier import AssetClassifier
from src.constants import SP_100_SYMBOLS
import logging

logger = logging.getLogger(__name__)

# Initialize asset classifier for multi-market support
asset_classifier = AssetClassifier()


class MarketScanTools:

    @staticmethod
    def get_sp100_symbols() -> List[str]:
        """Returns the list of S&P 100 symbols (legacy method for backwards compatibility)."""
        return SP_100_SYMBOLS

    @staticmethod
    def get_universe_symbols(
        market: Optional[str] = None, max_symbols: Optional[int] = None
    ) -> List[str]:
        """
        Get trading universe symbols for a specific market.

        Args:
            market: Market to scan ('US_EQUITY', 'CRYPTO', 'FOREX', or None for US_EQUITY)
            max_symbols: Maximum number of symbols to return (None for all)

        Returns:
            List of symbols from the specified universe

        Examples:
            >>> get_universe_symbols('CRYPTO', 10)  # Top 10 crypto
            ['BTC/USD', 'ETH/USD', ...]
            >>> get_universe_symbols('US_EQUITY')  # S&P 100
            ['AAPL', 'MSFT', ...]
        """
        # Default to US_EQUITY if no market specified (backwards compatibility)
        target_market = market or 'US_EQUITY'

        logger.info(
            f"Fetching universe symbols for market: {target_market}, "
            f"max_symbols: {max_symbols or 'all'}"
        )

        return universe_manager.get_active_universe(
            market=target_market, max_symbols=max_symbols
        )

    @staticmethod
    def fetch_universe_data(
        symbols: List[str],
        timeframe: str = "1Day",
        limit: int = 100,
        asset_class: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for a universe of symbols using parallel execution.

        Uses ThreadPoolExecutor to fetch data concurrently from Alpaca API,
        dramatically improving performance for large symbol lists. With parallel
        fetching, scanning 100 symbols completes in ~1 minute vs 7+ minutes sequentially.

        Supports multi-asset class fetching (stocks, crypto, forex) with automatic
        detection via AssetClassifier.

        Args:
            symbols: List of symbols to fetch (stocks, crypto, or forex)
            timeframe: Bar timeframe (e.g., '1Day', '1Hour', '15Min')
            limit: Number of bars to fetch per symbol
            asset_class: Optional asset class override ('US_EQUITY', 'CRYPTO', 'FOREX')
                        If None, auto-detected per symbol

        Returns:
            Dictionary mapping symbols to their DataFrames (only successful fetches)

        Examples:
            >>> fetch_universe_data(['AAPL', 'MSFT'])  # Auto-detects stocks
            >>> fetch_universe_data(['BTC/USD', 'ETH/USD'], asset_class='CRYPTO')
            >>> fetch_universe_data(['EUR/USD', 'GBP/USD'], asset_class='FOREX')
        """
        universe_data = {}

        def _fetch_one(symbol: str) -> tuple:
            """
            Helper function to fetch data for a single symbol.
            Used by ThreadPoolExecutor for concurrent execution.

            Args:
                symbol: Symbol to fetch (stock/crypto/forex)

            Returns:
                Tuple of (symbol, DataFrame or None)
            """
            try:
                # Auto-detect asset class if not specified
                if asset_class is None:
                    classification = asset_classifier.classify(symbol)
                    detected_class = classification['type']
                else:
                    detected_class = asset_class

                # Fetch historical bars with asset class for proper routing
                df = alpaca_manager.fetch_historical_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    asset_class=detected_class
                )
                
                if df is not None and not df.empty:
                    logger.debug(
                        f"Fetched {len(df)} bars for {symbol} ({detected_class})"
                    )
                    return (symbol, df)
                else:
                    logger.warning(
                        f"No data returned for {symbol} ({detected_class})"
                    )
                    return (symbol, None)
            except Exception as e:
                logger.warning(f"Exception fetching data for {symbol}: {e}")
                return (symbol, None)

        # Use ThreadPoolExecutor with max_workers=10 for concurrent API calls.
        # This provides optimal throughput without overwhelming the API or system resources.
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all fetch jobs to the executor
            future_to_symbol = {
                executor.submit(_fetch_one, symbol): symbol for symbol in symbols
            }

            # Process results as they complete (faster than waiting for all)
            for future in as_completed(future_to_symbol):
                symbol, data = future.result()
                if data is not None:
                    universe_data[symbol] = data

        logger.info(
            f"Successfully fetched data for {len(universe_data)}/{len(symbols)} symbols "
            f"(asset_class: {asset_class or 'auto-detect'})"
        )
        return universe_data

    @staticmethod
    def analyze_volatility(symbol_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Analyze the volatility of each symbol."""
        if not symbol_data:
            logger.warning("analyze_volatility: No symbol_data provided")
            return []
        
        volatility_results = []
        for symbol, df in symbol_data.items():
            try:
                if len(df) > 14:
                    atr = TechnicalAnalysisTools.calculate_atr(df, 14)
                    atr_percentile = (
                        (atr.iloc[-1] / atr.mean()) * 100 if atr.mean() > 0 else 0
                    )
                    volatility_results.append(
                        {
                            "symbol": symbol,
                            "atr": float(atr.iloc[-1]),
                            "volatility_score": min(
                                100, atr_percentile
                            ),  # Cap score at 100
                        }
                    )
                else:
                    logger.debug(f"Insufficient data for {symbol} (need > 14 bars, got {len(df)})")
            except Exception as e:
                logger.error(f"Error analyzing volatility for {symbol}: {e}")
                continue
        
        logger.info(f"Volatility analysis complete: {len(volatility_results)} symbols analyzed")
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
            price = df["close"].iloc[-1]

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

            if (
                macd_line.iloc[-1] > signal_line.iloc[-1]
                and macd_line.iloc[-2] <= signal_line.iloc[-2]
            ):
                score += 25
                reasons.append("Bullish MACD Crossover")
            elif (
                macd_line.iloc[-1] < signal_line.iloc[-1]
                and macd_line.iloc[-2] >= signal_line.iloc[-2]
            ):
                score += 25
                reasons.append("Bearish MACD Crossover")

            # Overbought/Oversold
            if rsi < 30:
                score += 20
                reasons.append("RSI Oversold (< 30)")
            elif rsi > 70:
                score -= 10  # Penalize overbought in a generic scan
                reasons.append("RSI Overbought (> 70)")

            technical_results.append(
                {
                    "symbol": symbol,
                    "technical_score": max(0, min(100, score)),  # Normalize to 0-100
                    "reason": ", ".join(reasons) if reasons else "Neutral",
                }
            )
        return technical_results

    @staticmethod
    def filter_by_liquidity(
        symbol_data: Dict[str, pd.DataFrame], min_volume: int = 1_000_000
    ) -> List[Dict]:
        """Filter symbols by their average trading volume."""
        liquidity_results = []
        for symbol, df in symbol_data.items():
            if df.empty or "volume" not in df.columns:
                continue
            avg_volume = df["volume"].mean()

            liquidity_results.append(
                {
                    "symbol": symbol,
                    "liquidity_score": min(
                        100, (avg_volume / min_volume) * 100
                    ),  # Score relative to minimum
                    "is_liquid": avg_volume >= min_volume,
                }
            )
        return liquidity_results


market_scan_tools = MarketScanTools()
