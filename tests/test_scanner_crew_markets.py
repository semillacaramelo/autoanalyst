"""
Quick end-to-end test for MarketScannerCrew with crypto
Tests instantiation and agent configuration only (no full crew run)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crew.market_scanner_crew import MarketScannerCrew
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_market_scanner_instantiation():
    """Test MarketScannerCrew instantiation with different markets."""
    print("\n" + "=" * 80)
    print("TEST: MarketScannerCrew Instantiation")
    print("=" * 80)

    # Test 1: Auto-detect (should choose CRYPTO since market closed)
    print("\n1. Auto-detect market:")
    crew_auto = MarketScannerCrew()
    print(f"   Target market: {crew_auto.target_market}")
    assert crew_auto.target_market in ["US_EQUITY", "CRYPTO"], "Invalid auto-detected market"
    assert crew_auto.volatility_analyzer is not None, "Volatility analyzer not initialized"
    assert crew_auto.technical_analyzer is not None, "Technical analyzer not initialized"
    assert crew_auto.liquidity_filter is not None, "Liquidity filter not initialized"
    assert crew_auto.chief_analyst is not None, "Chief analyst not initialized"
    print("   ✅ All agents initialized")

    # Test 2: Explicit CRYPTO market
    print("\n2. Explicit CRYPTO market:")
    crew_crypto = MarketScannerCrew(target_market="CRYPTO")
    print(f"   Target market: {crew_crypto.target_market}")
    assert crew_crypto.target_market == "CRYPTO", "CRYPTO market not set"
    assert crew_crypto.volatility_analyzer is not None, "Volatility analyzer not initialized"
    print("   ✅ Crypto market scanner initialized")

    # Test 3: Explicit US_EQUITY market
    print("\n3. Explicit US_EQUITY market:")
    crew_equity = MarketScannerCrew(target_market="US_EQUITY")
    print(f"   Target market: {crew_equity.target_market}")
    assert crew_equity.target_market == "US_EQUITY", "US_EQUITY market not set"
    assert crew_equity.volatility_analyzer is not None, "Volatility analyzer not initialized"
    print("   ✅ Equity market scanner initialized")

    # Test 4: Explicit FOREX market
    print("\n4. Explicit FOREX market:")
    crew_forex = MarketScannerCrew(target_market="FOREX")
    print(f"   Target market: {crew_forex.target_market}")
    assert crew_forex.target_market == "FOREX", "FOREX market not set"
    assert crew_forex.volatility_analyzer is not None, "Volatility analyzer not initialized"
    print("   ✅ Forex market scanner initialized")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - MarketScannerCrew Multi-Market Support Working")
    print("=" * 80)
    # Don't return value in test function


def main():
    """Run tests."""
    try:
        return test_market_scanner_instantiation()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
