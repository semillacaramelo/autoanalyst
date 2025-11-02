"""
Tests for Market Rotation Strategy
Validates intelligent market selection based on time and performance.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import tempfile
import json

from src.crew.market_rotation_strategy import MarketRotationStrategy


class TestMarketRotationStrategy(unittest.TestCase):
    """Test suite for market rotation strategy."""
    
    def setUp(self):
        """Set up test fixtures with temporary state file."""
        # Create temporary state file for each test
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "test_rotation_state.json"
        self.strategy = MarketRotationStrategy(state_file=self.state_file)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_1_us_market_hours_priority(self):
        """Test that US_EQUITY is prioritized during market hours."""
        # Mock time during US market hours (11:00 AM ET = 3:00 PM UTC)
        us_market_time = datetime(2025, 11, 3, 15, 0, 0, tzinfo=pytz.utc)  # Monday 11:00 AM ET
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            # Both markets active, but US should be prioritized
            mock_active.return_value = ['US_EQUITY', 'CRYPTO']
            
            selected = self.strategy.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False  # Disable performance overlay
            )
            
            self.assertEqual(selected, 'US_EQUITY', "US_EQUITY should be prioritized during market hours")
    
    def test_2_crypto_when_us_closed(self):
        """Test that CRYPTO is selected when US market is closed."""
        # Mock time after US market close (8:00 PM ET = 1:00 AM UTC)
        us_closed_time = datetime(2025, 11, 4, 1, 0, 0, tzinfo=pytz.utc)  # Tuesday 8:00 PM ET (previous day)
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            # Only crypto active (24/7)
            mock_active.return_value = ['CRYPTO']
            
            selected = self.strategy.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=False
            )
            
            self.assertEqual(selected, 'CRYPTO', "CRYPTO should be selected when US market is closed")
    
    def test_3_performance_tracking(self):
        """Test that performance metrics are tracked correctly."""
        # Add some trade results
        trade_1 = {
            'success': True,
            'profit': 150.0,
            'symbol': 'AAPL',
            'strategy': '3ma',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        
        trade_2 = {
            'success': False,
            'profit': -50.0,
            'symbol': 'MSFT',
            'strategy': 'rsi_breakout',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        
        trade_3 = {
            'success': True,
            'profit': 200.0,
            'symbol': 'GOOGL',
            'strategy': 'macd',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        
        # Update performance
        self.strategy.update_market_performance('US_EQUITY', trade_1)
        self.strategy.update_market_performance('US_EQUITY', trade_2)
        self.strategy.update_market_performance('US_EQUITY', trade_3)
        
        # Check metrics
        stats = self.strategy.get_market_statistics()
        equity_stats = stats['markets']['US_EQUITY']
        
        self.assertEqual(equity_stats['trades'], 3, "Should track 3 trades")
        self.assertEqual(equity_stats['wins'], 2, "Should track 2 wins")
        self.assertAlmostEqual(equity_stats['win_rate'], 2/3, places=2, msg="Win rate should be 66.67%")
        self.assertAlmostEqual(equity_stats['total_profit'], 300.0, places=2, msg="Total profit should be $300")
        self.assertAlmostEqual(equity_stats['avg_profit'], 100.0, places=2, msg="Avg profit should be $100")
    
    def test_4_performance_score_calculation(self):
        """Test that market score calculation is correct."""
        # Add trades to CRYPTO
        for i in range(10):
            trade = {
                'success': True if i < 8 else False,  # 80% win rate
                'profit': 100.0 if i < 8 else -50.0,
                'symbol': f'BTC-USD',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            }
            self.strategy.update_market_performance('CRYPTO', trade)
        
        # Calculate score
        score = self.strategy._calculate_market_score('CRYPTO')
        
        # Expected: win_rate (0.8) × avg_profit (70) × log(11) ≈ 0.8 × 70 × 2.4 ≈ 134.4
        self.assertGreater(score, 0, "Score should be positive")
        self.assertGreater(score, 100, "Score should be > 100 with good performance")
        
        # Add trades to US_EQUITY with worse performance
        for i in range(10):
            trade = {
                'success': True if i < 5 else False,  # 50% win rate
                'profit': 50.0 if i < 5 else -50.0,
                'symbol': f'AAPL',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            }
            self.strategy.update_market_performance('US_EQUITY', trade)
        
        equity_score = self.strategy._calculate_market_score('US_EQUITY')
        
        # CRYPTO should have higher score (better win rate and profit)
        self.assertGreater(score, equity_score, "CRYPTO score should be higher than US_EQUITY")
    
    def test_5_performance_based_override(self):
        """Test that performance can override time-based selection."""
        # Add excellent CRYPTO performance
        for i in range(10):
            trade = {
                'success': True,  # 100% win rate
                'profit': 200.0,
                'symbol': 'BTC-USD',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            }
            self.strategy.update_market_performance('CRYPTO', trade)
        
        # Add poor US_EQUITY performance
        for i in range(10):
            trade = {
                'success': False,  # 0% win rate
                'profit': -100.0,
                'symbol': 'AAPL',
                'strategy': '3ma',
                'timestamp': datetime.now(pytz.utc).isoformat()
            }
            self.strategy.update_market_performance('US_EQUITY', trade)
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            # Both markets active
            mock_active.return_value = ['US_EQUITY', 'CRYPTO']
            
            # With performance consideration, CRYPTO should be selected despite US market hours
            selected = self.strategy.select_active_market(
                target_markets=['US_EQUITY', 'CRYPTO'],
                consider_performance=True
            )
            
            # CRYPTO has 100% win rate vs 0%, so it should override time-based priority
            self.assertEqual(selected, 'CRYPTO', "Performance should override time-based selection when significantly better")
    
    def test_6_rotation_tracking(self):
        """Test that market rotations are tracked correctly."""
        initial_count = self.strategy.performance_state.get('rotation_count', 0)
        
        with patch('src.utils.market_calendar.MarketCalendar.get_active_markets') as mock_active:
            # First selection: US_EQUITY (counts as rotation from None)
            mock_active.return_value = ['US_EQUITY']
            self.strategy.select_active_market(consider_performance=False)
            
            # Second selection: CRYPTO (should increment)
            mock_active.return_value = ['CRYPTO']
            self.strategy.select_active_market(consider_performance=False)
            
            # Third selection: CRYPTO again (should NOT increment)
            mock_active.return_value = ['CRYPTO']
            self.strategy.select_active_market(consider_performance=False)
            
            # Fourth selection: US_EQUITY (should increment)
            mock_active.return_value = ['US_EQUITY']
            self.strategy.select_active_market(consider_performance=False)
        
        stats = self.strategy.get_market_statistics()
        
        # Should have 3 rotations (None→US_EQUITY, US_EQUITY→CRYPTO, CRYPTO→US_EQUITY)
        self.assertEqual(stats['rotation_count'], initial_count + 3, "Should track 3 rotations")
        self.assertEqual(stats['last_rotation'], 'US_EQUITY', "Last rotation should be US_EQUITY")
    
    def test_7_state_persistence(self):
        """Test that state is saved and loaded correctly."""
        # Add performance data
        trade = {
            'success': True,
            'profit': 100.0,
            'symbol': 'AAPL',
            'strategy': '3ma',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        self.strategy.update_market_performance('US_EQUITY', trade)
        
        # Create new strategy instance (should load state)
        new_strategy = MarketRotationStrategy(state_file=self.state_file)
        
        # Check that state was loaded
        stats = new_strategy.get_market_statistics()
        self.assertEqual(stats['markets']['US_EQUITY']['trades'], 1, "State should persist across instances")
        self.assertAlmostEqual(stats['markets']['US_EQUITY']['total_profit'], 100.0, places=2)
    
    def test_8_reset_performance(self):
        """Test that performance can be reset."""
        # Add performance data
        trade = {
            'success': True,
            'profit': 100.0,
            'symbol': 'BTC-USD',
            'strategy': '3ma',
            'timestamp': datetime.now(pytz.utc).isoformat()
        }
        self.strategy.update_market_performance('CRYPTO', trade)
        
        # Verify data exists
        stats = self.strategy.get_market_statistics()
        self.assertEqual(stats['markets']['CRYPTO']['trades'], 1)
        
        # Reset CRYPTO only
        self.strategy.reset_performance('CRYPTO')
        
        # Verify CRYPTO reset
        stats = self.strategy.get_market_statistics()
        self.assertEqual(stats['markets']['CRYPTO']['trades'], 0, "CRYPTO should be reset")
        
        # Add data to both markets
        self.strategy.update_market_performance('CRYPTO', trade)
        self.strategy.update_market_performance('US_EQUITY', trade)
        
        # Reset all
        self.strategy.reset_performance()
        
        # Verify all reset
        stats = self.strategy.get_market_statistics()
        self.assertEqual(stats['markets']['CRYPTO']['trades'], 0, "All markets should be reset")
        self.assertEqual(stats['markets']['US_EQUITY']['trades'], 0, "All markets should be reset")
        self.assertEqual(stats['rotation_count'], 0, "Rotation count should be reset")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
