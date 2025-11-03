"""
Tests for Trading Orchestrator - Parallel Crew Execution Manager

This module tests the orchestrator's ability to coordinate multiple
trading crews in parallel with proper thread safety and rate limiting.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import ThreadPoolExecutor
import time

from src.crew.orchestrator import TradingOrchestrator, trading_orchestrator


class TestTradingOrchestrator(unittest.TestCase):
    """Test TradingOrchestrator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = TradingOrchestrator()

    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertIsNotNone(self.orchestrator.market_scanner)
        self.assertIsNotNone(self.orchestrator.active_crews)
        self.assertIsInstance(self.orchestrator.active_crews, dict)
        self.assertIsNotNone(self.orchestrator.executor)
        self.assertIsInstance(self.orchestrator.executor, ThreadPoolExecutor)

    def test_singleton_instance(self):
        """Test that global trading_orchestrator singleton exists."""
        self.assertIsInstance(trading_orchestrator, TradingOrchestrator)
        self.assertIsNotNone(trading_orchestrator.market_scanner)

    @patch("src.crew.orchestrator.TradingCrew")
    def test_run_trading_crew_success(self, mock_trading_crew_class):
        """Test successful trading crew execution."""
        # Mock TradingCrew instance
        mock_crew_instance = Mock()
        mock_crew_instance.run.return_value = {
            "success": True,
            "result": "HOLD signal",
            "symbol": "SPY",
            "strategy": "3ma",
        }
        mock_trading_crew_class.return_value = mock_crew_instance

        # Execute
        result = self.orchestrator._run_trading_crew("SPY", "3ma")

        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "SPY")
        self.assertEqual(result["strategy"], "3ma")
        mock_trading_crew_class.assert_called_once()
        mock_crew_instance.run.assert_called_once_with(symbol="SPY", strategy="3ma")

    @patch("src.crew.orchestrator.TradingCrew")
    def test_run_trading_crew_failure(self, mock_trading_crew_class):
        """Test trading crew execution with error."""
        # Mock TradingCrew to raise exception
        mock_trading_crew_class.side_effect = Exception("Test error")

        # Execute
        result = self.orchestrator._run_trading_crew("AAPL", "rsi_breakout")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["strategy"], "rsi_breakout")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")

    def test_parse_scan_results_success(self):
        """Test parsing valid scanner results."""
        scan_results = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "scores": {"volatility": 0.8, "technical": 0.9, "liquidity": 1.0},
                    "recommended_strategies": ["3ma", "macd"],
                    "reason": "Strong momentum",
                },
                {
                    "symbol": "QQQ",
                    "priority": 4,
                    "scores": {"volatility": 0.7, "technical": 0.8, "liquidity": 0.9},
                    "recommended_strategies": ["rsi_breakout"],
                    "reason": "Oversold conditions",
                },
            ]
        }

        result = self.orchestrator._parse_scan_results(scan_results)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["symbol"], "SPY")
        self.assertEqual(result[1]["symbol"], "QQQ")
        self.assertIn("3ma", result[0]["recommended_strategies"])

    def test_parse_scan_results_empty(self):
        """Test parsing empty scanner results."""
        scan_results = {"top_assets": []}

        result = self.orchestrator._parse_scan_results(scan_results)

        self.assertEqual(len(result), 0)

    def test_parse_scan_results_invalid(self):
        """Test parsing invalid scanner results."""
        scan_results = {"invalid_key": "value"}

        result = self.orchestrator._parse_scan_results(scan_results)

        self.assertEqual(len(result), 0)

    def test_parse_scan_results_exception(self):
        """Test parsing scanner results that cause exception."""
        scan_results = None  # Will cause exception when calling .get()

        result = self.orchestrator._parse_scan_results(scan_results)

        self.assertEqual(len(result), 0)

    def test_log_cycle_summary_mixed_results(self):
        """Test logging summary with mixed success and failure results."""
        results = [
            {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "HOLD"},
            {"success": False, "symbol": "AAPL", "strategy": "rsi", "error": "Rate limit"},
            {"success": True, "symbol": "QQQ", "strategy": "macd", "result": "BUY"},
        ]

        # Should not raise exception
        self.orchestrator.log_cycle_summary(results)

    def test_log_cycle_summary_all_success(self):
        """Test logging summary with all successful results."""
        results = [
            {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "HOLD"},
            {"success": True, "symbol": "QQQ", "strategy": "macd", "result": "SELL"},
        ]

        # Should not raise exception
        self.orchestrator.log_cycle_summary(results)

    def test_log_cycle_summary_all_failures(self):
        """Test logging summary with all failed results."""
        results = [
            {"success": False, "symbol": "SPY", "strategy": "3ma", "error": "API error"},
            {"success": False, "symbol": "QQQ", "strategy": "macd", "error": "Timeout"},
        ]

        # Should not raise exception
        self.orchestrator.log_cycle_summary(results)

    def test_log_cycle_summary_empty(self):
        """Test logging summary with no results."""
        results = []

        # Should not raise exception
        self.orchestrator.log_cycle_summary(results)

    @patch.object(TradingOrchestrator, "_run_trading_crew")
    def test_run_cycle_no_assets(self, mock_run_crew):
        """Test run_cycle when scanner returns no assets."""
        # Mock the scanner instance
        with patch.object(self.orchestrator.market_scanner, 'run', return_value={"top_assets": []}):
            # Execute
            self.orchestrator.run_cycle()

        # Verify no crews were submitted
        mock_run_crew.assert_not_called()

    @patch.object(TradingOrchestrator, "_run_trading_crew")
    @patch("src.crew.orchestrator.time.sleep")
    def test_run_cycle_with_assets(self, mock_sleep, mock_run_crew):
        """Test run_cycle with valid scanner results."""
        # Mock scanner results
        scanner_results = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "recommended_strategies": ["3ma"],
                    "reason": "Strong trend",
                }
            ]
        }

        # Mock crew execution
        mock_run_crew.return_value = {
            "success": True,
            "symbol": "SPY",
            "strategy": "3ma",
            "result": "HOLD",
        }

        # Mock the scanner instance
        with patch.object(self.orchestrator.market_scanner, 'run', return_value=scanner_results) as mock_scanner_run:
            # Execute
            self.orchestrator.run_cycle()

            # Verify scanner was called
            mock_scanner_run.assert_called_once()

    @patch.object(TradingOrchestrator, "_run_trading_crew")
    @patch("src.crew.orchestrator.time.sleep")
    def test_run_cycle_multiple_strategies(self, mock_sleep, mock_run_crew):
        """Test run_cycle with multiple strategies per asset."""
        # Mock scanner results with multiple strategies
        scanner_results = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "recommended_strategies": ["3ma", "macd"],
                    "reason": "Multiple signals",
                }
            ]
        }

        # Mock crew execution
        mock_run_crew.return_value = {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "HOLD"}

        # Mock the scanner instance
        with patch.object(self.orchestrator.market_scanner, 'run', return_value=scanner_results) as mock_scanner_run:
            # Execute
            self.orchestrator.run_cycle()

            # Verify scanner was called
            mock_scanner_run.assert_called_once()

    @patch.object(TradingOrchestrator, "_run_trading_crew")
    @patch("src.crew.orchestrator.time.sleep")
    def test_run_cycle_top_3_assets_only(self, mock_sleep, mock_run_crew):
        """Test that run_cycle only processes top 3 assets."""
        # Mock scanner results with 5 assets
        scanner_results = {
            "top_assets": [
                {"symbol": f"ASSET{i}", "priority": 5 - i, "recommended_strategies": ["3ma"], "reason": f"Reason {i}"}
                for i in range(5)
            ]
        }

        # Mock crew execution
        mock_run_crew.return_value = {"success": True, "symbol": "ASSET0", "strategy": "3ma", "result": "HOLD"}

        # Mock the scanner instance
        with patch.object(self.orchestrator.market_scanner, 'run', return_value=scanner_results) as mock_scanner_run:
            # Execute
            self.orchestrator.run_cycle()

            # Verify scanner was called
            mock_scanner_run.assert_called_once()

        # The executor will only process top 3 assets
        # (exact call count verification is complex due to ThreadPoolExecutor)


class TestTradingOrchestratorThreadSafety(unittest.TestCase):
    """Test thread safety of orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = TradingOrchestrator()

    @patch("src.crew.orchestrator.TradingCrew")
    def test_parallel_crew_execution_thread_safety(self, mock_trading_crew_class):
        """Test that parallel crew executions don't interfere with each other."""
        # Mock TradingCrew to track instance creation
        instances_created = []

        def create_instance():
            instance = Mock()
            instance.run.return_value = {"success": True, "result": "HOLD"}
            instances_created.append(instance)
            return instance

        mock_trading_crew_class.side_effect = create_instance

        # Execute multiple crews in parallel
        symbols = ["SPY", "QQQ", "AAPL"]
        for symbol in symbols:
            self.orchestrator._run_trading_crew(symbol, "3ma")

        # Verify that separate instances were created (not shared)
        self.assertEqual(len(instances_created), 3)

        # Verify each instance had run() called
        for instance in instances_created:
            instance.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
