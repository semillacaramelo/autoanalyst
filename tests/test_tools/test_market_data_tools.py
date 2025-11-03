import unittest
import pandas as pd
from src.tools.market_data_tools import MarketDataTools
from datetime import datetime, timedelta


class TestMarketDataTools(unittest.TestCase):

    def test_validate_data_completeness_ambiguous_truth_error(self):
        """
        Verify that validate_data_completeness handles non-uniform time differences
        without raising the "ambiguous truth value" error.
        """
        # Arrange
        # Create a DataFrame with a non-uniform time difference, which will cause
        # the mode() function to return a Series of two values.
        timestamps = [
            datetime.now() - timedelta(minutes=3),
            datetime.now() - timedelta(minutes=2),
            datetime.now() - timedelta(minutes=0),  # 2 minute gap
        ]
        data = {
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }
        df = pd.DataFrame(data, index=pd.to_datetime(timestamps))

        # Act
        # This should not raise an exception.
        result = MarketDataTools.validate_data_completeness(df)

        # Assert
        # The validation should identify the time series gap.
        self.assertFalse(result["is_valid"])
        self.assertIn("Time series gaps detected: 1 gaps", result["issues"])


if __name__ == "__main__":
    unittest.main()
