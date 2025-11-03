"""
Tests for global_scheduler.py - Autonomous 24/7 trading scheduler.

This module tests the intelligent market rotation and adaptive interval scheduling.
"""

import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import pytz
import time

from src.utils.global_scheduler import AutoTradingScheduler


class TestAutoTradingSchedulerInit(unittest.TestCase):
    """Test scheduler initialization."""
    
    @patch('src.utils.global_scheduler.StateManager')
    @patch('src.utils.global_scheduler.MarketCalendar')
    @patch('src.utils.global_scheduler.trading_orchestrator')
    @patch('src.utils.global_scheduler.market_rotation_strategy')
    def test_initialization(self, mock_rotation, mock_orchestrator, mock_calendar, mock_state_mgr):
        """Test that scheduler initializes correctly."""
        mock_state_mgr_instance = MagicMock()
        mock_state_mgr.return_value = mock_state_mgr_instance
        mock_state_mgr_instance.load_state.return_value = {'test': 'state'}
        
        scheduler = AutoTradingScheduler()
        
        self.assertIsNotNone(scheduler.market_calendar)
        self.assertIsNotNone(scheduler.state_manager)
        self.assertIsNotNone(scheduler.orchestrator)
        self.assertIsNotNone(scheduler.market_rotation)
        self.assertEqual(scheduler.state, {'test': 'state'})
    
    @patch('src.utils.global_scheduler.StateManager')
    @patch('src.utils.global_scheduler.MarketCalendar')
    @patch('src.utils.global_scheduler.trading_orchestrator')
    @patch('src.utils.global_scheduler.market_rotation_strategy')
    def test_interval_configuration(self, mock_rotation, mock_orchestrator, mock_calendar, mock_state_mgr):
        """Test that adaptive intervals are configured correctly."""
        mock_state_mgr_instance = MagicMock()
        mock_state_mgr.return_value = mock_state_mgr_instance
        mock_state_mgr_instance.load_state.return_value = {}
        
        scheduler = AutoTradingScheduler()
        
        self.assertEqual(scheduler.intervals['US_EQUITY'], 5)
        self.assertEqual(scheduler.intervals['CRYPTO_PEAK'], 15)
        self.assertEqual(scheduler.intervals['CRYPTO_OFFPEAK'], 30)
        self.assertEqual(scheduler.intervals['FOREX'], 10)


