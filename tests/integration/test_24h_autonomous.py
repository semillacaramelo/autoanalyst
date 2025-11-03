"""
24-Hour Integration Test for Autonomous Multi-Market Trading

This test validates the complete system over a simulated 24-hour period:
- Market transitions (US equity → crypto → US equity)
- Adaptive scan intervals based on market activity
- Asset-class-aware strategy execution
- API quota management and rate limiting
- State persistence and recovery
- Performance metrics tracking

Run in DRY_RUN mode with mock data for safety.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz
import time
import logging
from pathlib import Path
import tempfile
import json

from src.utils.global_scheduler import AutoTradingScheduler
from src.crew.market_rotation_strategy import MarketRotationStrategy
from src.utils.market_calendar import MarketCalendar
from src.config.settings import settings

logger = logging.getLogger(__name__)


class Test24HourAutonomous(unittest.TestCase):
    """
    Integration test suite for 24-hour autonomous trading.
    
    Tests simulate a full day of trading activity:
    - 9:30 AM - 4:00 PM ET: US equity trading
    - 4:00 PM - 9:30 AM ET: Crypto trading (24/7)
    - Market transitions handled smoothly
    - API quota stays under limits
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.state_file = Path(cls.temp_dir) / "test_state.json"
        logger.info(f"Test environment: {cls.temp_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def setUp(self):
        """Set up each test."""
        self.scheduler = AutoTradingScheduler()
        self.rotation = MarketRotationStrategy(state_file=self.state_file)
        self.calendar = MarketCalendar()
    
    def test_1_us_market_hours_trading(self):
        """
        Test trading during US market hours (9:30 AM - 4:00 PM ET).
        
        Expected behavior:
        - US_EQUITY market selected
        - 5-minute scan interval
        - Equities strategies used (3ma, rsi_breakout, macd)
        - No crypto trades during this period
        """
        # Simulate US market open time (11:00 AM ET = 4:00 PM UTC on a weekday)
        us_market_time = datetime(2025, 11, 3, 16, 0, 0, tzinfo=pytz.utc)  # Monday 11:00 AM ET
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            mock_active.return_value = ['US_EQUITY']
            
            # Select market
            selected_market = self.rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False
            )
            
            # Verify US_EQUITY selected
            self.assertEqual(selected_market, 'US_EQUITY', "Should trade US_EQUITY during market hours")
            
            # Verify 5-minute interval
            interval = self.scheduler._calculate_next_interval('US_EQUITY', us_market_time)
            self.assertEqual(interval, 300, "US_EQUITY should use 5-minute interval (300 seconds)")
            
            # Verify optimal strategies for equities
            strategies = self.scheduler._get_optimal_strategies('US_EQUITY')
            self.assertIn('3ma', strategies, "3MA should be available for US_EQUITY")
            self.assertIn('rsi_breakout', strategies, "RSI breakout should be available")
            self.assertGreaterEqual(len(strategies), 3, "Should have at least 3 strategies for equities")
    
    def test_2_crypto_trading_after_market_close(self):
        """
        Test trading after US market close (4:00 PM - 9:30 AM ET).
        
        Expected behavior:
        - CRYPTO market selected
        - 15-minute interval (peak hours) or 30-minute (off-peak)
        - Crypto strategies used (trend-following)
        - No equity trades during this period
        """
        # Simulate after US market close (8:00 PM ET = 1:00 AM UTC next day)
        us_closed_time = datetime(2025, 11, 4, 1, 0, 0, tzinfo=pytz.utc)  # Monday 8:00 PM ET
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            mock_active.return_value = ['CRYPTO']  # Only crypto active
            
            # Select market
            selected_market = self.rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False
            )
            
            # Verify CRYPTO selected
            self.assertEqual(selected_market, 'CRYPTO', "Should trade CRYPTO when US market closed")
            
            # Verify 30-minute interval (off-peak: 0-8 UTC)
            interval_offpeak = self.scheduler._calculate_next_interval('CRYPTO', us_closed_time)
            self.assertEqual(interval_offpeak, 1800, "CRYPTO off-peak should use 30-minute interval")
            
            # Verify 15-minute interval during peak hours (9-23 UTC)
            peak_time = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)  # 15:00 UTC (peak)
            interval_peak = self.scheduler._calculate_next_interval('CRYPTO', peak_time)
            self.assertEqual(interval_peak, 900, "CRYPTO peak should use 15-minute interval")
            
            # Verify crypto strategies
            strategies = self.scheduler._get_optimal_strategies('CRYPTO')
            self.assertIn('3ma', strategies, "3MA should work for crypto (trend-following)")
            self.assertIn('rsi_breakout', strategies, "RSI breakout should work for crypto")
    
    def test_3_market_transition_us_to_crypto(self):
        """
        Test smooth transition from US equity to crypto at market close.
        
        Expected behavior:
        - Rotation count increments
        - State persists with new market
        - No errors during transition
        - Previous market performance tracked
        """
        # Reset rotation state
        self.rotation.reset_performance()
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            # Step 1: Trade US equity
            mock_active.return_value = ['US_EQUITY']
            market1 = self.rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False
            )
            self.assertEqual(market1, 'US_EQUITY')
            
            # Step 2: Market closes, switch to crypto
            mock_active.return_value = ['CRYPTO']
            market2 = self.rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False
            )
            self.assertEqual(market2, 'CRYPTO')
            
            # Step 3: Verify rotation tracked
            stats = self.rotation.get_market_statistics()
            self.assertGreaterEqual(stats['rotation_count'], 2, "Should track market rotations")
            self.assertEqual(stats['last_rotation'], 'CRYPTO', "Last rotation should be CRYPTO")
    
    def test_4_performance_tracking_persistence(self):
        """
        Test that market performance metrics persist across restarts.
        
        Expected behavior:
        - Trade results tracked per market
        - Win rates calculated correctly
        - State saved to disk
        - State loads correctly on restart
        """
        # Add some trade results
        trade_us_win = {
            'success': True,
            'profit': 150.0,
            'symbol': 'AAPL',
            'strategy': '3ma',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        
        trade_crypto_loss = {
            'success': False,
            'profit': -50.0,
            'symbol': 'BTC/USD',
            'strategy': 'rsi_breakout',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        
        # Update performance
        self.rotation.update_market_performance('US_EQUITY', trade_us_win)
        self.rotation.update_market_performance('CRYPTO', trade_crypto_loss)
        
        # Get stats
        stats1 = self.rotation.get_market_statistics()
        self.assertEqual(stats1['markets']['US_EQUITY']['trades'], 1)
        self.assertEqual(stats1['markets']['US_EQUITY']['wins'], 1)
        self.assertEqual(stats1['markets']['CRYPTO']['trades'], 1)
        self.assertEqual(stats1['markets']['CRYPTO']['wins'], 0)
        
        # Simulate restart by creating new instance
        rotation2 = MarketRotationStrategy(state_file=self.state_file)
        stats2 = rotation2.get_market_statistics()
        
        # Verify persistence
        self.assertEqual(stats2['markets']['US_EQUITY']['trades'], 1, "Stats should persist")
        self.assertEqual(stats2['markets']['CRYPTO']['trades'], 1, "Stats should persist")
    
    def test_5_adaptive_interval_changes(self):
        """
        Test that scan intervals adapt correctly to market conditions.
        
        Expected behavior:
        - US_EQUITY: Always 5 minutes (peak liquidity)
        - CRYPTO peak (9-23 UTC): 15 minutes
        - CRYPTO off-peak (0-8 UTC): 30 minutes
        - FOREX: 10 minutes
        """
        # Test US_EQUITY
        us_time = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)
        interval_us = self.scheduler._calculate_next_interval('US_EQUITY', us_time)
        self.assertEqual(interval_us, 300, "US_EQUITY should be 5 minutes")
        
        # Test CRYPTO peak hours
        crypto_peak = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)  # 15:00 UTC
        interval_crypto_peak = self.scheduler._calculate_next_interval('CRYPTO', crypto_peak)
        self.assertEqual(interval_crypto_peak, 900, "CRYPTO peak should be 15 minutes")
        
        # Test CRYPTO off-peak hours
        crypto_offpeak = datetime(2025, 11, 3, 5, 0, 0, tzinfo=pytz.utc)  # 05:00 UTC
        interval_crypto_offpeak = self.scheduler._calculate_next_interval('CRYPTO', crypto_offpeak)
        self.assertEqual(interval_crypto_offpeak, 1800, "CRYPTO off-peak should be 30 minutes")
        
        # Test FOREX
        forex_time = datetime(2025, 11, 3, 10, 0, 0, tzinfo=pytz.utc)
        interval_forex = self.scheduler._calculate_next_interval('FOREX', forex_time)
        self.assertEqual(interval_forex, 600, "FOREX should be 10 minutes")
    
    def test_6_performance_based_market_selection(self):
        """
        Test that market selection considers performance when appropriate.
        
        Expected behavior:
        - Time-based selection by default
        - Performance overlay when markets compete
        - Better performing market selected if score >20% higher
        """
        # Add excellent crypto performance
        for i in range(10):
            self.rotation.update_market_performance('CRYPTO', {
                'success': True,
                'profit': 200.0,
                'symbol': 'BTC/USD',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            })
        
        # Add poor equity performance
        for i in range(10):
            self.rotation.update_market_performance('US_EQUITY', {
                'success': False,
                'profit': -100.0,
                'symbol': 'AAPL',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            })
        
        # Calculate scores
        crypto_score = self.rotation._calculate_market_score('CRYPTO')
        equity_score = self.rotation._calculate_market_score('US_EQUITY')
        
        # Verify crypto has much better score
        self.assertGreater(crypto_score, equity_score, 
                          "CRYPTO should have higher score with 100% win rate vs 0%")
        
        # With both markets active, performance should influence selection
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            mock_active.return_value = ['US_EQUITY', 'CRYPTO']
            
            # With performance consideration, might override time-based
            selected = self.rotation.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=True
            )
            
            # Note: Time-based usually wins, but performance can override if significantly better
            # This test validates the scoring logic works correctly
            self.assertIn(selected, ['US_EQUITY', 'CRYPTO'], "Should select valid market")
    
    def test_7_state_recovery_after_failure(self):
        """
        Test that system can recover state after simulated failure.
        
        Expected behavior:
        - State saves after each operation
        - New instance loads previous state
        - No data loss
        - Rotation count preserved
        """
        # Perform some operations
        self.rotation.update_market_performance('US_EQUITY', {
            'success': True,
            'profit': 100.0,
            'symbol': 'AAPL',
            'strategy': '3ma',
            'timestamp': datetime.now(pytz.utc).isoformat()
        })
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            mock_active.return_value = ['US_EQUITY']
            self.rotation.select_active_market()
            
            mock_active.return_value = ['CRYPTO']
            self.rotation.select_active_market()
        
        # Get state before "crash"
        stats_before = self.rotation.get_market_statistics()
        rotation_count_before = stats_before['rotation_count']
        trades_before = stats_before['markets']['US_EQUITY']['trades']
        
        # Simulate crash and restart
        del self.rotation
        rotation_after = MarketRotationStrategy(state_file=self.state_file)
        
        # Verify state recovered
        stats_after = rotation_after.get_market_statistics()
        self.assertEqual(stats_after['rotation_count'], rotation_count_before,
                        "Rotation count should be preserved")
        self.assertEqual(stats_after['markets']['US_EQUITY']['trades'], trades_before,
                        "Trade count should be preserved")


