"""
Test script for Feature 2.5: Asset-Class-Aware Strategies
Tests strategy parameter adaptation for CRYPTO vs US_EQUITY
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.registry import get_strategy
from src.strategies.triple_ma import TripleMovingAverageStrategy
from src.strategies.rsi_breakout import RSIBreakoutStrategy
from src.strategies.macd_crossover import MACDCrossoverStrategy
from src.strategies.bollinger_bands_reversal import BollingerBandsReversalStrategy
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_strategy_instantiation():
    """Test that strategies can be instantiated with asset_class parameter."""
    print("\n" + "=" * 80)
    print("TEST 1: Strategy Instantiation with Asset Class")
    print("=" * 80)

    strategies = ["3ma", "rsi_breakout", "macd", "bollinger"]
    asset_classes = ["US_EQUITY", "CRYPTO", "FOREX"]

    for strategy_name in strategies:
        print(f"\n{strategy_name}:")
        for asset_class in asset_classes:
            strategy = get_strategy(strategy_name, asset_class)
            print(f"  {asset_class}: ✅ Instantiated")
            assert strategy.asset_class == asset_class, f"Asset class not set correctly"
            assert hasattr(strategy, "params"), "Parameters not initialized"

    print("\n✅ PASS: All strategies instantiate with asset classes")


def test_parameter_differences():
    """Test that CRYPTO has different parameters than US_EQUITY."""
    print("\n" + "=" * 80)
    print("TEST 2: Parameter Differences (CRYPTO vs US_EQUITY)")
    print("=" * 80)

    strategies = ["3ma", "rsi_breakout", "macd", "bollinger"]

    for strategy_name in strategies:
        equity_strategy = get_strategy(strategy_name, "US_EQUITY")
        crypto_strategy = get_strategy(strategy_name, "CRYPTO")

        print(f"\n{strategy_name}:")
        print(f"  US_EQUITY params: {equity_strategy.params}")
        print(f"  CRYPTO params:    {crypto_strategy.params}")

        # Check specific differences
        assert (
            crypto_strategy.params["atr_multiplier"] > equity_strategy.params["atr_multiplier"]
        ), "CRYPTO should have wider stops"
        assert (
            crypto_strategy.params["volume_weight"] < equity_strategy.params["volume_weight"]
        ), "CRYPTO should have less volume weight"
        assert (
            crypto_strategy.params["atr_period"] >= equity_strategy.params["atr_period"]
        ), "CRYPTO should have equal or longer ATR period"

        print(
            f"  ✅ CRYPTO has wider stops: {crypto_strategy.params['atr_multiplier']} vs {equity_strategy.params['atr_multiplier']}"
        )
        print(
            f"  ✅ CRYPTO has less volume weight: {crypto_strategy.params['volume_weight']} vs {equity_strategy.params['volume_weight']}"
        )
        print(
            f"  ✅ CRYPTO has longer ATR period: {crypto_strategy.params['atr_period']} vs {equity_strategy.params['atr_period']}"
        )

    print("\n✅ PASS: CRYPTO parameters properly adapted")


def test_base_strategy_defaults():
    """Test that base strategy provides sensible defaults."""
    print("\n" + "=" * 80)
    print("TEST 3: Base Strategy Default Parameters")
    print("=" * 80)

    # Test US_EQUITY defaults
    equity_strategy = TripleMovingAverageStrategy("US_EQUITY")
    print(f"\nUS_EQUITY defaults:")
    print(f"  ATR Multiplier: {equity_strategy.params['atr_multiplier']}")
    print(f"  Volume Weight: {equity_strategy.params['volume_weight']}")
    print(f"  ATR Period: {equity_strategy.params['atr_period']}")
    print(f"  ADX Threshold: {equity_strategy.params['adx_threshold']}")
    print(f"  Min Confidence: {equity_strategy.params['min_confidence']}")

    assert equity_strategy.params["atr_multiplier"] == 2.0, "Default ATR multiplier should be 2.0"
    assert equity_strategy.params["volume_weight"] == 0.15, "Default volume weight should be 0.15"
    assert equity_strategy.params["atr_period"] == 14, "Default ATR period should be 14"

    # Test CRYPTO adjustments
    crypto_strategy = TripleMovingAverageStrategy("CRYPTO")
    print(f"\nCRYPTO adjustments:")
    print(f"  ATR Multiplier: {crypto_strategy.params['atr_multiplier']}")
    print(f"  Volume Weight: {crypto_strategy.params['volume_weight']}")
    print(f"  ATR Period: {crypto_strategy.params['atr_period']}")
    print(f"  ADX Threshold: {crypto_strategy.params['adx_threshold']}")
    print(f"  Min Confidence: {crypto_strategy.params['min_confidence']}")

    assert crypto_strategy.params["atr_multiplier"] == 3.0, "CRYPTO ATR multiplier should be 3.0"
    assert crypto_strategy.params["volume_weight"] == 0.05, "CRYPTO volume weight should be 0.05"
    assert crypto_strategy.params["atr_period"] == 20, "CRYPTO ATR period should be 20"

    # Test FOREX adjustments
    forex_strategy = TripleMovingAverageStrategy("FOREX")
    print(f"\nFOREX adjustments:")
    print(f"  ATR Multiplier: {forex_strategy.params['atr_multiplier']}")
    print(f"  Volume Weight: {forex_strategy.params['volume_weight']}")
    print(f"  ATR Period: {forex_strategy.params['atr_period']}")

    assert forex_strategy.params["volume_weight"] == 0.0, "FOREX volume weight should be 0.0"

    print("\n✅ PASS: Default parameters working correctly")


def test_registry_with_asset_class():
    """Test that registry properly passes asset_class to strategies."""
    print("\n" + "=" * 80)
    print("TEST 4: Registry Asset Class Propagation")
    print("=" * 80)

    # Test with explicit asset_class
    crypto_strategy = get_strategy("3ma", "CRYPTO")
    print(f"\nget_strategy('3ma', 'CRYPTO'):")
    print(f"  Asset class: {crypto_strategy.asset_class}")
    print(f"  ATR multiplier: {crypto_strategy.params['atr_multiplier']}")
    assert crypto_strategy.asset_class == "CRYPTO", "Asset class not propagated"
    assert crypto_strategy.params["atr_multiplier"] == 3.0, "CRYPTO params not applied"
    print("  ✅ CRYPTO parameters applied")

    # Test with None (default to US_EQUITY)
    default_strategy = get_strategy("3ma")
    print(f"\nget_strategy('3ma'):")
    print(f"  Asset class: {default_strategy.asset_class}")
    print(f"  ATR multiplier: {default_strategy.params['atr_multiplier']}")
    assert default_strategy.asset_class == "US_EQUITY", "Should default to US_EQUITY"
    assert default_strategy.params["atr_multiplier"] == 2.0, "US_EQUITY params not applied"
    print("  ✅ Defaults to US_EQUITY")

    print("\n✅ PASS: Registry correctly propagates asset_class")


def test_all_strategies_have_asset_class():
    """Test that all 4 strategies support asset_class parameter."""
    print("\n" + "=" * 80)
    print("TEST 5: All Strategies Support Asset Class")
    print("=" * 80)

    strategy_classes = [
        ("3ma", TripleMovingAverageStrategy),
        ("rsi_breakout", RSIBreakoutStrategy),
        ("macd", MACDCrossoverStrategy),
        ("bollinger", BollingerBandsReversalStrategy),
    ]

    for name, strategy_class in strategy_classes:
        print(f"\n{name} ({strategy_class.__name__}):")

        # Test instantiation with asset_class
        equity = strategy_class("US_EQUITY")
        crypto = strategy_class("CRYPTO")
        forex = strategy_class("FOREX")

        print(f"  US_EQUITY: {equity.asset_class} ✅")
        print(f"  CRYPTO: {crypto.asset_class} ✅")
        print(f"  FOREX: {forex.asset_class} ✅")

        # Verify they have different params
        assert equity.params != crypto.params, "Equity and Crypto should have different params"
        print(f"  Parameter adaptation: ✅")

    print("\n✅ PASS: All 4 strategies support asset_class")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("FEATURE 2.5 VALIDATION: Asset-Class-Aware Strategies")
    print("=" * 80)

    try:
        # Test 1: Instantiation
        test_strategy_instantiation()

        # Test 2: Parameter differences
        test_parameter_differences()

        # Test 3: Base strategy defaults
        test_base_strategy_defaults()

        # Test 4: Registry integration
        test_registry_with_asset_class()

        # Test 5: All strategies support asset_class
        test_all_strategies_have_asset_class()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature 2.5 Implementation Validated")
        print("=" * 80)
        print("\nAsset-Class-Aware Strategy Features:")
        print("  ✅ All 4 strategies support asset_class parameter")
        print("  ✅ CRYPTO has wider stops (3.0x vs 2.0x ATR)")
        print("  ✅ CRYPTO has less volume weight (0.05 vs 0.15)")
        print("  ✅ CRYPTO has longer ATR period (20 vs 14)")
        print("  ✅ FOREX has no volume weight (0.0)")
        print("  ✅ Registry properly propagates asset_class")
        print("  ✅ Base strategy provides sensible defaults")
        print("\nReady for backtesting validation")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