class TestCalculateNextInterval(unittest.TestCase):
    """Test adaptive interval calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('src.utils.global_scheduler.StateManager'), \
             patch('src.utils.global_scheduler.MarketCalendar'), \
             patch('src.utils.global_scheduler.trading_orchestrator'), \
             patch('src.utils.global_scheduler.market_rotation_strategy'):
            self.scheduler = AutoTradingScheduler()
    
    def test_us_equity_interval(self):
        """Test interval for US_EQUITY market."""
        current_time = datetime(2025, 1, 15, 14, 30, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('US_EQUITY', current_time)
        
        # US_EQUITY should be 5 minutes = 300 seconds
        self.assertEqual(interval, 300)
    
    def test_crypto_peak_hours(self):
        """Test interval for CRYPTO during peak hours (9-23 UTC)."""
        # 15:00 UTC is peak time
        current_time = datetime(2025, 1, 15, 15, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', current_time)
        
        # Peak crypto: 15 minutes = 900 seconds
        self.assertEqual(interval, 900)
    
    def test_crypto_offpeak_hours(self):
        """Test interval for CRYPTO during off-peak hours (0-8 UTC)."""
        # 3:00 UTC is off-peak time
        current_time = datetime(2025, 1, 15, 3, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', current_time)
        
        # Off-peak crypto: 30 minutes = 1800 seconds
        self.assertEqual(interval, 1800)
    
    def test_crypto_peak_boundary_start(self):
        """Test interval at peak hours start boundary (9:00 UTC)."""
        current_time = datetime(2025, 1, 15, 9, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', current_time)
        
        # 9:00 is start of peak, should be 15 minutes
        self.assertEqual(interval, 900)
    
    def test_crypto_peak_boundary_end(self):
        """Test interval just before peak hours end (22:59 UTC)."""
        current_time = datetime(2025, 1, 15, 22, 59, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', current_time)
        
        # Still peak hours
        self.assertEqual(interval, 900)
    
    def test_crypto_after_peak(self):
        """Test interval just after peak hours end (23:00 UTC)."""
        current_time = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('CRYPTO', current_time)
        
        # Off-peak after 23:00
        self.assertEqual(interval, 1800)
    
    def test_forex_interval(self):
        """Test interval for FOREX market."""
        current_time = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('FOREX', current_time)
        
        # Forex: 10 minutes = 600 seconds
        self.assertEqual(interval, 600)
    
    @patch('src.utils.global_scheduler.settings')
    def test_unknown_market_fallback(self, mock_settings):
        """Test fallback for unknown market type."""
        mock_settings.scan_interval_minutes = 20
        current_time = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        interval = self.scheduler._calculate_next_interval('UNKNOWN_MARKET', current_time)
        
        # Should fall back to settings default
        self.assertEqual(interval, 1200)  # 20 minutes


class TestGetOptimalStrategies(unittest.TestCase):
    """Test strategy selection for different asset classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('src.utils.global_scheduler.StateManager'), \
             patch('src.utils.global_scheduler.MarketCalendar'), \
             patch('src.utils.global_scheduler.trading_orchestrator'), \
             patch('src.utils.global_scheduler.market_rotation_strategy'):
            self.scheduler = AutoTradingScheduler()
    
    def test_us_equity_strategies(self):
        """Test optimal strategies for US_EQUITY."""
        strategies = self.scheduler._get_optimal_strategies('US_EQUITY')
        
        self.assertEqual(strategies, ['3ma', 'rsi_breakout', 'macd'])
    
    def test_crypto_strategies(self):
        """Test optimal strategies for CRYPTO."""
        strategies = self.scheduler._get_optimal_strategies('CRYPTO')
        
        self.assertEqual(strategies, ['3ma', 'rsi_breakout'])
    
    def test_forex_strategies(self):
        """Test optimal strategies for FOREX."""
        strategies = self.scheduler._get_optimal_strategies('FOREX')
        
        self.assertEqual(strategies, ['macd', 'bollinger'])
    
    def test_unknown_market_fallback(self):
        """Test fallback for unknown market type."""
        strategies = self.scheduler._get_optimal_strategies('UNKNOWN')
        
        # Should return default
        self.assertEqual(strategies, ['3ma'])


