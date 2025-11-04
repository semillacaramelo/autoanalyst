"""
Market Scanning Tools
Provides functions for scanning a universe of assets to identify trading opportunities.

⚠️  CRITICAL ARCHITECTURE NOTE (November 4, 2025) ⚠️
=====================================================================================================
**STATUS**: This module requires architectural refactoring as part of Phase 4.

**ROOT CAUSE**: CrewAI uses LLM-first architecture where all inter-tool communication is JSON-
serialized. DataFrames serialize to unparseable string representations, breaking workflows.

**THE PROBLEM**:
When `fetch_universe_data()` returns Dict[str, pd.DataFrame], the DataFrame objects exist in Python
memory. However, when the NEXT agent/tool tries to use this data:

1. Agent receives DataFrames in context
2. LLM processes context and decides to call `analyze_volatility(symbol_data)`
3. CrewAI serializes parameters to JSON for LLM → DataFrame becomes STRING like:
   "BTC/USD": "open        high        low       close     volume
   timestamp
   2025-10-31 03:00:00+00:00  184.7100  185.960000  184.5000  185.240  1160.315..."

4. Tool receives STRINGS, not DataFrames → TypeError when trying df['high']

**EVIDENCE**:
- Logs: "TypeError: string indices must be integers, not 'str'" (line 84 in analysis_tools.py)
- Scanner completes cycles but finds ZERO opportunities (empty results)
- All 11 crypto symbols fetched successfully, ALL 11 fail analysis

**WHY CONVERSION ATTEMPTS FAIL**:
- String format is unparseable (not JSON, not CSV, just __str__ representation)
- No way to reconstruct DataFrame from "open high low..." string
- Even dict detection fails because LLM sends strings, not dicts in real usage

**THE FIX** (See `docs/CREWAI_REFERENCE.md` for full patterns):

**Option A (Recommended): Independent Tool Fetching**
```python
@tool("Analyze Volatility")
def analyze_volatility(symbols: List[str]) -> dict:
    # Each tool fetches its own data (no passing)
    results = {}
    for symbol in symbols:
        df = alpaca_manager.fetch_historical_bars(symbol, "1Hour", 100)
        atr = calculate_atr(df)
        results[symbol] = {"atr": float(atr), "score": ...}
    return results  # JSON-serializable
```

**Option B: Knowledge Sources Pattern**
```python
# Store data in CrewAI knowledge base during crew initialization
knowledge = MarketDataKnowledgeSource(symbols)
crew = Crew(agents=[...], tasks=[...], knowledge_sources=[knowledge])

# Tools query knowledge by symbol name (strings)
@tool("Analyze Volatility from Knowledge")
def analyze(symbols: List[str]) -> dict:
    # Tool queries knowledge base or fetches independently
    ...
```

**Option C: CrewAI Flows**
```python
# Move data pipeline to Flow (DataFrames OK in Flow code)
class MarketScanFlow(Flow):
    @start()
    def fetch_and_analyze(self):
        data = fetch_ohlcv()  # DataFrame OK here
        metrics = calculate_metrics(data)  # DataFrame OK here
        return metrics  # Only JSON goes to Crew

    @listen(fetch_and_analyze)
    def generate_signals(self, metrics: dict):
        crew = Crew(...)  # Crew only gets JSON
        return crew.kickoff(inputs={"metrics": metrics})
```

**MIGRATION PLAN**: See Phase 4 in FEATURE_ROADMAP.md

**REFERENCES**:
- `docs/CREWAI_REFERENCE.md` - Complete architecture guide
- `docs/FEATURE_ROADMAP.md` - Phase 4 implementation plan
- CrewAI Official Docs: https://docs.crewai.com/concepts/tools

**DO NOT** attempt to "fix" this by adding more serialization logic. The entire pattern of passing
DataFrames between tools is incompatible with CrewAI's design. Refactoring required.
=====================================================================================================
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

        ⚠️  DEPRECATED (Phase 4 - November 4, 2025) ⚠️
        -----------------------------------------------
        This function is deprecated due to CrewAI architecture constraints.
        Returning Dict[str, DataFrame] causes serialization issues when passed between tools.

        **NEW PATTERN**: Tools now fetch their own data internally.
        - Use analyze_volatility(symbols) instead of fetch_universe_data() + analyze_volatility(data)
        - Use analyze_technical_setup(symbols) instead of fetch_universe_data() + analyze_technical_setup(data)
        - Use filter_by_liquidity(symbols) instead of fetch_universe_data() + filter_by_liquidity(data)

        **This function is kept for:**
        1. Backwards compatibility with existing code
        2. Testing/debugging purposes
        3. Direct Python usage (non-CrewAI contexts)

        **DO NOT USE** in CrewAI tool chains - tools will fail with TypeError.
        -----------------------------------------------

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
    def analyze_volatility(
        symbols: List[str],
        timeframe: str = "1Hour",
        limit: int = 100,
        asset_class: Optional[str] = None
    ) -> List[Dict]:
        """
        Analyze the volatility of each symbol using Independent Tool Fetching pattern.

        ✅ PHASE 4 REFACTORED (November 4, 2025)
        -----------------------------------------
        **NEW BEHAVIOR**: Accepts List[str] (symbol names) and fetches data internally.
        This follows CrewAI's Independent Tool Fetching pattern (Option A from architecture guide).

        **WHY THIS WORKS**: 
        - Tool parameters are JSON-serializable (List[str])
        - Tool is self-sufficient (fetches its own data)
        - Returns JSON-serializable results (List[Dict])
        - No DataFrame passing between tools

        **PATTERN**: Each tool fetches what it needs based on simple parameters.
        See docs/CREWAI_REFERENCE.md Section 4.1 for complete pattern documentation.

        Args:
            symbols: List of symbol strings to analyze (e.g., ['SPY', 'BTC/USD'])
            timeframe: Bar timeframe for volatility calculation (default: '1Hour')
            limit: Number of bars to fetch (default: 100)
            asset_class: Optional asset class override ('US_EQUITY', 'CRYPTO', 'FOREX')

        Returns:
            List of dicts with volatility metrics:
            [
                {
                    "symbol": "SPY",
                    "atr": 2.45,
                    "volatility_score": 65.3,
                    "status": "success"
                },
                ...
            ]

        Examples:
            >>> analyze_volatility(['SPY', 'AAPL', 'QQQ'])
            >>> analyze_volatility(['BTC/USD', 'ETH/USD'], asset_class='CRYPTO')
        """
        if not symbols:
            logger.warning("analyze_volatility: No symbols provided")
            return []
        
        logger.info(f"Analyzing volatility for {len(symbols)} symbols...")
        volatility_results = []
        
        for symbol in symbols:
            try:
                # Auto-detect asset class if not specified
                if asset_class is None:
                    classification = asset_classifier.classify(symbol)
                    detected_class = classification['type']
                else:
                    detected_class = asset_class
                
                # Fetch data internally (Independent Tool pattern)
                df = alpaca_manager.fetch_historical_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    asset_class=detected_class
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data returned for {symbol}")
                    volatility_results.append({
                        "symbol": symbol,
                        "status": "no_data",
                        "error": "No data available"
                    })
                    continue
                
                if len(df) < 14:
                    logger.debug(f"Insufficient data for {symbol} (need 14+ bars, got {len(df)})")
                    volatility_results.append({
                        "symbol": symbol,
                        "status": "insufficient_data",
                        "bars": len(df)
                    })
                    continue
                
                # Calculate ATR (Average True Range)
                atr = TechnicalAnalysisTools.calculate_atr(df, 14)
                atr_current = float(atr.iloc[-1])
                atr_mean = float(atr.mean())
                atr_percentile = (atr_current / atr_mean) * 100 if atr_mean > 0 else 0
                
                volatility_results.append({
                    "symbol": symbol,
                    "atr": atr_current,
                    "atr_mean": atr_mean,
                    "volatility_score": min(100, atr_percentile),  # Cap at 100
                    "status": "success"
                })
                
                logger.debug(f"{symbol}: ATR={atr_current:.2f}, Score={atr_percentile:.1f}")
                
            except Exception as e:
                logger.error(f"Error analyzing volatility for {symbol}: {e}", exc_info=True)
                volatility_results.append({
                    "symbol": symbol,
                    "status": "error",
                    "error": str(e)
                })
                continue
        
        success_count = sum(1 for r in volatility_results if r.get("status") == "success")
        logger.info(f"Volatility analysis complete: {success_count}/{len(symbols)} symbols successful")
        return volatility_results

    @staticmethod
    def analyze_technical_setup(
        symbols: List[str],
        timeframe: str = "1Day",
        limit: int = 100,
        asset_class: Optional[str] = None
    ) -> List[Dict]:
        """
        Analyze the technical setup of each symbol using Independent Tool Fetching pattern.

        ✅ PHASE 4 REFACTORED (November 4, 2025)
        -----------------------------------------
        **NEW BEHAVIOR**: Accepts List[str] (symbol names) and fetches data internally.
        Each tool is self-sufficient and returns JSON-serializable results.

        Analyzes technical indicators (RSI, MACD, SMA) and provides scoring based on:
        - Trend strength (SMA crossovers)
        - Momentum (MACD crossovers)
        - Overbought/oversold conditions (RSI)

        Args:
            symbols: List of symbol strings to analyze
            timeframe: Bar timeframe for analysis (default: '1Day')
            limit: Number of bars to fetch (default: 100, need 50+ for indicators)
            asset_class: Optional asset class override

        Returns:
            List of dicts with technical analysis:
            [
                {
                    "symbol": "SPY",
                    "technical_score": 85,
                    "reason": "Strong Uptrend, Bullish MACD",
                    "indicators": {"rsi": 55.2, "macd": 1.3, "price": 450.50},
                    "status": "success"
                },
                ...
            ]
        """
        if not symbols:
            logger.warning("analyze_technical_setup: No symbols provided")
            return []
        
        logger.info(f"Analyzing technical setup for {len(symbols)} symbols...")
        technical_results = []
        
        for symbol in symbols:
            try:
                # Auto-detect asset class if not specified
                if asset_class is None:
                    classification = asset_classifier.classify(symbol)
                    detected_class = classification['type']
                else:
                    detected_class = asset_class
                
                # Fetch data internally
                df = alpaca_manager.fetch_historical_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    asset_class=detected_class
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data returned for {symbol}")
                    technical_results.append({
                        "symbol": symbol,
                        "status": "no_data",
                        "error": "No data available"
                    })
                    continue
                
                if len(df) < 50:
                    logger.debug(f"Insufficient data for {symbol} (need 50+ bars, got {len(df)})")
                    technical_results.append({
                        "symbol": symbol,
                        "status": "insufficient_data",
                        "bars": len(df)
                    })
                    continue

                # Calculate indicators
                rsi = TechnicalAnalysisTools.calculate_rsi(df, 14).iloc[-1]
                macd_line, signal_line, _ = TechnicalAnalysisTools.calculate_macd(df)
                sma_20 = TechnicalAnalysisTools.calculate_sma(df, 20).iloc[-1]
                sma_50 = TechnicalAnalysisTools.calculate_sma(df, 50).iloc[-1]
                price = df["close"].iloc[-1]

                # Scoring logic
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
                    score -= 10  # Penalize overbought
                    reasons.append("RSI Overbought (> 70)")

                technical_results.append({
                    "symbol": symbol,
                    "technical_score": max(0, min(100, score)),  # Normalize 0-100
                    "reason": ", ".join(reasons) if reasons else "Neutral",
                    "indicators": {
                        "rsi": float(rsi),
                        "macd": float(macd_line.iloc[-1]),
                        "sma_20": float(sma_20),
                        "sma_50": float(sma_50),
                        "price": float(price)
                    },
                    "status": "success"
                })
                
                logger.debug(f"{symbol}: Score={score}, RSI={rsi:.1f}, MACD={macd_line.iloc[-1]:.2f}")
                
            except Exception as e:
                logger.error(f"Error analyzing technical setup for {symbol}: {e}", exc_info=True)
                technical_results.append({
                    "symbol": symbol,
                    "status": "error",
                    "error": str(e)
                })
                continue
        
        success_count = sum(1 for r in technical_results if r.get("status") == "success")
        logger.info(f"Technical analysis complete: {success_count}/{len(symbols)} symbols successful")
        return technical_results

    @staticmethod
    def filter_by_liquidity(
        symbols: List[str],
        min_volume: int = 1_000_000,
        timeframe: str = "1Day",
        limit: int = 30,
        asset_class: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter symbols by their average trading volume using Independent Tool Fetching pattern.

        ✅ PHASE 4 REFACTORED (November 4, 2025)
        -----------------------------------------
        **NEW BEHAVIOR**: Accepts List[str] (symbol names) and fetches data internally.

        Args:
            symbols: List of symbol strings to filter
            min_volume: Minimum average daily volume threshold (default: 1M)
            timeframe: Bar timeframe for volume calculation (default: '1Day')
            limit: Number of bars to average (default: 30 for monthly average)
            asset_class: Optional asset class override

        Returns:
            List of dicts with liquidity metrics:
            [
                {
                    "symbol": "SPY",
                    "avg_volume": 85000000,
                    "liquidity_score": 100,
                    "is_liquid": true,
                    "status": "success"
                },
                ...
            ]
        """
        if not symbols:
            logger.warning("filter_by_liquidity: No symbols provided")
            return []
        
        logger.info(f"Filtering liquidity for {len(symbols)} symbols (min_volume: {min_volume:,})...")
        liquidity_results = []
        
        for symbol in symbols:
            try:
                # Auto-detect asset class if not specified
                if asset_class is None:
                    classification = asset_classifier.classify(symbol)
                    detected_class = classification['type']
                else:
                    detected_class = asset_class
                
                # Fetch data internally
                df = alpaca_manager.fetch_historical_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    asset_class=detected_class
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data returned for {symbol}")
                    liquidity_results.append({
                        "symbol": symbol,
                        "status": "no_data",
                        "error": "No data available"
                    })
                    continue
                
                if "volume" not in df.columns:
                    logger.warning(f"No volume data for {symbol}")
                    liquidity_results.append({
                        "symbol": symbol,
                        "status": "no_volume_data",
                        "error": "Volume column missing"
                    })
                    continue
                
                avg_volume = float(df["volume"].mean())
                is_liquid = avg_volume >= min_volume
                liquidity_score = min(100, (avg_volume / min_volume) * 100)  # Score relative to minimum

                liquidity_results.append({
                    "symbol": symbol,
                    "avg_volume": avg_volume,
                    "liquidity_score": liquidity_score,
                    "is_liquid": is_liquid,
                    "status": "success"
                })
                
                logger.debug(f"{symbol}: Avg Volume={avg_volume:,.0f}, Liquid={is_liquid}")
                
            except Exception as e:
                logger.error(f"Error filtering liquidity for {symbol}: {e}", exc_info=True)
                liquidity_results.append({
                    "symbol": symbol,
                    "status": "error",
                    "error": str(e)
                })
                continue
        
        liquid_count = sum(1 for r in liquidity_results if r.get("is_liquid"))
        logger.info(f"Liquidity filtering complete: {liquid_count}/{len(symbols)} symbols are liquid")
        return liquidity_results


market_scan_tools = MarketScanTools()
