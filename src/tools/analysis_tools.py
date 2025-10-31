"""
Technical Analysis Tools
A collection of generic technical indicator calculation functions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)


class TechnicalAnalysisTools:
    """Technical analysis indicators and signal generation."""
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            df: OHLCV DataFrame
            period: EMA period
            column: Column to calculate EMA on
        
        Returns:
            Series with EMA values
        """
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average."""
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = df[column].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast_period=12, slow_period=26, signal_period=9, column='close'):
        """Calculate MACD, Signal Line, and Histogram."""
        fast_ema = df[column].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df[column].ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period=20, std_dev=2, column='close'):
        """Calculate Bollinger Bands."""
        sma = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (volatility indicator).
        
        Args:
            df: OHLCV DataFrame with high, low, close
            period: ATR period
        
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index (trend strength).
        
        Args:
            df: OHLCV DataFrame
            period: ADX period
        
        Returns:
            Series with ADX values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    
    @staticmethod
    def calculate_volume_confirmation(df: pd.DataFrame, threshold: float = None) -> Dict:
        """
        Check if current volume exceeds threshold.
        
        Args:
            df: OHLCV DataFrame
            threshold: Multiplier for average volume (default from settings)
        
        Returns:
            Dict with confirmation result
        """
        if threshold is None:
            threshold = settings.volume_threshold
        
        try:
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            
            volume_ratio = current_volume / avg_volume
            confirmed = volume_ratio >= threshold
            
            return {
                "confirmed": confirmed,
                "current_volume": int(current_volume),
                "average_volume": int(avg_volume),
                "volume_ratio": float(volume_ratio),
                "threshold": threshold
            }
        
        except Exception as e:
            logger.error(f"Volume confirmation failed: {e}")
            return {
                "confirmed": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_volatility_check(df: pd.DataFrame, min_atr: float = 0.3, max_atr: float = 2.0) -> Dict:
        """
        Check if volatility (ATR) is within acceptable range.
        
        Args:
            df: OHLCV DataFrame
            min_atr: Minimum acceptable ATR
            max_atr: Maximum acceptable ATR
        
        Returns:
            Dict with volatility check result
        """
        try:
            atr = TechnicalAnalysisTools.calculate_atr(df, period=14)
            current_atr = atr.iloc[-1]
            
            is_acceptable = min_atr <= current_atr <= max_atr
            
            return {
                "acceptable": is_acceptable,
                "current_atr": float(current_atr),
                "min_atr": min_atr,
                "max_atr": max_atr,
                "status": "normal" if is_acceptable else ("too_low" if current_atr < min_atr else "too_high")
            }
        
        except Exception as e:
            logger.error(f"Volatility check failed: {e}")
            return {
                "acceptable": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame, threshold: float = None) -> Dict:
        """
        Calculate trend strength using ADX.
        
        Args:
            df: OHLCV DataFrame
            threshold: Minimum ADX value (default from settings)
        
        Returns:
            Dict with trend strength analysis
        """
        if threshold is None:
            threshold = settings.adx_threshold
        
        try:
            adx = TechnicalAnalysisTools.calculate_adx(df, period=14)
            current_adx = adx.iloc[-1]
            
            has_strong_trend = current_adx >= threshold
            
            # Classify trend strength
            if current_adx < 20:
                strength = "weak"
            elif current_adx < 25:
                strength = "moderate"
            elif current_adx < 40:
                strength = "strong"
            else:
                strength = "very_strong"
            
            return {
                "has_strong_trend": has_strong_trend,
                "current_adx": float(current_adx),
                "threshold": threshold,
                "strength": strength
            }
        
        except Exception as e:
            logger.error(f"Trend strength calculation failed: {e}")
            return {
                "has_strong_trend": False,
                "error": str(e)
            }

# Global instance
technical_analysis = TechnicalAnalysisTools()