class TestEmergencyClosePositions(unittest.TestCase):
    """Test emergency position closing."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('src.utils.global_scheduler.StateManager'), \
             patch('src.utils.global_scheduler.MarketCalendar'), \
             patch('src.utils.global_scheduler.trading_orchestrator'), \
             patch('src.utils.global_scheduler.market_rotation_strategy'):
            self.scheduler = AutoTradingScheduler()
    
    @patch('src.utils.global_scheduler.alpaca_manager')
    def test_close_long_positions(self, mock_alpaca):
        """Test closing long positions in emergency."""
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'SPY', 'qty': '10', 'side': 'long'},
            {'symbol': 'QQQ', 'qty': '5', 'side': 'long'}
        ]
        
        self.scheduler._emergency_close_positions()
        
        # Should place SELL orders for long positions
        calls = mock_alpaca.place_market_order.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], call('SPY', '10', 'SELL'))
        self.assertEqual(calls[1], call('QQQ', '5', 'SELL'))
    
    @patch('src.utils.global_scheduler.alpaca_manager')
    def test_close_short_positions(self, mock_alpaca):
        """Test closing short positions in emergency."""
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'TSLA', 'qty': '10', 'side': 'short'}
        ]
        
        self.scheduler._emergency_close_positions()
        
        # Should place BUY order for short position
        mock_alpaca.place_market_order.assert_called_once_with('TSLA', '10', 'BUY')
    
    @patch('src.utils.global_scheduler.alpaca_manager')
    def test_no_positions(self, mock_alpaca):
        """Test when there are no open positions."""
        mock_alpaca.get_positions.return_value = []
        
        # Should not raise error
        self.scheduler._emergency_close_positions()
        
        # No orders should be placed
        mock_alpaca.place_market_order.assert_not_called()
    
    @patch('src.utils.global_scheduler.alpaca_manager')
    def test_api_failure(self, mock_alpaca):
        """Test handling of API failure during emergency close."""
        mock_alpaca.get_positions.side_effect = Exception("API Error")
        
        # Should not raise exception
        self.scheduler._emergency_close_positions()


class TestRunForeverLoop(unittest.TestCase):
    """Test the main run_forever loop."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('src.utils.global_scheduler.StateManager'), \
             patch('src.utils.global_scheduler.MarketCalendar'), \
             patch('src.utils.global_scheduler.trading_orchestrator'), \
             patch('src.utils.global_scheduler.market_rotation_strategy'):
            self.scheduler = AutoTradingScheduler()
    
    @patch('src.utils.global_scheduler.time.sleep')
    @patch('src.utils.global_scheduler.alpaca_manager')
    @patch('src.utils.global_scheduler.settings')
    def test_successful_cycle_execution(self, mock_settings, mock_alpaca, mock_sleep):
        """Test successful execution of one trading cycle."""
        mock_settings.target_markets = ['US_EQUITY']
        mock_settings.auto_close_on_error = False
        
        # Mock market rotation
        self.scheduler.market_rotation.select_active_market.return_value = 'US_EQUITY'
        self.scheduler.market_rotation.get_market_statistics.return_value = {
            'rotation_count': 5,
            'last_rotation': '2025-01-15 10:00:00'
        }
        
        # Mock market calendar
        self.scheduler.market_calendar.get_active_markets.return_value = ['US_EQUITY']
        
        # Mock orchestrator
        self.scheduler.orchestrator.run_cycle = MagicMock()
        
        # Mock positions
        mock_alpaca.get_positions.return_value = []
        
        # Mock state manager
        self.scheduler.state_manager.save_state = MagicMock()
        
        # Run one iteration then stop
        iteration_count = [0]
        original_sleep = mock_sleep.side_effect
        
        def sleep_and_stop(*args):
            iteration_count[0] += 1
            if iteration_count[0] >= 1:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = sleep_and_stop
        
        # Run scheduler
        self.scheduler.run_forever()
        
        # Verify one cycle executed
        self.scheduler.orchestrator.run_cycle.assert_called_once()
        self.scheduler.state_manager.save_state.assert_called_once()
    
    @patch('src.utils.global_scheduler.time.sleep')
    @patch('src.utils.global_scheduler.settings')
    def test_market_closed_sleep(self, mock_settings, mock_sleep):
        """Test scheduler behavior when market is closed."""
        mock_settings.target_markets = ['US_EQUITY']
        
        # Mock market rotation
        self.scheduler.market_rotation.select_active_market.return_value = 'US_EQUITY'
        
        # Mock market closed
        self.scheduler.market_calendar.get_active_markets.return_value = []
        next_open = datetime.now(pytz.utc) + timedelta(hours=2)
        self.scheduler.market_calendar.next_market_open.return_value = next_open
        
        # Run one iteration then stop
        iteration_count = [0]
        
        def sleep_and_stop(*args):
            iteration_count[0] += 1
            if iteration_count[0] >= 1:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = sleep_and_stop
        
        # Run scheduler
        self.scheduler.run_forever()
        
        # Should have slept (market closed)
        self.assertTrue(mock_sleep.called)
    
    @patch('src.utils.global_scheduler.time.sleep')
    @patch('src.utils.global_scheduler.settings')
    def test_error_recovery(self, mock_settings, mock_sleep):
        """Test that scheduler recovers from errors."""
        mock_settings.target_markets = ['US_EQUITY']
        mock_settings.auto_close_on_error = False
        
        # Mock market rotation to raise error first, then succeed
        call_count = [0]
        
        def market_selection_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Test error")
            return 'US_EQUITY'
        
        self.scheduler.market_rotation.select_active_market.side_effect = market_selection_effect
        
        # Stop after 2 iterations
        iteration_count = [0]
        
        def sleep_and_stop(*args):
            iteration_count[0] += 1
            if iteration_count[0] >= 2:
                raise KeyboardInterrupt()
        
        mock_sleep.side_effect = sleep_and_stop
        
        # Run scheduler
        self.scheduler.run_forever()
        
        # Should have called sleep twice (once for error, once for KeyboardInterrupt)
        self.assertGreaterEqual(mock_sleep.call_count, 2)


if __name__ == '__main__':
    unittest.main()