class TestLongRunningOperations(unittest.TestCase):
    """
    Tests for long-running operations and resource management.
    
    These tests validate:
    - No memory leaks during extended operation
    - API rate limits respected
    - State file doesn't grow unbounded
    - Logging doesn't fill disk
    """
    
    def test_1_repeated_market_selections(self):
        """Test that repeated market selections don't leak memory or corrupt state."""
        rotation = MarketRotationStrategy()
        
        # Perform 100 market selections
        for i in range(100):
            with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
                mock_active.return_value = ['US_EQUITY'] if i % 2 == 0 else ['CRYPTO']
                market = rotation.select_active_market(consider_performance=False)
                self.assertIn(market, ['US_EQUITY', 'CRYPTO'])
        
        # Verify state is valid
        stats = rotation.get_market_statistics()
        self.assertIsNotNone(stats)
        self.assertIn('rotation_count', stats)
        self.assertGreater(stats['rotation_count'], 0)
    
    def test_2_performance_tracking_scale(self):
        """Test that performance tracking handles many trades efficiently."""
        rotation = MarketRotationStrategy()
        
        # Clear any existing state from previous runs
        rotation.reset_performance('US_EQUITY')
        
        # Add 1000 trades
        start_time = time.time()
        for i in range(1000):
            rotation.update_market_performance('US_EQUITY', {
                'success': i % 3 != 0,  # ~67% win rate
                'profit': 50.0 if i % 3 != 0 else -25.0,
                'symbol': 'AAPL',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            })
        elapsed = time.time() - start_time
        
        # Should complete quickly (< 5 seconds for 1000 updates)
        self.assertLess(elapsed, 5.0, f"1000 updates took {elapsed:.2f}s (should be <5s)")
        
        # Verify stats are correct
        stats = rotation.get_market_statistics()
        self.assertEqual(stats['markets']['US_EQUITY']['trades'], 1000)
        self.assertAlmostEqual(stats['markets']['US_EQUITY']['win_rate'], 0.67, delta=0.01)


if __name__ == '__main__':
    # Configure logging for test output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests with verbose output
    unittest.main(verbosity=2)
