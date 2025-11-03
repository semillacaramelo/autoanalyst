"""
Additional Tests for Global Scheduler - Autonomous Trading Workflow

This module tests the autonomous 24/7 trading workflow including
emergency position closing and full cycle execution.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import pytz

from src.utils.global_scheduler import AutoTradingScheduler


class TestGlobalSchedulerEmergencyFunctions(unittest.TestCase):
    """Test emergency and critical functions of the scheduler."""

    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = AutoTradingScheduler()

    @patch("src.utils.global_scheduler.alpaca_manager")
    def test_emergency_close_positions_with_long_positions(self, mock_alpaca):
        """Test emergency close with long positions."""
        # Mock positions
        mock_alpaca.get_positions.return_value = [
            {"symbol": "SPY", "qty": "10", "side": "long"},
            {"symbol": "QQQ", "qty": "5", "side": "long"},
        ]
        mock_alpaca.place_market_order.return_value = {"success": True}

        # Execute
        self.scheduler._emergency_close_positions()

        # Verify positions were fetched
        mock_alpaca.get_positions.assert_called_once()

        # Verify market orders were placed to close (sell for long positions)
        self.assertEqual(mock_alpaca.place_market_order.call_count, 2)
        mock_alpaca.place_market_order.assert_any_call("SPY", "10", "SELL")
        mock_alpaca.place_market_order.assert_any_call("QQQ", "5", "SELL")

    @patch("src.utils.global_scheduler.alpaca_manager")
    def test_emergency_close_positions_with_short_positions(self, mock_alpaca):
        """Test emergency close with short positions."""
        # Mock positions
        mock_alpaca.get_positions.return_value = [
            {"symbol": "TSLA", "qty": "3", "side": "short"}
        ]
        mock_alpaca.place_market_order.return_value = {"success": True}

        # Execute
        self.scheduler._emergency_close_positions()

        # Verify market order was placed to close (buy for short positions)
        mock_alpaca.place_market_order.assert_called_once_with("TSLA", "3", "BUY")

    @patch("src.utils.global_scheduler.alpaca_manager")
    def test_emergency_close_positions_no_positions(self, mock_alpaca):
        """Test emergency close with no open positions."""
        # Mock no positions
        mock_alpaca.get_positions.return_value = []

        # Execute - should not raise exception
        self.scheduler._emergency_close_positions()

        # Verify positions were fetched but no orders placed
        mock_alpaca.get_positions.assert_called_once()
        mock_alpaca.place_market_order.assert_not_called()

    @patch("src.utils.global_scheduler.alpaca_manager")
    def test_emergency_close_positions_error_handling(self, mock_alpaca):
        """Test emergency close with API error."""
        # Mock API error
        mock_alpaca.get_positions.side_effect = Exception("API connection failed")

        # Execute - should not raise exception, just log error
        self.scheduler._emergency_close_positions()

        # Verify error was handled gracefully
        mock_alpaca.get_positions.assert_called_once()

    @patch("src.utils.global_scheduler.settings")
    def test_calculate_next_interval_fallback(self, mock_settings):
        """Test interval calculation with unknown market (fallback)."""
        mock_settings.scan_interval_minutes = 20

        current_time = datetime(2025, 11, 3, 12, 0, 0, tzinfo=pytz.utc)

        interval = self.scheduler._calculate_next_interval(
            "UNKNOWN_MARKET", current_time
        )

        # Should use fallback from settings (20 minutes = 1200 seconds)
        self.assertEqual(interval, 1200)


class TestGlobalSchedulerRunForever(unittest.TestCase):
    """Test the main run_forever loop."""

    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = AutoTradingScheduler()

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.alpaca_manager")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    @patch("src.utils.global_scheduler.MarketCalendar")
    @patch("src.utils.global_scheduler.trading_orchestrator")
    @patch("src.utils.global_scheduler.StateManager")
    def test_run_forever_single_iteration(
        self,
        mock_state_mgr_class,
        mock_orchestrator,
        mock_calendar_class,
        mock_rotation,
        mock_alpaca,
        mock_sleep,
    ):
        """Test a single iteration of run_forever loop."""
        # Mock market rotation to select US_EQUITY
        mock_rotation.select_active_market.return_value = "US_EQUITY"
        mock_rotation.get_market_statistics.return_value = {
            "rotation_count": 5,
            "last_rotation": "2025-11-03 10:00:00",
        }

        # Mock market calendar instance
        mock_calendar_inst = Mock()
        mock_calendar_inst.get_active_markets.return_value = ["US_EQUITY"]
        mock_calendar_class.return_value = mock_calendar_inst

        # Mock state manager instance
        mock_state_inst = Mock()
        mock_state_inst.load_state.return_value = {}
        mock_state_inst.save_state.return_value = None
        mock_state_mgr_class.return_value = mock_state_inst

        # Mock orchestrator
        mock_orchestrator.run_cycle.return_value = None

        # Mock alpaca positions
        mock_alpaca.get_positions.return_value = [
            {"symbol": "SPY", "qty": "10", "unrealized_pl": 50.0}
        ]

        # Mock sleep to break loop after first iteration
        def sleep_side_effect(duration):
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Create new scheduler with mocked dependencies
        scheduler = AutoTradingScheduler()

        # Execute (will run one iteration then exit via KeyboardInterrupt)
        scheduler.run_forever()

        # Verify key methods were called
        mock_rotation.select_active_market.assert_called_once()
        mock_calendar_inst.get_active_markets.assert_called_once()
        mock_orchestrator.run_cycle.assert_called_once()
        mock_state_inst.save_state.assert_called_once()

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_run_forever_market_closed(self, mock_rotation, mock_sleep):
        """Test run_forever when selected market is closed."""
        # Mock market rotation
        mock_rotation.select_active_market.return_value = "US_EQUITY"

        # Mock market calendar on instance
        self.scheduler.market_calendar.get_active_markets = Mock(return_value=[])

        # Mock next market open time
        next_open_time = datetime(2025, 11, 4, 14, 30, 0, tzinfo=pytz.utc)
        self.scheduler.market_calendar.next_market_open = Mock(
            return_value=next_open_time
        )

        # Mock sleep to break loop after first sleep call
        sleep_calls = []

        def sleep_side_effect(duration):
            sleep_calls.append(duration)
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute (will sleep then exit via KeyboardInterrupt)
        self.scheduler.run_forever()

        # Verify sleep was called (market closed, waiting for next open)
        self.assertEqual(len(sleep_calls), 1)
        # Sleep duration should be capped at 3600 seconds (1 hour)
        self.assertLessEqual(sleep_calls[0], 3600)

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.settings")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_run_forever_error_with_auto_close(
        self, mock_rotation, mock_settings, mock_sleep
    ):
        """Test run_forever with critical error and auto_close_on_error enabled."""
        # Enable auto close on error
        mock_settings.auto_close_on_error = True

        # Mock market rotation
        mock_rotation.select_active_market.return_value = "US_EQUITY"

        # Mock market calendar on instance
        self.scheduler.market_calendar.get_active_markets = Mock(
            return_value=["US_EQUITY"]
        )

        # Mock orchestrator to raise critical error
        self.scheduler.orchestrator.run_cycle = Mock(
            side_effect=Exception("Critical trading error")
        )

        # Mock emergency close
        self.scheduler._emergency_close_positions = Mock()

        # Mock sleep to break loop after error handling
        def sleep_side_effect(duration):
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute
        self.scheduler.run_forever()

        # Verify emergency close was called due to critical error
        self.scheduler._emergency_close_positions.assert_called_once()

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_run_forever_market_closed_no_schedule(self, mock_rotation, mock_sleep):
        """Test run_forever when market is closed and no schedule available."""
        # Mock market rotation
        mock_rotation.select_active_market.return_value = "CRYPTO"

        # Mock market calendar on instance
        self.scheduler.market_calendar.get_active_markets = Mock(return_value=[])
        self.scheduler.market_calendar.next_market_open = Mock(return_value=None)

        # Mock sleep to break loop
        sleep_calls = []

        def sleep_side_effect(duration):
            sleep_calls.append(duration)
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute
        self.scheduler.run_forever()

        # Verify sleep was called with fallback duration (1 hour)
        self.assertEqual(len(sleep_calls), 1)
        self.assertEqual(sleep_calls[0], 3600)

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_run_forever_unexpected_error_recovery(self, mock_rotation, mock_sleep):
        """Test run_forever recovers from unexpected errors."""
        # Mock market rotation to raise error
        mock_rotation.select_active_market.side_effect = Exception("Unexpected error")

        # Mock sleep to break loop after error recovery sleep
        def sleep_side_effect(duration):
            if duration == 300:  # 5 minute error recovery sleep
                raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute
        self.scheduler.run_forever()

        # Verify sleep was called with 5 minute error recovery duration
        mock_sleep.assert_called_once_with(300)


class TestGlobalSchedulerStateManagement(unittest.TestCase):
    """Test state management in the scheduler."""

    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = AutoTradingScheduler()

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.alpaca_manager")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_state_tracking_after_cycle(self, mock_rotation, mock_alpaca, mock_sleep):
        """Test that state is properly tracked after each cycle."""
        # Mock dependencies
        mock_rotation.select_active_market.return_value = "CRYPTO"
        mock_rotation.get_market_statistics.return_value = {
            "rotation_count": 10,
            "last_rotation": "2025-11-03 12:00:00",
        }

        # Mock market calendar and orchestrator on instance
        self.scheduler.market_calendar.get_active_markets = Mock(
            return_value=["CRYPTO"]
        )
        self.scheduler.orchestrator.run_cycle = Mock(return_value=None)

        # Mock positions with P&L
        mock_alpaca.get_positions.return_value = [
            {"symbol": "BTC/USD", "qty": "0.1", "unrealized_pl": 100.0},
            {"symbol": "ETH/USD", "qty": "1.5", "unrealized_pl": -20.0},
        ]

        # Mock state manager
        saved_states = []

        def save_state_side_effect(state):
            saved_states.append(state.copy())

        self.scheduler.state_manager.save_state = Mock(
            side_effect=save_state_side_effect
        )

        # Mock sleep to break loop
        def sleep_side_effect(duration):
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute
        self.scheduler.run_forever()

        # Verify state was saved
        self.assertEqual(len(saved_states), 1)
        saved_state = saved_states[0]

        # Verify state contains required fields
        self.assertIn("last_run_timestamp", saved_state)
        self.assertIn("active_market", saved_state)
        self.assertEqual(saved_state["active_market"], "CRYPTO")
        self.assertIn("strategies_used", saved_state)
        self.assertIn("positions", saved_state)
        self.assertIn("daily_pnl", saved_state)

        # Verify daily P&L calculation (100 - 20 = 80)
        self.assertEqual(saved_state["daily_pnl"], 80.0)

    @patch("src.utils.global_scheduler.time.sleep")
    @patch("src.utils.global_scheduler.alpaca_manager")
    @patch("src.utils.global_scheduler.market_rotation_strategy")
    def test_state_update_handles_position_fetch_error(
        self, mock_rotation, mock_alpaca, mock_sleep
    ):
        """Test that state update handles position fetch errors gracefully."""
        # Mock dependencies
        mock_rotation.select_active_market.return_value = "US_EQUITY"
        mock_rotation.get_market_statistics.return_value = {
            "rotation_count": 1,
            "last_rotation": None,
        }

        # Mock market calendar and orchestrator on instance
        self.scheduler.market_calendar.get_active_markets = Mock(
            return_value=["US_EQUITY"]
        )
        self.scheduler.orchestrator.run_cycle = Mock(return_value=None)

        # Mock positions fetch to raise error
        mock_alpaca.get_positions.side_effect = Exception("API error")

        # Mock state manager
        saved_states = []

        def save_state_side_effect(state):
            saved_states.append(state.copy())

        self.scheduler.state_manager.save_state = Mock(
            side_effect=save_state_side_effect
        )

        # Mock sleep to break loop
        def sleep_side_effect(duration):
            raise KeyboardInterrupt()

        mock_sleep.side_effect = sleep_side_effect

        # Execute
        self.scheduler.run_forever()

        # Verify state was still saved (without position data)
        self.assertEqual(len(saved_states), 1)
        saved_state = saved_states[0]

        # Verify basic state fields still present
        self.assertIn("last_run_timestamp", saved_state)
        self.assertIn("active_market", saved_state)


if __name__ == "__main__":
    unittest.main()
