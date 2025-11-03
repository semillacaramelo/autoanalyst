"""
Tests for orchestrator.py - Parallel crew execution manager.

This module tests the trading orchestrator's workflow including market scanning,
crew distribution, parallel execution, and result aggregation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future
from src.crew.orchestrator import TradingOrchestrator, trading_orchestrator


class TestOrchestratorInit(unittest.TestCase):
    """Test orchestrator initialization."""
    
    def test_initialization(self):
        """Test orchestrator initializes with correct attributes."""
        orch = TradingOrchestrator()
        self.assertIsNotNone(orch.market_scanner)
        self.assertEqual(orch.active_crews, {})
        self.assertIsNotNone(orch.executor)
        self.assertIsNone(orch.global_rate_limiter)
    
    def test_singleton_instance(self):
        """Test global singleton instance exists."""
        self.assertIsInstance(trading_orchestrator, TradingOrchestrator)


class TestRunTradingCrew(unittest.TestCase):
    """Test single trading crew execution."""
    
    def setUp(self):
        self.orch = TradingOrchestrator()
    
    @patch('src.crew.orchestrator.TradingCrew')
    def test_run_trading_crew_success(self, mock_trading_crew_class):
        """Test successful trading crew execution."""
        mock_crew = Mock()
        mock_crew.run.return_value = {
            "success": True,
            "symbol": "SPY",
            "strategy": "3ma",
            "result": "Trade executed"
        }
        mock_trading_crew_class.return_value = mock_crew
        
        result = self.orch._run_trading_crew("SPY", "3ma")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "SPY")
        self.assertEqual(result["strategy"], "3ma")
        mock_crew.run.assert_called_once_with(symbol="SPY", strategy="3ma")
    
    @patch('src.crew.orchestrator.TradingCrew')
    def test_run_trading_crew_failure(self, mock_trading_crew_class):
        """Test trading crew execution handles errors gracefully."""
        mock_crew = Mock()
        mock_crew.run.side_effect = Exception("API connection failed")
        mock_trading_crew_class.return_value = mock_crew
        
        result = self.orch._run_trading_crew("AAPL", "rsi_breakout")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["strategy"], "rsi_breakout")
        self.assertIn("API connection failed", result["error"])


class TestParseScanResults(unittest.TestCase):
    """Test market scanner result parsing."""
    
    def setUp(self):
        self.orch = TradingOrchestrator()
    
    def test_parse_valid_results(self):
        """Test parsing valid scanner results."""
        scan_results = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "scores": {"volatility": 0.8, "technical": 0.9, "liquidity": 1.0},
                    "recommended_strategies": ["3ma", "rsi_breakout"],
                    "reason": "Strong uptrend"
                },
                {
                    "symbol": "QQQ",
                    "priority": 4,
                    "scores": {"volatility": 0.7, "technical": 0.85, "liquidity": 0.95},
                    "recommended_strategies": ["macd"],
                    "reason": "Momentum building"
                }
            ]
        }
        
        assets = self.orch._parse_scan_results(scan_results)
        
        self.assertEqual(len(assets), 2)
        self.assertEqual(assets[0]["symbol"], "SPY")
        self.assertEqual(assets[0]["priority"], 5)
        self.assertEqual(assets[1]["symbol"], "QQQ")
    
    def test_parse_empty_results(self):
        """Test parsing empty scanner results."""
        scan_results = {"top_assets": []}
        
        assets = self.orch._parse_scan_results(scan_results)
        
        self.assertEqual(assets, [])
    
    def test_parse_missing_top_assets(self):
        """Test parsing results without top_assets key."""
        scan_results = {"other_data": "value"}
        
        assets = self.orch._parse_scan_results(scan_results)
        
        self.assertEqual(assets, [])
    
    def test_parse_malformed_results(self):
        """Test parsing malformed scanner results returns empty list."""
        scan_results = None
        
        assets = self.orch._parse_scan_results(scan_results)
        
        self.assertEqual(assets, [])


class TestLogCycleSummary(unittest.TestCase):
    """Test cycle summary logging."""
    
    def setUp(self):
        self.orch = TradingOrchestrator()
    
    @patch('src.crew.orchestrator.logger')
    def test_log_all_successes(self, mock_logger):
        """Test logging with all successful crew executions."""
        results = [
            {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "BUY executed"},
            {"success": True, "symbol": "QQQ", "strategy": "macd", "result": "HOLD"}
        ]
        
        self.orch.log_cycle_summary(results)
        
        # Verify summary log
        mock_logger.info.assert_any_call("Cycle complete: 2 succeeded, 0 failed out of 2 total")
    
    @patch('src.crew.orchestrator.logger')
    def test_log_all_failures(self, mock_logger):
        """Test logging with all failed crew executions."""
        results = [
            {"success": False, "symbol": "AAPL", "strategy": "rsi_breakout", "error": "API error"},
            {"success": False, "symbol": "MSFT", "strategy": "bollinger", "error": "Rate limit"}
        ]
        
        self.orch.log_cycle_summary(results)
        
        # Verify summary log
        mock_logger.info.assert_any_call("Cycle complete: 0 succeeded, 2 failed out of 2 total")
    
    @patch('src.crew.orchestrator.logger')
    def test_log_mixed_results(self, mock_logger):
        """Test logging with mixed success/failure results."""
        results = [
            {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "BUY"},
            {"success": False, "symbol": "QQQ", "strategy": "macd", "error": "Timeout"},
            {"success": True, "symbol": "IWM", "strategy": "rsi_breakout", "result": "SELL"}
        ]
        
        self.orch.log_cycle_summary(results)
        
        # Verify summary log
        mock_logger.info.assert_any_call("Cycle complete: 2 succeeded, 1 failed out of 3 total")
    
    @patch('src.crew.orchestrator.logger')
    def test_log_empty_results(self, mock_logger):
        """Test logging with no results."""
        results = []
        
        self.orch.log_cycle_summary(results)
        
        # Verify summary log
        mock_logger.info.assert_any_call("Cycle complete: 0 succeeded, 0 failed out of 0 total")


class TestRunCycle(unittest.TestCase):
    """Test complete trading cycle execution."""
    
    def setUp(self):
        self.orch = TradingOrchestrator()
    
    @patch('src.crew.orchestrator.TradingOrchestrator.log_cycle_summary')
    @patch('src.crew.orchestrator.TradingOrchestrator._run_trading_crew')
    @patch('src.crew.orchestrator.time.sleep')
    def test_run_cycle_with_top_assets(self, mock_sleep, mock_run_crew, mock_log_summary):
        """Test complete cycle with market scanner returning top assets."""
        # Mock market scanner results
        self.orch.market_scanner = Mock()
        self.orch.market_scanner.run.return_value = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "recommended_strategies": ["3ma", "rsi_breakout"]
                },
                {
                    "symbol": "QQQ",
                    "priority": 4,
                    "recommended_strategies": ["macd"]
                }
            ]
        }
        
        # Mock trading crew results
        mock_run_crew.return_value = {"success": True, "symbol": "SPY", "strategy": "3ma", "result": "BUY"}
        
        self.orch.run_cycle()
        
        # Verify market scanner was called
        self.orch.market_scanner.run.assert_called_once()
        
        # Verify trading crews were submitted (3 total: SPY-3ma, SPY-rsi, QQQ-macd)
        self.assertEqual(mock_run_crew.call_count, 3)
        
        # Verify summary was logged
        mock_log_summary.assert_called_once()
    
    @patch('src.crew.orchestrator.TradingOrchestrator.log_cycle_summary')
    def test_run_cycle_with_no_assets(self, mock_log_summary):
        """Test cycle exits gracefully when scanner returns no assets."""
        # Mock market scanner with no results
        self.orch.market_scanner = Mock()
        self.orch.market_scanner.run.return_value = {"top_assets": []}
        
        self.orch.run_cycle()
        
        # Verify market scanner was called
        self.orch.market_scanner.run.assert_called_once()
        
        # Verify summary was NOT called (early exit)
        mock_log_summary.assert_not_called()
    
    @patch('src.crew.orchestrator.TradingOrchestrator.log_cycle_summary')
    @patch('src.crew.orchestrator.TradingOrchestrator._run_trading_crew')
    @patch('src.crew.orchestrator.time.sleep')
    def test_run_cycle_limits_to_top_3_assets(self, mock_sleep, mock_run_crew, mock_log_summary):
        """Test cycle only processes top 3 assets even if more are available."""
        # Mock market scanner with 5 assets
        self.orch.market_scanner = Mock()
        self.orch.market_scanner.run.return_value = {
            "top_assets": [
                {"symbol": "SPY", "priority": 5, "recommended_strategies": ["3ma"]},
                {"symbol": "QQQ", "priority": 4, "recommended_strategies": ["macd"]},
                {"symbol": "IWM", "priority": 3, "recommended_strategies": ["rsi_breakout"]},
                {"symbol": "DIA", "priority": 2, "recommended_strategies": ["bollinger"]},
                {"symbol": "EFA", "priority": 1, "recommended_strategies": ["3ma"]}
            ]
        }
        
        mock_run_crew.return_value = {"success": True}
        
        self.orch.run_cycle()
        
        # Verify only 3 crews were submitted (top 3 assets)
        self.assertEqual(mock_run_crew.call_count, 3)
        
        # Verify the top 3 symbols were used
        call_symbols = [call.kwargs["symbol"] for call in mock_run_crew.call_args_list]
        self.assertIn("SPY", call_symbols)
        self.assertIn("QQQ", call_symbols)
        self.assertIn("IWM", call_symbols)
        self.assertNotIn("DIA", call_symbols)
        self.assertNotIn("EFA", call_symbols)
    
    @patch('src.crew.orchestrator.TradingOrchestrator.log_cycle_summary')
    @patch('src.crew.orchestrator.TradingOrchestrator._run_trading_crew')
    @patch('src.crew.orchestrator.time.sleep')
    def test_run_cycle_staggered_submission(self, mock_sleep, mock_run_crew, mock_log_summary):
        """Test cycle staggers crew submissions with delays."""
        # Mock market scanner with 2 assets, each with 1 strategy (2 crews total)
        self.orch.market_scanner = Mock()
        self.orch.market_scanner.run.return_value = {
            "top_assets": [
                {"symbol": "SPY", "priority": 5, "recommended_strategies": ["3ma"]},
                {"symbol": "QQQ", "priority": 4, "recommended_strategies": ["macd"]}
            ]
        }
        
        mock_run_crew.return_value = {"success": True}
        
        self.orch.run_cycle()
        
        # Verify sleep was called between submissions (2 crews = 1 sleep call)
        self.assertEqual(mock_sleep.call_count, 1)
        mock_sleep.assert_called_with(2)
    
    @patch('src.crew.orchestrator.TradingOrchestrator.log_cycle_summary')
    @patch('src.crew.orchestrator.TradingOrchestrator._run_trading_crew')
    @patch('src.crew.orchestrator.time.sleep')
    def test_run_cycle_with_multiple_strategies_per_asset(self, mock_sleep, mock_run_crew, mock_log_summary):
        """Test cycle handles assets with multiple recommended strategies."""
        # Mock market scanner with 1 asset having 3 strategies
        self.orch.market_scanner = Mock()
        self.orch.market_scanner.run.return_value = {
            "top_assets": [
                {
                    "symbol": "SPY",
                    "priority": 5,
                    "recommended_strategies": ["3ma", "rsi_breakout", "macd"]
                }
            ]
        }
        
        mock_run_crew.return_value = {"success": True}
        
        self.orch.run_cycle()
        
        # Verify 3 crews were submitted (1 asset x 3 strategies)
        self.assertEqual(mock_run_crew.call_count, 3)
        
        # Verify all strategies were used
        call_strategies = [call.kwargs["strategy"] for call in mock_run_crew.call_args_list]
        self.assertIn("3ma", call_strategies)
        self.assertIn("rsi_breakout", call_strategies)
        self.assertIn("macd", call_strategies)


if __name__ == "__main__":
    unittest.main()
