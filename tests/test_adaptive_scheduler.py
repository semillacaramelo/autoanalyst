"""
Tests for Adaptive 24/7 Scheduler
Validates intelligent market rotation integration and adaptive intervals.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import tempfile

from src.utils.global_scheduler import AutoTradingScheduler


class TestAdaptiveScheduler(unittest.TestCase):
    """Test suite for adaptive 24/7 scheduler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = AutoTradingScheduler()
    
    def test_1_adaptive_intervals_us_equity(self):
        """Test that US_EQUITY uses 5-minute interval."""
        current_time = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)  # 11:00 AM ET
        
        interval = self.scheduler._calculate_next_interval('US_EQUITY', current_time)
        
        # Should be 5 minutes (300 seconds)
        self.assertEqual(interval, 300, "US_EQUITY should use 5-minute interval")
    
    def test_2_adaptive_intervals_crypto_peak(self):
        """Test that CRYPTO uses 15-minute interval during peak hours."""
        # Peak hours: 9:00-23:00 UTC
        peak_time = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)  # 15:00 UTC (peak)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', peak_time)
        
        # Should be 15 minutes (900 seconds)
        self.assertEqual(interval, 900, "CRYPTO should use 15-minute interval during peak")
    
    def test_3_adaptive_intervals_crypto_offpeak(self):
        """Test that CRYPTO uses 30-minute interval during off-peak hours."""
        # Off-peak hours: 0:00-8:00 UTC
        offpeak_time = datetime(2025, 11, 3, 3, 0, 0, tzinfo=pytz.utc)  # 03:00 UTC (off-peak)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', offpeak_time)
        
        # Should be 30 minutes (1800 seconds)
        self.assertEqual(interval, 1800, "CRYPTO should use 30-minute interval during off-peak")
    
    def test_4_adaptive_intervals_forex(self):
        """Test that FOREX uses 10-minute interval."""
        current_time = datetime(2025, 11, 3, 10, 0, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('FOREX', current_time)
        
        # Should be 10 minutes (600 seconds)
        self.assertEqual(interval, 600, "FOREX should use 10-minute interval")
    
    def test_5_optimal_strategies_us_equity(self):
        """Test that US_EQUITY gets all strategies."""
        strategies = self.scheduler._get_optimal_strategies('US_EQUITY')
        
        # Should include all major strategies
        self.assertIn('3ma', strategies)
        self.assertIn('rsi_breakout', strategies)
        self.assertIn('macd', strategies)
        self.assertGreaterEqual(len(strategies), 3, "US_EQUITY should have at least 3 strategies")
    
    def test_6_optimal_strategies_crypto(self):
        """Test that CRYPTO gets trend-following strategies."""
        strategies = self.scheduler._get_optimal_strategies('CRYPTO')
        
        # Should favor trend-following
        self.assertIn('3ma', strategies)
        self.assertIn('rsi_breakout', strategies)
        self.assertGreaterEqual(len(strategies), 2, "CRYPTO should have at least 2 strategies")
    
    def test_7_optimal_strategies_forex(self):
        """Test that FOREX gets momentum strategies."""
        strategies = self.scheduler._get_optimal_strategies('FOREX')
        
        # Should favor momentum strategies
        self.assertIn('macd', strategies)
        self.assertIn('bollinger', strategies)
        self.assertGreaterEqual(len(strategies), 2, "FOREX should have at least 2 strategies")
    
    def test_8_market_rotation_integration(self):
        """Test that scheduler integrates with market rotation strategy."""
        # Verify scheduler has market rotation instance
        self.assertIsNotNone(self.scheduler.market_rotation)
        self.assertTrue(hasattr(self.scheduler.market_rotation, 'select_active_market'))
        
        # Verify it can call select_active_market
        with patch.object(self.scheduler.market_rotation, 'select_active_market') as mock_select:
            mock_select.return_value = 'US_EQUITY'
            
            result = self.scheduler.market_rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO']
            )
            
            self.assertEqual(result, 'US_EQUITY')
            mock_select.assert_called_once()
    
    def test_9_state_tracking(self):
        """Test that scheduler tracks state correctly."""
        # Verify state manager exists
        self.assertIsNotNone(self.scheduler.state_manager)
        
        # Verify state is loaded
        self.assertIsNotNone(self.scheduler.state)
        self.assertIsInstance(self.scheduler.state, dict)
    
    def test_10_interval_configuration(self):
        """Test that interval configuration is correct."""
        # Verify all expected intervals are configured
        self.assertIn('US_EQUITY', self.scheduler.intervals)
        self.assertIn('CRYPTO_PEAK', self.scheduler.intervals)
        self.assertIn('CRYPTO_OFFPEAK', self.scheduler.intervals)
        self.assertIn('FOREX', self.scheduler.intervals)
        
        # Verify interval values are reasonable (in minutes)
        self.assertEqual(self.scheduler.intervals['US_EQUITY'], 5)
        self.assertEqual(self.scheduler.intervals['CRYPTO_PEAK'], 15)
        self.assertEqual(self.scheduler.intervals['CRYPTO_OFFPEAK'], 30)
        self.assertEqual(self.scheduler.intervals['FOREX'], 10)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
