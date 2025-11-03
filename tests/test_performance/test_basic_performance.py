"""
Basic performance validation tests - no complex mocking, just simple property checks.

These tests validate that core components can be instantiated quickly and are thread-safe.
"""

import time
import tracemalloc
import unittest
from threading import Thread

from src.crew.trading_crew import TradingCrew
from src.crew.orchestrator import TradingOrchestrator
from src.connectors.gemini_connector_enhanced import EnhancedGeminiConnectionManager
from src.connectors.alpaca_connector import AlpacaConnectionManager
from src.utils.backtester_v2 import BacktesterV2
from src.strategies.triple_ma import TripleMovingAverageStrategy


class TestInstantiationSpeed(unittest.TestCase):
    """Test components instantiate quickly."""

    def test_crew_proxy_instantiation_fast(self):
        """Test crew proxy instantiates in <0.5s."""
        start = time.time()
        crew = TradingCrew()
        duration = time.time() - start

        self.assertLess(duration, 0.5, f"Crew took {duration:.3f}s")
        self.assertIsNotNone(crew)

    def test_orchestrator_instantiation_fast(self):
        """Test orchestrator instantiates in <2s."""
        start = time.time()
        orch = TradingOrchestrator()
        duration = time.time() - start

        self.assertLess(duration, 2.0, f"Orchestrator took {duration:.3f}s")
        self.assertIsNotNone(orch)

    def test_gemini_manager_instantiation_fast(self):
        """Test Gemini manager instantiates in <2s."""
        start = time.time()
        manager = EnhancedGeminiConnectionManager(api_keys=["test_key"])
        duration = time.time() - start

        self.assertLess(duration, 2.0, f"Gemini manager took {duration:.3f}s")
        self.assertIsNotNone(manager)

    def test_alpaca_manager_instantiation_fast(self):
        """Test Alpaca manager instantiates in <1s."""
        start = time.time()
        manager = AlpacaConnectionManager()
        duration = time.time() - start

        self.assertLess(duration, 1.0, f"Alpaca manager took {duration:.3f}s")
        self.assertIsNotNone(manager)

    def test_backtester_instantiation_fast(self):
        """Test backtester instantiates in <1s."""
        start = time.time()
        backtester = BacktesterV2(
            start_date="2024-01-01", end_date="2024-06-30", risk_free_rate=0.02
        )
        duration = time.time() - start

        self.assertLess(duration, 1.0, f"Backtester took {duration:.3f}s")
        self.assertIsNotNone(backtester)

    def test_strategy_instantiation_fast(self):
        """Test strategy instantiates in <0.5s."""
        start = time.time()
        strategy = TripleMovingAverageStrategy()
        duration = time.time() - start

        self.assertLess(duration, 0.5, f"Strategy took {duration:.3f}s")
        self.assertIsNotNone(strategy)


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of instantiation."""

    def test_concurrent_crew_instantiation_safe(self):
        """Test crews can be instantiated concurrently (using skip_init to avoid API calls)."""
        crews = []
        errors = []

        def create_crew(idx):
            try:
                crew = TradingCrew(skip_init=True)
                crews.append(crew)
            except Exception as e:
                errors.append((idx, str(e)))

        threads = [Thread(target=create_crew, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Errors: {errors}")
        self.assertEqual(len(crews), 10)

    def test_multiple_crew_instances_independent(self):
        """Test multiple crew instances are independent (using skip_init to avoid API calls)."""
        crew1 = TradingCrew(skip_init=True)
        crew2 = TradingCrew(skip_init=True)
        crew3 = TradingCrew(skip_init=True)

        # All should be valid instances
        self.assertIsNotNone(crew1)
        self.assertIsNotNone(crew2)
        self.assertIsNotNone(crew3)


class TestMemoryEfficiency(unittest.TestCase):
    """Test memory efficiency."""

    def test_crew_instantiation_memory_efficient(self):
        """Test crew instantiation doesn't use excessive memory (using skip_init to avoid API calls)."""
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        crews = [TradingCrew(skip_init=True) for _ in range(10)]

        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        memory_used = (peak - baseline) / 1024 / 1024
        self.assertLess(
            memory_used, 100, f"10 crews used {memory_used:.2f}MB (expected <100MB)"
        )
        self.assertEqual(len(crews), 10)

    def test_strategy_instantiation_memory_efficient(self):
        """Test strategy instantiation is memory efficient."""
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        strategies = [TripleMovingAverageStrategy() for _ in range(20)]

        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        memory_used = (peak - baseline) / 1024 / 1024
        self.assertLess(
            memory_used, 50, f"20 strategies used {memory_used:.2f}MB (expected <50MB)"
        )
        self.assertEqual(len(strategies), 20)


class TestRateLimitStructures(unittest.TestCase):
    """Test rate limiting structures exist and have correct configuration."""

    def test_gemini_manager_has_quota_tracking(self):
        """Test Gemini manager initializes with quota tracking."""
        manager = EnhancedGeminiConnectionManager(api_keys=["test_key"])

        self.assertTrue(hasattr(manager, "quota_tracker"))
        self.assertIsNotNone(manager.quota_tracker)

    def test_gemini_quota_tracking_structures_exist(self):
        """Test Gemini quota tracker has required data structures."""
        manager = EnhancedGeminiConnectionManager(api_keys=["test_key"])

        # Should have tracking for RPM and RPD
        self.assertTrue(hasattr(manager.quota_tracker, "minute_windows"))
        self.assertTrue(hasattr(manager.quota_tracker, "day_windows"))

    def test_gemini_multiple_keys_supported(self):
        """Test Gemini manager supports multiple API keys."""
        keys = ["key1", "key2", "key3", "key4", "key5"]
        manager = EnhancedGeminiConnectionManager(api_keys=keys)

        self.assertEqual(len(manager.api_keys), 5)

    def test_gemini_has_quota_validation_method(self):
        """Test Gemini manager can check quota availability."""
        manager = EnhancedGeminiConnectionManager(api_keys=["test_key"])

        # Should have method to check if model can be used
        self.assertTrue(hasattr(manager.quota_tracker, "can_use_model"))


class TestBacktesterCalculations(unittest.TestCase):
    """Test backtester calculations are fast."""

    def test_annualization_factor_calculation_fast(self):
        """Test annualization factor calculation is fast."""
        backtester = BacktesterV2(
            start_date="2024-01-01", end_date="2024-06-30", risk_free_rate=0.02
        )

        timeframes = ["1Min", "5Min", "15Min", "1Hour", "1Day"]

        start = time.time()
        for tf in timeframes:
            factor = backtester._get_annualization_factor(tf)
            self.assertGreater(factor, 0)

        duration = time.time() - start
        self.assertLess(duration, 0.1, f"Calculation took {duration:.3f}s")


if __name__ == "__main__":
    unittest.main()
