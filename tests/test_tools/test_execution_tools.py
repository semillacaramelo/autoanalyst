"""
Tests for execution_tools.py - Order placement and risk management.

This module tests trade execution, position sizing, and portfolio constraints.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.tools.execution_tools import ExecutionTools, execution_tools


class TestCalculatePositionSize(unittest.TestCase):
    """Test position sizing calculations."""
    
    @patch('src.tools.execution_tools.settings')
    def test_normal_position_size(self, mock_settings):
        """Test position size calculation with normal values."""
        mock_settings.max_risk_per_trade = 0.02  # 2%
        
        result = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=100.0,
            atr=2.0,
            account_equity=10000.0
        )
        
        # risk_amount = 10000 * 0.02 = 200
        # shares = 200 / 2.0 = 100
        self.assertEqual(result['shares'], 100)
        self.assertEqual(result['total_cost'], 10000.0)  # 100 shares * $100
        self.assertEqual(result['risk_amount'], 200.0)
        self.assertEqual(result['price_per_share'], 100.0)
        self.assertEqual(result['atr_used'], 2.0)
    
    @patch('src.tools.execution_tools.settings')
    def test_zero_atr_fallback(self, mock_settings):
        """Test fallback when ATR is zero."""
        mock_settings.max_risk_per_trade = 0.02
        
        result = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=50.0,
            atr=0.0,  # Zero ATR
            account_equity=10000.0
        )
        
        # Falls back to 1% of equity / price
        # shares = (10000 * 0.01) / 50 = 2
        self.assertEqual(result['shares'], 2)
        self.assertIn('atr_used', result)
    
    @patch('src.tools.execution_tools.settings')
    def test_minimum_one_share(self, mock_settings):
        """Test that position size is at least 1 share."""
        mock_settings.max_risk_per_trade = 0.001  # Very small risk
        
        result = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=10000.0,  # Very expensive stock
            atr=100.0,
            account_equity=1000.0
        )
        
        # Even with small account, should get at least 1 share
        self.assertGreaterEqual(result['shares'], 1)
    
    @patch('src.tools.execution_tools.settings')
    def test_high_volatility_reduces_shares(self, mock_settings):
        """Test that higher ATR (volatility) reduces position size."""
        mock_settings.max_risk_per_trade = 0.02
        
        # Low volatility
        result_low = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=100.0,
            atr=1.0,  # Low volatility
            account_equity=10000.0
        )
        
        # High volatility
        result_high = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=100.0,
            atr=5.0,  # High volatility
            account_equity=10000.0
        )
        
        # Higher ATR should result in fewer shares
        self.assertGreater(result_low['shares'], result_high['shares'])
    
    @patch('src.tools.execution_tools.settings')
    def test_error_handling(self, mock_settings):
        """Test error handling in position size calculation."""
        mock_settings.max_risk_per_trade = 0.02
        
        # Invalid inputs (e.g., negative values shouldn't crash)
        result = ExecutionTools.calculate_position_size(
            signal='BUY',
            current_price=-100.0,  # Invalid price
            atr=2.0,
            account_equity=10000.0
        )
        
        # Should return fallback with minimum shares
        self.assertIn('shares', result)
        self.assertGreaterEqual(result['shares'], 1)


class TestCheckPortfolioConstraints(unittest.TestCase):
    """Test portfolio constraint checks."""
    
    @patch('src.tools.execution_tools.settings')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_all_constraints_pass(self, mock_alpaca, mock_settings):
        """Test when all portfolio constraints pass."""
        mock_settings.max_open_positions = 5
        mock_settings.daily_loss_limit = 0.05  # 5%
        
        # Mock account with no losses
        mock_alpaca.get_account.return_value = {
            'equity': '10000.00',
            'last_equity': '10000.00',
            'buying_power': '5000.00',
            'trading_blocked': False
        }
        
        # Mock 2 open positions (under limit of 5)
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'SPY', 'qty': '10'},
            {'symbol': 'QQQ', 'qty': '5'}
        ]
        
        result = ExecutionTools.check_portfolio_constraints()
        
        self.assertTrue(result['approved'])
        self.assertTrue(result['checks']['max_positions']['passed'])
        self.assertTrue(result['checks']['daily_loss']['passed'])
        self.assertTrue(result['checks']['trading_status']['passed'])
    
    @patch('src.tools.execution_tools.settings')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_max_positions_exceeded(self, mock_alpaca, mock_settings):
        """Test when max positions limit is exceeded."""
        mock_settings.max_open_positions = 3
        mock_settings.daily_loss_limit = 0.05
        
        mock_alpaca.get_account.return_value = {
            'equity': '10000.00',
            'last_equity': '10000.00',
            'buying_power': '5000.00',
            'trading_blocked': False
        }
        
        # Mock 4 positions (exceeds limit of 3)
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'SPY'},
            {'symbol': 'QQQ'},
            {'symbol': 'AAPL'},
            {'symbol': 'MSFT'}
        ]
        
        result = ExecutionTools.check_portfolio_constraints()
        
        self.assertFalse(result['approved'])
        self.assertFalse(result['checks']['max_positions']['passed'])
        self.assertEqual(result['checks']['max_positions']['current'], 4)
    
    @patch('src.tools.execution_tools.settings')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_daily_loss_limit_exceeded(self, mock_alpaca, mock_settings):
        """Test when daily loss limit is exceeded."""
        mock_settings.max_open_positions = 5
        mock_settings.daily_loss_limit = 0.05  # 5% limit
        
        # Mock account with 6% loss
        mock_alpaca.get_account.return_value = {
            'equity': '9400.00',      # Current equity
            'last_equity': '10000.00', # Yesterday's equity
            'buying_power': '5000.00',
            'trading_blocked': False
        }
        
        mock_alpaca.get_positions.return_value = []
        
        result = ExecutionTools.check_portfolio_constraints()
        
        self.assertFalse(result['approved'])
        self.assertFalse(result['checks']['daily_loss']['passed'])
        # Loss: (9400 / 10000) - 1 = -0.06 = -6%
        self.assertLess(result['checks']['daily_loss']['current_loss_pct'], -5.0)
    
    @patch('src.tools.execution_tools.settings')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_trading_blocked(self, mock_alpaca, mock_settings):
        """Test when trading is blocked."""
        mock_settings.max_open_positions = 5
        mock_settings.daily_loss_limit = 0.05
        
        # Mock account with trading blocked
        mock_alpaca.get_account.return_value = {
            'equity': '10000.00',
            'last_equity': '10000.00',
            'buying_power': '0.00',
            'trading_blocked': True  # Trading blocked!
        }
        
        mock_alpaca.get_positions.return_value = []
        
        result = ExecutionTools.check_portfolio_constraints()
        
        self.assertFalse(result['approved'])
        self.assertFalse(result['checks']['trading_status']['passed'])
        self.assertTrue(result['checks']['trading_status']['blocked'])
    
    @patch('src.tools.execution_tools.settings')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_missing_last_equity(self, mock_alpaca, mock_settings):
        """Test handling of missing last_equity field."""
        mock_settings.max_open_positions = 5
        mock_settings.daily_loss_limit = 0.05
        
        # Mock account with missing last_equity
        mock_alpaca.get_account.return_value = {
            'equity': '10000.00',
            'last_equity': None,  # Missing value
            'buying_power': '5000.00',
            'trading_blocked': False
        }
        
        mock_alpaca.get_positions.return_value = []
        
        result = ExecutionTools.check_portfolio_constraints()
        
        # Should still approve (skips loss check)
        self.assertTrue(result['approved'])
    
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_error_handling(self, mock_alpaca):
        """Test error handling when API calls fail."""
        # Mock API failure
        mock_alpaca.get_account.side_effect = Exception("API Error")
        
        result = ExecutionTools.check_portfolio_constraints()
        
        self.assertFalse(result['approved'])
        self.assertIn('error', result)


class TestPlaceOrder(unittest.TestCase):
    """Test order placement functionality."""
    
    @patch('src.tools.execution_tools.ExecutionTools.check_portfolio_constraints')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_successful_buy_order(self, mock_alpaca, mock_constraints):
        """Test successful BUY order placement."""
        # Mock constraints passing
        mock_constraints.return_value = {
            'approved': True,
            'checks': {},
            'account_info': {'equity': '10000', 'buying_power': '5000'}
        }
        
        # Mock order placement
        mock_alpaca.place_market_order.return_value = {
            'status': 'submitted',
            'order_id': 'order123',
            'symbol': 'SPY',
            'qty': 10,
            'side': 'BUY'
        }
        
        result = ExecutionTools.place_order('SPY', 10, 'BUY')
        
        self.assertTrue(result['success'])
        self.assertIn('order', result)
        self.assertEqual(result['order']['order_id'], 'order123')
        
        # Verify order was placed correctly
        mock_alpaca.place_market_order.assert_called_once_with(
            symbol='SPY',
            qty=10,
            side='BUY'
        )
    
    @patch('src.tools.execution_tools.ExecutionTools.check_portfolio_constraints')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_successful_sell_order(self, mock_alpaca, mock_constraints):
        """Test successful SELL order placement."""
        mock_constraints.return_value = {
            'approved': True,
            'checks': {},
            'account_info': {'equity': '10000', 'buying_power': '5000'}
        }
        
        mock_alpaca.place_market_order.return_value = {
            'status': 'submitted',
            'order_id': 'order456',
            'symbol': 'AAPL',
            'qty': 5,
            'side': 'SELL'
        }
        
        result = ExecutionTools.place_order('AAPL', 5, 'SELL')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order']['side'], 'SELL')
    
    @patch('src.tools.execution_tools.ExecutionTools.check_portfolio_constraints')
    def test_order_rejected_by_constraints(self, mock_constraints):
        """Test order rejected when constraints fail."""
        # Mock constraints failing
        mock_constraints.return_value = {
            'approved': False,
            'checks': {'max_positions': {'passed': False}}
        }
        
        result = ExecutionTools.place_order('SPY', 10, 'BUY')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'constraints_failed')
        self.assertIn('constraints', result)
    
    def test_invalid_side(self):
        """Test order with invalid side parameter."""
        result = ExecutionTools.place_order('SPY', 10, 'INVALID')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'exception')
        self.assertIn('error', result)
    
    def test_invalid_quantity(self):
        """Test order with invalid quantity."""
        result = ExecutionTools.place_order('SPY', -5, 'BUY')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('src.tools.execution_tools.ExecutionTools.check_portfolio_constraints')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_dry_run_mode(self, mock_alpaca, mock_constraints):
        """Test order in DRY_RUN mode."""
        mock_constraints.return_value = {'approved': True}
        
        # Mock dry run response
        mock_alpaca.place_market_order.return_value = {
            'status': 'dry_run',
            'order_id': 'dry_run_123',
            'symbol': 'SPY',
            'qty': 10,
            'side': 'BUY'
        }
        
        result = ExecutionTools.place_order('SPY', 10, 'BUY')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['order']['status'], 'dry_run')
    
    @patch('src.tools.execution_tools.ExecutionTools.check_portfolio_constraints')
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_order_placement_failure(self, mock_alpaca, mock_constraints):
        """Test handling of order placement failure."""
        mock_constraints.return_value = {'approved': True}
        
        # Mock order failure
        mock_alpaca.place_market_order.return_value = {
            'status': 'rejected',
            'reason': 'Insufficient buying power'
        }
        
        result = ExecutionTools.place_order('SPY', 10, 'BUY')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'], 'order_failed')


class TestGetPositionForSymbol(unittest.TestCase):
    """Test position retrieval."""
    
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_get_existing_position(self, mock_alpaca):
        """Test getting an existing position."""
        # Mock positions list
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'SPY', 'qty': '10', 'avg_entry_price': '450.00'},
            {'symbol': 'QQQ', 'qty': '5', 'avg_entry_price': '380.00'},
            {'symbol': 'AAPL', 'qty': '20', 'avg_entry_price': '175.00'}
        ]
        
        result = ExecutionTools.get_position_for_symbol('QQQ')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'QQQ')
        self.assertEqual(result['qty'], '5')
    
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_get_nonexistent_position(self, mock_alpaca):
        """Test getting a non-existent position."""
        mock_alpaca.get_positions.return_value = [
            {'symbol': 'SPY', 'qty': '10'},
            {'symbol': 'QQQ', 'qty': '5'}
        ]
        
        result = ExecutionTools.get_position_for_symbol('TSLA')
        
        self.assertIsNone(result)
    
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_no_positions(self, mock_alpaca):
        """Test when there are no open positions."""
        mock_alpaca.get_positions.return_value = []
        
        result = ExecutionTools.get_position_for_symbol('SPY')
        
        self.assertIsNone(result)
    
    @patch('src.tools.execution_tools.alpaca_manager')
    def test_error_handling(self, mock_alpaca):
        """Test error handling when API fails."""
        mock_alpaca.get_positions.side_effect = Exception("API Error")
        
        result = ExecutionTools.get_position_for_symbol('SPY')
        
        self.assertIsNone(result)


class TestExecutionToolsGlobalInstance(unittest.TestCase):
    """Test global execution_tools instance."""
    
    def test_global_instance_exists(self):
        """Test that global instance is created."""
        from src.tools.execution_tools import execution_tools
        
        self.assertIsNotNone(execution_tools)
        self.assertIsInstance(execution_tools, ExecutionTools)


if __name__ == '__main__':
    unittest.main()
