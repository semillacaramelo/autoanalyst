"""
Tests for Trading Crew - 4-Agent Trading Workflow

This module tests the complete 4-agent trading workflow including
data collection, signal generation, risk management, and execution.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading

from src.crew.trading_crew import (
    TradingCrew,
    get_trading_crew,
    _TradingCrewProxy,
    trading_crew,
)


class TestTradingCrew(unittest.TestCase):
    """Test TradingCrew functionality."""

    @patch("src.crew.trading_crew.enhanced_gemini_manager")
    @patch("src.crew.trading_crew.TradingAgents")
    @patch("src.crew.trading_crew.TradingTasks")
    @patch("src.crew.trading_crew.Crew")
    @patch("src.crew.trading_crew.LLM")
    def test_initialization_success(
        self,
        mock_llm_class,
        mock_crew_class,
        mock_tasks_class,
        mock_agents_class,
        mock_gemini_manager,
    ):
        """Test successful TradingCrew initialization."""
        # Mock Gemini manager
        mock_gemini_manager.get_llm_for_crewai.return_value = (
            "gemini/flash",
            "test-api-key",
        )

        # Mock LLM
        mock_llm_instance = Mock()
        mock_llm_class.return_value = mock_llm_instance

        # Mock agents
        mock_agents_instance = Mock()
        mock_agents_instance.data_collector_agent.return_value = Mock()
        mock_agents_instance.signal_generator_agent.return_value = Mock()
        mock_agents_instance.risk_manager_agent.return_value = Mock()
        mock_agents_instance.execution_agent.return_value = Mock()
        mock_agents_class.return_value = mock_agents_instance

        # Mock tasks
        mock_tasks_instance = Mock()
        mock_tasks_instance.collect_data_task.return_value = Mock()
        mock_tasks_instance.generate_signal_task.return_value = Mock()
        mock_tasks_instance.assess_risk_task.return_value = Mock()
        mock_tasks_instance.execute_trade_task.return_value = Mock()
        mock_tasks_class.return_value = mock_tasks_instance

        # Mock Crew
        mock_crew_instance = Mock()
        mock_crew_class.return_value = mock_crew_instance

        # Initialize
        crew = TradingCrew()

        # Verify initialization
        self.assertIsNotNone(crew.crew)
        mock_gemini_manager.get_llm_for_crewai.assert_called_once()
        mock_llm_class.assert_called_once_with(
            model="gemini/flash", api_key="test-api-key"
        )

    def test_initialization_skip_init(self):
        """Test TradingCrew initialization with skip_init=True."""
        crew = TradingCrew(skip_init=True)

        self.assertIsNone(crew.crew)

    @patch("src.crew.trading_crew.enhanced_gemini_manager")
    @patch("src.crew.trading_crew.TradingAgents")
    @patch("src.crew.trading_crew.TradingTasks")
    @patch("src.crew.trading_crew.Crew")
    @patch("src.crew.trading_crew.LLM")
    @patch("src.crew.trading_crew.settings")
    def test_run_success(
        self,
        mock_settings,
        mock_llm_class,
        mock_crew_class,
        mock_tasks_class,
        mock_agents_class,
        mock_gemini_manager,
    ):
        """Test successful crew execution."""
        # Mock settings
        mock_settings.trading_symbol = "SPY"
        mock_settings.max_open_positions = 3
        mock_settings.max_risk_per_trade = 0.02
        mock_settings.daily_loss_limit = 0.05
        mock_settings.dry_run = True

        # Mock Gemini manager
        mock_gemini_manager.get_llm_for_crewai.return_value = (
            "gemini/flash",
            "test-api-key",
        )

        # Mock LLM
        mock_llm_instance = Mock()
        mock_llm_class.return_value = mock_llm_instance

        # Mock agents
        mock_agents_instance = Mock()
        mock_agents_instance.data_collector_agent.return_value = Mock()
        mock_agents_instance.signal_generator_agent.return_value = Mock()
        mock_agents_instance.risk_manager_agent.return_value = Mock()
        mock_agents_instance.execution_agent.return_value = Mock()
        mock_agents_class.return_value = mock_agents_instance

        # Mock tasks
        mock_tasks_instance = Mock()
        mock_tasks_instance.collect_data_task.return_value = Mock()
        mock_tasks_instance.generate_signal_task.return_value = Mock()
        mock_tasks_instance.assess_risk_task.return_value = Mock()
        mock_tasks_instance.execute_trade_task.return_value = Mock()
        mock_tasks_class.return_value = mock_tasks_instance

        # Mock Crew with kickoff result
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = "Trading completed: HOLD signal"
        mock_crew_class.return_value = mock_crew_instance

        # Initialize and run
        crew = TradingCrew()
        result = crew.run(symbol="AAPL", strategy="3ma", timeframe="1Min", limit=100)

        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["strategy"], "3ma")
        self.assertIn("result", result)
        self.assertIn("configuration", result)

        # Verify crew was kicked off with correct inputs
        mock_crew_instance.kickoff.assert_called_once()
        call_args = mock_crew_instance.kickoff.call_args
        inputs = call_args.kwargs["inputs"]
        self.assertEqual(inputs["symbol"], "AAPL")
        self.assertEqual(inputs["strategy_name"], "3ma")
        self.assertEqual(inputs["timeframe"], "1Min")
        self.assertEqual(inputs["limit"], 100)

    @patch("src.crew.trading_crew.enhanced_gemini_manager")
    @patch("src.crew.trading_crew.TradingAgents")
    @patch("src.crew.trading_crew.TradingTasks")
    @patch("src.crew.trading_crew.Crew")
    @patch("src.crew.trading_crew.LLM")
    @patch("src.crew.trading_crew.settings")
    def test_run_with_default_symbol(
        self,
        mock_settings,
        mock_llm_class,
        mock_crew_class,
        mock_tasks_class,
        mock_agents_class,
        mock_gemini_manager,
    ):
        """Test crew execution with default symbol from settings."""
        # Mock settings
        mock_settings.trading_symbol = "SPY"
        mock_settings.max_open_positions = 3
        mock_settings.max_risk_per_trade = 0.02
        mock_settings.daily_loss_limit = 0.05
        mock_settings.dry_run = True

        # Mock Gemini manager
        mock_gemini_manager.get_llm_for_crewai.return_value = (
            "gemini/flash",
            "test-api-key",
        )

        # Mock LLM
        mock_llm_instance = Mock()
        mock_llm_class.return_value = mock_llm_instance

        # Mock agents
        mock_agents_instance = Mock()
        mock_agents_instance.data_collector_agent.return_value = Mock()
        mock_agents_instance.signal_generator_agent.return_value = Mock()
        mock_agents_instance.risk_manager_agent.return_value = Mock()
        mock_agents_instance.execution_agent.return_value = Mock()
        mock_agents_class.return_value = mock_agents_instance

        # Mock tasks
        mock_tasks_instance = Mock()
        mock_tasks_instance.collect_data_task.return_value = Mock()
        mock_tasks_instance.generate_signal_task.return_value = Mock()
        mock_tasks_instance.assess_risk_task.return_value = Mock()
        mock_tasks_instance.execute_trade_task.return_value = Mock()
        mock_tasks_class.return_value = mock_tasks_instance

        # Mock Crew
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = "Trading completed"
        mock_crew_class.return_value = mock_crew_instance

        # Initialize and run without symbol (should use default)
        crew = TradingCrew()
        result = crew.run(symbol=None, strategy="macd")

        # Verify default symbol was used
        mock_crew_instance.kickoff.assert_called_once()
        call_args = mock_crew_instance.kickoff.call_args
        inputs = call_args.kwargs["inputs"]
        self.assertEqual(inputs["symbol"], "SPY")

    @patch("src.crew.trading_crew.enhanced_gemini_manager")
    @patch("src.crew.trading_crew.TradingAgents")
    @patch("src.crew.trading_crew.TradingTasks")
    @patch("src.crew.trading_crew.Crew")
    @patch("src.crew.trading_crew.LLM")
    def test_run_failure(
        self,
        mock_llm_class,
        mock_crew_class,
        mock_tasks_class,
        mock_agents_class,
        mock_gemini_manager,
    ):
        """Test crew execution with error."""
        # Mock Gemini manager
        mock_gemini_manager.get_llm_for_crewai.return_value = (
            "gemini/flash",
            "test-api-key",
        )

        # Mock LLM
        mock_llm_instance = Mock()
        mock_llm_class.return_value = mock_llm_instance

        # Mock agents
        mock_agents_instance = Mock()
        mock_agents_instance.data_collector_agent.return_value = Mock()
        mock_agents_instance.signal_generator_agent.return_value = Mock()
        mock_agents_instance.risk_manager_agent.return_value = Mock()
        mock_agents_instance.execution_agent.return_value = Mock()
        mock_agents_class.return_value = mock_agents_instance

        # Mock tasks
        mock_tasks_instance = Mock()
        mock_tasks_instance.collect_data_task.return_value = Mock()
        mock_tasks_instance.generate_signal_task.return_value = Mock()
        mock_tasks_instance.assess_risk_task.return_value = Mock()
        mock_tasks_instance.execute_trade_task.return_value = Mock()
        mock_tasks_class.return_value = mock_tasks_instance

        # Mock Crew to raise exception
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.side_effect = Exception("Test error")
        mock_crew_class.return_value = mock_crew_instance

        # Initialize and run
        crew = TradingCrew()
        result = crew.run(symbol="AAPL", strategy="3ma")

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["strategy"], "3ma")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")

    def test_run_with_skip_init_raises_error(self):
        """Test that running crew with skip_init=True raises error."""
        crew = TradingCrew(skip_init=True)

        with self.assertRaises(RuntimeError) as context:
            crew.run(symbol="SPY", strategy="3ma")

        self.assertIn("skip_init=True", str(context.exception))


class TestGetTradingCrew(unittest.TestCase):
    """Test get_trading_crew lazy initialization."""

    def tearDown(self):
        """Clean up global instance after each test."""
        import src.crew.trading_crew as module

        module._trading_crew_instance = None

    @patch("src.crew.trading_crew.TradingCrew")
    def test_get_trading_crew_creates_instance(self, mock_trading_crew_class):
        """Test that get_trading_crew creates instance on first call."""
        mock_instance = Mock()
        mock_trading_crew_class.return_value = mock_instance

        # First call should create instance
        result = get_trading_crew()

        self.assertEqual(result, mock_instance)
        mock_trading_crew_class.assert_called_once()

    @patch("src.crew.trading_crew.TradingCrew")
    def test_get_trading_crew_reuses_instance(self, mock_trading_crew_class):
        """Test that get_trading_crew reuses instance on subsequent calls."""
        mock_instance = Mock()
        mock_trading_crew_class.return_value = mock_instance

        # First call
        result1 = get_trading_crew()

        # Second call should return same instance
        result2 = get_trading_crew()

        self.assertEqual(result1, result2)
        # Should only be called once
        mock_trading_crew_class.assert_called_once()


class TestTradingCrewProxy(unittest.TestCase):
    """Test _TradingCrewProxy lazy initialization."""

    def tearDown(self):
        """Clean up global instance after each test."""
        import src.crew.trading_crew as module

        module._trading_crew_instance = None

    @patch("src.crew.trading_crew.TradingCrew")
    def test_proxy_run_method(self, mock_trading_crew_class):
        """Test that proxy.run() works correctly."""
        # Mock TradingCrew instance
        mock_instance = Mock()
        mock_instance.run.return_value = {"success": True, "result": "HOLD"}
        mock_trading_crew_class.return_value = mock_instance

        # Call via proxy
        proxy = _TradingCrewProxy()
        result = proxy.run(symbol="SPY", strategy="3ma")

        # Verify
        self.assertEqual(result["success"], True)
        mock_instance.run.assert_called_once_with(symbol="SPY", strategy="3ma")

    def test_proxy_other_attributes_raise_error(self):
        """Test that accessing other attributes raises AttributeError."""
        proxy = _TradingCrewProxy()

        with self.assertRaises(AttributeError) as context:
            _ = proxy.some_other_method

        self.assertIn("only supports the 'run' method", str(context.exception))

    def test_global_trading_crew_is_proxy(self):
        """Test that global trading_crew is a proxy instance."""
        self.assertIsInstance(trading_crew, _TradingCrewProxy)


class TestTradingCrewThreadSafety(unittest.TestCase):
    """Test thread safety of get_trading_crew."""

    def tearDown(self):
        """Clean up global instance after each test."""
        import src.crew.trading_crew as module

        module._trading_crew_instance = None

    @patch("src.crew.trading_crew.TradingCrew")
    def test_concurrent_get_trading_crew(self, mock_trading_crew_class):
        """Test that concurrent calls to get_trading_crew are thread-safe."""
        mock_instance = Mock()
        mock_trading_crew_class.return_value = mock_instance

        results = []
        threads = []

        def get_crew():
            result = get_trading_crew()
            results.append(result)

        # Create multiple threads
        for _ in range(5):
            thread = threading.Thread(target=get_crew)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all threads got the same instance
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result, mock_instance)

        # Verify TradingCrew was only instantiated once
        mock_trading_crew_class.assert_called_once()


if __name__ == "__main__":
    unittest.main()
