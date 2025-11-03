"""
Tests for market_calendar.py - Market hours tracking.

This module tests market hours validation and schedule management.
"""

import unittest
from unittest.mock import patch
from datetime import datetime, time
import pytz

from src.utils.market_calendar import MarketCalendar


class TestMarketCalendarInit(unittest.TestCase):
    """Test market calendar initialization."""
    
    def test_initialization(self):
        """Test that market calendar initializes with predefined markets."""
        calendar = MarketCalendar()
        
        self.assertIn('US_EQUITY', calendar.MARKETS)
        self.assertIn('CRYPTO', calendar.MARKETS)
        self.assertIn('EU_EQUITY', calendar.MARKETS)
    
    def test_market_structure(self):
        """Test that markets have required fields."""
        calendar = MarketCalendar()
        
        for market_name, market in calendar.MARKETS.items():
            self.assertIn('open', market)
            self.assertIn('close', market)
            self.assertIn('tz', market)
            
            # Verify times are time objects
            self.assertIsInstance(market['open'], time)
            self.assertIsInstance(market['close'], time)
            
            # Verify timezone string
            self.assertIsInstance(market['tz'], str)


class TestGetActiveMarkets(unittest.TestCase):
    """Test active market detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = MarketCalendar()
    
    def test_us_equity_open_hours(self):
        """Test US equity market during open hours (9:30-16:00 ET)."""
        # Create timestamp for 10:00 AM ET (market open)
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 10, 0))
        
        active = self.calendar.get_active_markets(timestamp, ['US_EQUITY'])
        
        self.assertIn('US_EQUITY', active)
    
    def test_us_equity_closed_before_open(self):
        """Test US equity market before opening (before 9:30 ET)."""
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 9, 0))  # 9:00 AM
        
        active = self.calendar.get_active_markets(timestamp, ['US_EQUITY'])
        
        self.assertNotIn('US_EQUITY', active)
    
    def test_us_equity_closed_after_close(self):
        """Test US equity market after closing (after 16:00 ET)."""
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 17, 0))  # 5:00 PM
        
        active = self.calendar.get_active_markets(timestamp, ['US_EQUITY'])
        
        self.assertNotIn('US_EQUITY', active)
    
    def test_us_equity_open_boundary(self):
        """Test US equity at opening boundary (exactly 9:30 ET)."""
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 9, 30))
        
        active = self.calendar.get_active_markets(timestamp, ['US_EQUITY'])
        
        self.assertIn('US_EQUITY', active)
    
    def test_us_equity_close_boundary(self):
        """Test US equity at closing boundary (exactly 16:00 ET)."""
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 16, 0))
        
        active = self.calendar.get_active_markets(timestamp, ['US_EQUITY'])
        
        self.assertIn('US_EQUITY', active)
    
    def test_crypto_always_open(self):
        """Test that crypto market is always open (24/7)."""
        # Test at various times
        timestamps = [
            datetime(2025, 1, 15, 0, 0, tzinfo=pytz.utc),   # Midnight
            datetime(2025, 1, 15, 6, 0, tzinfo=pytz.utc),   # 6 AM
            datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc),  # Noon
            datetime(2025, 1, 15, 18, 0, tzinfo=pytz.utc),  # 6 PM
            datetime(2025, 1, 15, 23, 59, tzinfo=pytz.utc), # Almost midnight
        ]
        
        for timestamp in timestamps:
            active = self.calendar.get_active_markets(timestamp, ['CRYPTO'])
            self.assertIn('CRYPTO', active, f"Crypto should be open at {timestamp}")
    
    def test_multiple_markets(self):
        """Test checking multiple markets simultaneously."""
        # 10:00 AM ET = 3:00 PM London = 10:00 AM ET
        eastern = pytz.timezone('America/New_York')
        timestamp = eastern.localize(datetime(2025, 1, 15, 10, 0))
        
        active = self.calendar.get_active_markets(
            timestamp, 
            ['US_EQUITY', 'EU_EQUITY', 'CRYPTO']
        )
        
        # US and crypto should be open, EU might be open depending on time
        self.assertIn('US_EQUITY', active)
        self.assertIn('CRYPTO', active)
    
    def test_unknown_market(self):
        """Test that unknown markets are ignored."""
        timestamp = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        active = self.calendar.get_active_markets(timestamp, ['UNKNOWN_MARKET'])
        
        self.assertEqual(active, [])
    
    def test_empty_target_markets(self):
        """Test with empty target markets list."""
        timestamp = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        active = self.calendar.get_active_markets(timestamp, [])
        
        self.assertEqual(active, [])


class TestNextMarketOpen(unittest.TestCase):
    """Test next market opening calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = MarketCalendar()
    
    def test_next_open_before_market_hours(self):
        """Test finding next open when before market hours."""
        eastern = pytz.timezone('America/New_York')
        # 8:00 AM ET (before 9:30 open)
        timestamp = eastern.localize(datetime(2025, 1, 15, 8, 0))
        
        # Convert to UTC for the method call
        timestamp_utc = timestamp.astimezone(pytz.utc)
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp_utc
            
            next_open = self.calendar.next_market_open(['US_EQUITY'])
            
            self.assertIsNotNone(next_open)
            # Should be today at 9:30 AM ET
            next_open_et = next_open.astimezone(eastern)
            self.assertEqual(next_open_et.hour, 9)
            self.assertEqual(next_open_et.minute, 30)
    
    def test_next_open_after_market_close(self):
        """Test finding next open when after market close."""
        eastern = pytz.timezone('America/New_York')
        # 5:00 PM ET (after 4:00 PM close)
        timestamp = eastern.localize(datetime(2025, 1, 15, 17, 0))
        timestamp_utc = timestamp.astimezone(pytz.utc)
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp_utc
            
            next_open = self.calendar.next_market_open(['US_EQUITY'])
            
            self.assertIsNotNone(next_open)
            # Should be tomorrow at 9:30 AM ET
            next_open_et = next_open.astimezone(eastern)
            self.assertEqual(next_open_et.hour, 9)
            self.assertEqual(next_open_et.minute, 30)
            # Should be next day
            self.assertEqual(next_open_et.day, timestamp.day + 1)
    
    def test_next_open_multiple_markets(self):
        """Test finding earliest next open across multiple markets."""
        # Set time when no markets are open
        timestamp = datetime(2025, 1, 15, 5, 0, tzinfo=pytz.utc)  # 5 AM UTC
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            next_open = self.calendar.next_market_open(['US_EQUITY', 'EU_EQUITY'])
            
            self.assertIsNotNone(next_open)
            # Should return the earliest opening (EU opens before US)
    
    def test_next_open_crypto_immediate(self):
        """Test that crypto market is always considered open."""
        timestamp = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            next_open = self.calendar.next_market_open(['CRYPTO'])
            
            # Crypto is 24/7, so should return midnight today or tomorrow
            self.assertIsNotNone(next_open)
    
    def test_next_open_unknown_market(self):
        """Test with unknown market."""
        timestamp = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            next_open = self.calendar.next_market_open(['UNKNOWN_MARKET'])
            
            # Should return None for unknown markets
            self.assertIsNone(next_open)
    
    def test_next_open_empty_markets(self):
        """Test with empty markets list."""
        timestamp = datetime(2025, 1, 15, 12, 0, tzinfo=pytz.utc)
        
        with patch('src.utils.market_calendar.datetime') as mock_datetime:
            mock_datetime.now.return_value = timestamp
            
            next_open = self.calendar.next_market_open([])
            
            self.assertIsNone(next_open)


class TestEuEquityMarket(unittest.TestCase):
    """Test EU equity market hours."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar = MarketCalendar()
    
    def test_eu_equity_open_hours(self):
        """Test EU equity during open hours (8:00-16:30 London time)."""
        london = pytz.timezone('Europe/London')
        timestamp = london.localize(datetime(2025, 1, 15, 10, 0))
        
        active = self.calendar.get_active_markets(timestamp, ['EU_EQUITY'])
        
        self.assertIn('EU_EQUITY', active)
    
    def test_eu_equity_closed(self):
        """Test EU equity when closed."""
        london = pytz.timezone('Europe/London')
        timestamp = london.localize(datetime(2025, 1, 15, 7, 0))  # Before open
        
        active = self.calendar.get_active_markets(timestamp, ['EU_EQUITY'])
        
        self.assertNotIn('EU_EQUITY', active)


if __name__ == '__main__':
    unittest.main()
