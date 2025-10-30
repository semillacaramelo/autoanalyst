"""
Market Data Tools
Pure Python functions for fetching and validating market data.
These tools will be used by CrewAI agents.
"""

from typing import Optional, Dict
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.connectors.alpaca_connector import alpaca_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataTools:
    """Collection of market data fetching and validation tools."""
    
    @staticmethod
    def fetch_ohlcv_data(
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> Dict:
        """
        Fetch OHLCV data and return validated result.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of bars
        
        Returns:
            Dict with keys: success, data, error, metadata
        """
        try:
            df = alpaca_manager.fetch_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            # Validate data
            validation = MarketDataTools.validate_data_completeness(df)
            
            if not validation['is_valid']:
                logger.warning(
                    f"Data validation warning: {validation['issues']}"
                )
            
            return {
                "success": True,
                "data": df,
                "error": None,
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bars_fetched": len(df),
                    "start_time": str(df.index[0]) if len(df) > 0 else None,
                    "end_time": str(df.index[-1]) if len(df) > 0 else None,
                    "validation": validation
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe
                }
            }
    
    @staticmethod
    def validate_data_completeness(df: pd.DataFrame) -> Dict:
        """
        Validate that data is complete and usable.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check for empty DataFrame
        if df is None or len(df) == 0:
            return {
                "is_valid": False,
                "issues": ["DataFrame is empty"]
            }
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check for NaN values
        if df.isnull().any().any():
            nan_cols = df.columns[df.isnull().any()].tolist()
            issues.append(f"NaN values found in: {nan_cols}")
        
        # Check for negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns and (df[col] <= 0).any():
                issues.append(f"Negative or zero prices in {col}")
        
        # Check OHLC logic (high >= low, etc.)
        if 'high' in df.columns and 'low' in df.columns:
            if (df['high'] < df['low']).any():
                issues.append("Invalid OHLC: high < low detected")
        
        # Check for gaps in time series
        if len(df) > 1:
            time_diffs = df.index.to_series().diff()[1:]
            expected_diff = time_diffs.mode() if len(time_diffs) > 0 else None
            
            if expected_diff is not None and not expected_diff.empty:
                # Use the first mode if there are multiple
                mode_diff = expected_diff.iloc[0]
                large_gaps = time_diffs[time_diffs > mode_diff * 1.5]
                if len(large_gaps) > 0:
                    issues.append(
                        f"Time series gaps detected: {len(large_gaps)} gaps"
                    )
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues if issues else None,
            "bars_count": len(df),
            "date_range": {
                # Use the first timestamp in the index for the start, not the
                # entire Index object converted to a string.
                "start": str(df.index[0]) if len(df) > 0 else None,
                "end": str(df.index[-1]) if len(df) > 0 else None
            }
        }
    
    @staticmethod
    def get_latest_price(symbol: str) -> Dict:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with latest price info
        """
        try:
            # Fetch just 1 bar
            df = alpaca_manager.fetch_historical_bars(
                symbol=symbol,
                timeframe="1Min",
                limit=1
            )
            
            if len(df) == 0:
                raise ValueError("No data returned")
            
            latest = df.iloc[-1]
            
            return {
                "success": True,
                "symbol": symbol,
                "price": float(latest['close']),
                "timestamp": df.index[-1],
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "volume": int(latest['volume'])
            }
        
        except Exception as e:
            logger.error(f"Failed to get latest price: {e}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }


# Global instance
market_data_tools = MarketDataTools()
