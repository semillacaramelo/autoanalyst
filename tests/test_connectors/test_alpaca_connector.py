import unittest
from unittest.mock import patch, MagicMock
from src.connectors.alpaca_connector import AlpacaConnectionManager
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd
from datetime import datetime

class TestAlpacaConnector(unittest.TestCase):

    @patch('src.connectors.alpaca_connector.StockHistoricalDataClient')
    def test_fetch_historical_bars_timeframe_parsing(self, MockDataClient):
        """
        Verify that fetch_historical_bars correctly parses various timeframe strings.
        """
        # Arrange
        mock_instance = MockDataClient.return_value
        mock_instance.get_stock_bars.return_value = MagicMock(df=pd.DataFrame({
            'open': [100], 'high': [101], 'low': [99], 'close': [100.5], 'volume': [1000]
        }, index=[pd.to_datetime(datetime.now())]))

        manager = AlpacaConnectionManager()
        # To avoid re-initializing the mocked client, we assign it directly
        manager._data_client = mock_instance

        test_cases = {
            "1m": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1h": TimeFrame(1, TimeFrameUnit.Hour),
            "1d": TimeFrame(1, TimeFrameUnit.Day),
            "1Day": TimeFrame(1, TimeFrameUnit.Day),
        }

        for timeframe_str, expected_timeframe in test_cases.items():
            with self.subTest(timeframe=timeframe_str):
                # Act
                manager.fetch_historical_bars(symbol="SPY", timeframe=timeframe_str, limit=1)

                # Assert
                # Check that the call was made with the correct timeframe object
                called_args, called_kwargs = mock_instance.get_stock_bars.call_args
                request_params = called_args[0]
                self.assertEqual(request_params.timeframe.amount, expected_timeframe.amount)
                self.assertEqual(request_params.timeframe.unit, expected_timeframe.unit)

if __name__ == '__main__':
    unittest.main()
