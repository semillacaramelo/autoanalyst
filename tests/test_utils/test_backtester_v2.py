"""
Tests for backtester_v2.py - Backtesting engine for strategy validation.

This module tests the backtesting functionality that validates
trading strategies against historical data.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import numpy as np
from datetime import datetime

from src.utils.backtester_v2 import BacktesterV2


class TestBacktesterV2Initialization(unittest.TestCase):
    """Test BacktesterV2 initialization."""
    
    def test_initialization_with_dates(self):
        """Test creating backtester with date range."""
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        
        self.assertEqual(backtester.start_date, '2024-01-01')
        self.assertEqual(backtester.end_date, '2024-06-30')
        self.assertEqual(backtester.risk_free_rate, 0.02)
    
    def test_initialization_with_custom_risk_free_rate(self):
        """Test backtester with custom risk-free rate."""
        backtester = BacktesterV2('2024-01-01', '2024-06-30', risk_free_rate=0.05)
        
        self.assertEqual(backtester.risk_free_rate, 0.05)


class TestAnnualizationFactor(unittest.TestCase):
    """Test annualization factor calculation for different timeframes."""
    
    def setUp(self):
        self.backtester = BacktesterV2('2024-01-01', '2024-06-30')
    
    def test_daily_timeframe(self):
        """Test annualization factor for daily data."""
        factor = self.backtester._get_annualization_factor('1Day')
        self.assertEqual(factor, 252)
        
        factor = self.backtester._get_annualization_factor('1d')
        self.assertEqual(factor, 252)
        
        factor = self.backtester._get_annualization_factor('1day')
        self.assertEqual(factor, 252)
    
    def test_hourly_timeframe(self):
        """Test annualization factor for hourly data."""
        factor = self.backtester._get_annualization_factor('1Hour')
        self.assertEqual(factor, 252 * 6.5)
        
        factor = self.backtester._get_annualization_factor('1h')
        self.assertEqual(factor, 252 * 6.5)
    
    def test_minute_timeframe(self):
        """Test annualization factor for minute data."""
        factor = self.backtester._get_annualization_factor('1Min')
        self.assertEqual(factor, 252 * 6.5 * 60)
        
        factor = self.backtester._get_annualization_factor('5m')
        self.assertEqual(factor, 252 * 6.5 * 60)
    
    def test_invalid_timeframe_returns_default(self):
        """Test that invalid timeframe returns default (252)."""
        factor = self.backtester._get_annualization_factor('invalid')
        self.assertEqual(factor, 252)
        
        factor = self.backtester._get_annualization_factor('')
        self.assertEqual(factor, 252)


class TestCalculatePerformance(unittest.TestCase):
    """Test performance metrics calculation."""
    
    def setUp(self):
        self.backtester = BacktesterV2('2024-01-01', '2024-06-30')
    
    def test_no_trades_returns_zero_metrics(self):
        """Test that no trades returns all zero metrics."""
        result = self.backtester.calculate_performance([], '1Day')
        
        self.assertEqual(result['trades'], 0)
        self.assertEqual(result['pnl'], 0)
        self.assertEqual(result['win_rate'], 0)
        self.assertEqual(result['sharpe_ratio'], 0)
        self.assertEqual(result['sortino_ratio'], 0)
        self.assertEqual(result['calmar_ratio'], 0)
        self.assertEqual(result['max_drawdown'], 0)
    
    def test_single_winning_trade(self):
        """Test performance with one winning trade."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 1.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 110.0, 'commission': 1.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        self.assertEqual(result['trades'], 1)
        self.assertEqual(result['pnl'], 8.0)  # 110 - 100 - 2 commissions
        self.assertEqual(result['win_rate'], 100.0)
        # Single trade has no variance, so Sharpe ratio is 0
        self.assertEqual(result['sharpe_ratio'], 0)
    
    def test_single_losing_trade(self):
        """Test performance with one losing trade."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 1.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 90.0, 'commission': 1.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        self.assertEqual(result['trades'], 1)
        self.assertEqual(result['pnl'], -12.0)  # 90 - 100 - 2
        self.assertEqual(result['win_rate'], 0.0)
        # Single trade has no variance, so Sharpe ratio is 0
        self.assertEqual(result['sharpe_ratio'], 0)
    
    def test_multiple_trades_mixed_results(self):
        """Test performance with multiple winning and losing trades."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 1.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 110.0, 'commission': 1.0},
            {'date': '2024-01-15', 'type': 'BUY', 'price': 110.0, 'commission': 1.0},
            {'date': '2024-01-20', 'type': 'SELL', 'price': 105.0, 'commission': 1.0},
            {'date': '2024-01-25', 'type': 'BUY', 'price': 105.0, 'commission': 1.0},
            {'date': '2024-01-30', 'type': 'SELL', 'price': 115.0, 'commission': 1.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        self.assertEqual(result['trades'], 3)
        # Trade 1: +8, Trade 2: -7, Trade 3: +8 = +9 total
        self.assertEqual(result['pnl'], 9.0)
        self.assertAlmostEqual(result['win_rate'], 66.67, places=1)  # 2 wins out of 3
    
    def test_open_position_warning(self):
        """Test handling of incomplete trade (open position)."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 1.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 110.0, 'commission': 1.0},
            {'date': '2024-01-15', 'type': 'BUY', 'price': 110.0, 'commission': 1.0},
            # Missing SELL - open position
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        # Should only count complete trades (open position gets logged but calculated)
        self.assertEqual(result['trades'], 1)
        self.assertEqual(result['pnl'], 8.0)  # Only the complete trade
        # Note: 'note' field only added when num_complete_trades == 0
        self.assertNotIn('note', result)
    
    def test_only_open_position_no_complete_trades(self):
        """Test with only a single BUY (no complete trades)."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 1.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        self.assertEqual(result['trades'], 0)
        self.assertEqual(result['pnl'], 0)
        self.assertIn('note', result)
    
    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation with losing trades."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 0.0},
            {'date': '2024-01-05', 'type': 'SELL', 'price': 110.0, 'commission': 0.0},  # +10
            {'date': '2024-01-10', 'type': 'BUY', 'price': 110.0, 'commission': 0.0},
            {'date': '2024-01-15', 'type': 'SELL', 'price': 95.0, 'commission': 0.0},   # -15
            {'date': '2024-01-20', 'type': 'BUY', 'price': 95.0, 'commission': 0.0},
            {'date': '2024-01-25', 'type': 'SELL', 'price': 115.0, 'commission': 0.0},  # +20
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        # Max drawdown should be negative (the -15 loss)
        self.assertLess(result['max_drawdown'], 0)
        self.assertEqual(result['trades'], 3)
    
    def test_sharpe_ratio_with_no_variance(self):
        """Test Sharpe ratio when all returns are identical."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 0.0},
            {'date': '2024-01-05', 'type': 'SELL', 'price': 105.0, 'commission': 0.0},
            {'date': '2024-01-10', 'type': 'BUY', 'price': 100.0, 'commission': 0.0},
            {'date': '2024-01-15', 'type': 'SELL', 'price': 105.0, 'commission': 0.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        # With no variance in returns, Sharpe should be 0
        self.assertEqual(result['sharpe_ratio'], 0)
    
    def test_sortino_ratio_with_no_downside(self):
        """Test Sortino ratio when there are no negative returns."""
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 0.0},
            {'date': '2024-01-05', 'type': 'SELL', 'price': 110.0, 'commission': 0.0},
            {'date': '2024-01-10', 'type': 'BUY', 'price': 110.0, 'commission': 0.0},
            {'date': '2024-01-15', 'type': 'SELL', 'price': 120.0, 'commission': 0.0},
        ]
        
        result = self.backtester.calculate_performance(trades, '1Day')
        
        # With no downside returns, Sortino should be 0
        self.assertEqual(result['sortino_ratio'], 0)


class TestBacktestRun(unittest.TestCase):
    """Test full backtest run with mocked data."""
    
    @patch('src.utils.backtester_v2.alpaca_manager')
    @patch('src.utils.backtester_v2.get_strategy')
    def test_run_with_no_data(self, mock_get_strategy, mock_alpaca):
        """Test backtest run when no historical data is available."""
        mock_alpaca.fetch_historical_bars.return_value = pd.DataFrame()
        
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        result = backtester.run('SPY', '3ma')
        
        # Should return zero metrics
        self.assertEqual(result['trades'], 0)
        self.assertEqual(result['pnl'], 0)
    
    @patch('src.utils.backtester_v2.alpaca_manager')
    @patch('src.utils.backtester_v2.get_strategy')
    def test_run_with_insufficient_data_for_strategy(self, mock_get_strategy, mock_alpaca):
        """Test backtest when data is insufficient for strategy requirements."""
        # Mock strategy with high min_bars_required
        mock_strategy = MagicMock()
        mock_strategy.min_bars_required = 100
        mock_get_strategy.return_value = mock_strategy
        
        # Mock data with only 50 bars
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'open': range(100, 150),
            'high': range(105, 155),
            'low': range(95, 145),
            'close': range(100, 150),
            'volume': [1000000] * 50
        }, index=dates)
        mock_alpaca.fetch_historical_bars.return_value = data
        
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        result = backtester.run('SPY', '3ma')
        
        # Should return zero trades (insufficient data)
        self.assertEqual(result['trades'], 0)
    
    @patch('src.utils.backtester_v2.settings')
    @patch('src.utils.backtester_v2.alpaca_manager')
    @patch('src.utils.backtester_v2.get_strategy')
    def test_run_uses_default_data_feed_from_settings(self, mock_get_strategy, mock_alpaca, mock_settings):
        """Test that backtest uses default data feed from settings."""
        mock_settings.alpaca_data_feed = 'iex'
        
        mock_strategy = MagicMock()
        mock_strategy.min_bars_required = 5
        mock_strategy.generate_signal.return_value = {'signal': 'HOLD'}
        mock_strategy.validate_signal.return_value = {'signal': 'HOLD'}
        mock_get_strategy.return_value = mock_strategy
        
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        data = pd.DataFrame({
            'open': range(100, 120),
            'high': range(105, 125),
            'low': range(95, 115),
            'close': range(100, 120),
            'volume': [1000000] * 20
        }, index=dates)
        mock_alpaca.fetch_historical_bars.return_value = data
        
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        result = backtester.run('SPY', '3ma')
        
        # Verify strategy validation was called with data feed
        self.assertTrue(mock_strategy.validate_signal.called)
        self.assertIsNotNone(result)


class TestBacktestCompare(unittest.TestCase):
    """Test strategy comparison functionality."""
    
    @patch.object(BacktesterV2, 'run')
    def test_compare_multiple_strategies(self, mock_run):
        """Test comparing performance of multiple strategies."""
        # Mock different results for each strategy
        mock_run.side_effect = [
            {'trades': 10, 'pnl': 1000.0, 'win_rate': 60.0, 'sharpe_ratio': 1.5},
            {'trades': 15, 'pnl': 1500.0, 'win_rate': 70.0, 'sharpe_ratio': 2.0},
            {'trades': 12, 'pnl': 800.0, 'win_rate': 50.0, 'sharpe_ratio': 1.0},
        ]
        
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        results = backtester.compare('SPY', ['3ma', 'rsi_breakout', 'macd'])
        
        # Should have results for all 3 strategies
        self.assertEqual(len(results), 3)
        self.assertIn('3ma', results)
        self.assertIn('rsi_breakout', results)
        self.assertIn('macd', results)
        
        # Verify each strategy's results
        self.assertEqual(results['3ma']['trades'], 10)
        self.assertEqual(results['rsi_breakout']['trades'], 15)
        self.assertEqual(results['macd']['trades'], 12)
        
        # Verify run was called for each strategy
        self.assertEqual(mock_run.call_count, 3)


class TestBacktesterEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_negative_risk_free_rate(self):
        """Test backtester with negative risk-free rate."""
        backtester = BacktesterV2('2024-01-01', '2024-06-30', risk_free_rate=-0.01)
        self.assertEqual(backtester.risk_free_rate, -0.01)
    
    def test_very_large_commission(self):
        """Test performance calculation with large commissions."""
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 50.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 110.0, 'commission': 50.0},
        ]
        
        result = backtester.calculate_performance(trades, '1Day')
        
        # Should still calculate correctly (negative due to commissions)
        self.assertEqual(result['pnl'], -90.0)  # 110 - 100 - 100
    
    def test_zero_commission_trades(self):
        """Test trades with zero commission."""
        backtester = BacktesterV2('2024-01-01', '2024-06-30')
        
        trades = [
            {'date': '2024-01-01', 'type': 'BUY', 'price': 100.0, 'commission': 0.0},
            {'date': '2024-01-10', 'type': 'SELL', 'price': 110.0, 'commission': 0.0},
        ]
        
        result = backtester.calculate_performance(trades, '1Day')
        
        self.assertEqual(result['pnl'], 10.0)  # Exact price difference


if __name__ == '__main__':
    unittest.main()
