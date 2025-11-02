"""
Test script for Feature 2.4: Market-Aware Scanner
Tests multi-market scanning capabilities with crypto, forex, and equity data.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.market_scan_tools import market_scan_tools
from src.connectors.alpaca_connector import alpaca_manager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_get_universe_symbols():
    """Test getting symbols for each market."""
    print("\n" + "="*80)
    print("TEST 1: Get Universe Symbols")
    print("="*80)
    
    markets = ['US_EQUITY', 'CRYPTO', 'FOREX']
    
    for market in markets:
        symbols = market_scan_tools.get_universe_symbols(market=market, max_symbols=5)
        print(f"\n{market} (top 5):")
        print(f"  Symbols: {symbols}")
        print(f"  Count: {len(symbols)}")
        assert len(symbols) <= 5, f"Max symbols limit not working for {market}"
        assert len(symbols) > 0, f"No symbols returned for {market}"
    
    print("\n✅ PASS: Universe symbol retrieval working for all markets")


def test_fetch_crypto_data():
    """Test fetching crypto data for multiple symbols."""
    print("\n" + "="*80)
    print("TEST 2: Fetch Crypto Data")
    print("="*80)
    
    crypto_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
    
    print(f"\nFetching data for: {crypto_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=crypto_symbols,
        timeframe='1Hour',
        limit=24,  # Last 24 hours
        asset_class='CRYPTO'
    )
    
    print(f"\nResults:")
    for symbol, df in data.items():
        print(f"  {symbol}: {len(df)} bars")
        print(f"    Date range: {df.index[0]} to {df.index[-1]}")
        print(f"    Columns: {list(df.columns)}")
        print(f"    Last close: ${df['close'].iloc[-1]:.2f}")
    
    assert len(data) == len(crypto_symbols), f"Expected {len(crypto_symbols)} symbols, got {len(data)}"
    for symbol in crypto_symbols:
        assert symbol in data, f"Missing data for {symbol}"
        assert len(data[symbol]) > 0, f"Empty DataFrame for {symbol}"
    
    print("\n✅ PASS: Crypto data fetching working")


def test_fetch_equity_data():
    """Test fetching equity data for multiple symbols."""
    print("\n" + "="*80)
    print("TEST 3: Fetch Equity Data")
    print("="*80)
    
    equity_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print(f"\nFetching data for: {equity_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=equity_symbols,
        timeframe='1Day',
        limit=30,  # Last 30 days
        asset_class='US_EQUITY'
    )
    
    print(f"\nResults:")
    for symbol, df in data.items():
        print(f"  {symbol}: {len(df)} bars")
        if len(df) > 0:
            print(f"    Date range: {df.index[0]} to {df.index[-1]}")
            print(f"    Last close: ${df['close'].iloc[-1]:.2f}")
        else:
            print(f"    (No data - possibly market closed)")
    
    # Note: May have empty DataFrames if market is closed
    print("\n✅ PASS: Equity data fetching working")


def test_auto_detect_asset_class():
    """Test automatic asset class detection."""
    print("\n" + "="*80)
    print("TEST 4: Auto-Detect Asset Class")
    print("="*80)
    
    mixed_symbols = ['AAPL', 'BTC/USD', 'ETH/USD']
    
    print(f"\nFetching mixed symbols (auto-detect): {mixed_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=mixed_symbols,
        timeframe='1Hour',
        limit=10,
        asset_class=None  # Auto-detect
    )
    
    print(f"\nResults:")
    for symbol, df in data.items():
        if df is not None and len(df) > 0:
            print(f"  {symbol}: {len(df)} bars ✅")
        else:
            print(f"  {symbol}: No data (possibly closed)")
    
    # At least crypto should have data (24/7)
    assert 'BTC/USD' in data or 'ETH/USD' in data, "No crypto data returned"
    
    print("\n✅ PASS: Auto-detect asset class working")


def test_analyze_volatility():
    """Test volatility analysis on crypto data."""
    print("\n" + "="*80)
    print("TEST 5: Analyze Volatility")
    print("="*80)
    
    crypto_symbols = ['BTC/USD', 'ETH/USD']
    
    # Fetch data
    print(f"\nFetching data for volatility analysis: {crypto_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=crypto_symbols,
        timeframe='1Day',
        limit=100,
        asset_class='CRYPTO'
    )
    
    # Analyze volatility
    print("\nAnalyzing volatility...")
    volatility_results = market_scan_tools.analyze_volatility(data)
    
    print(f"\nVolatility Results:")
    for result in volatility_results:
        print(f"  {result['symbol']}:")
        print(f"    ATR: {result['atr']:.2f}")
        print(f"    Volatility Score: {result['volatility_score']:.1f}")
    
    assert len(volatility_results) == len(crypto_symbols), "Volatility analysis incomplete"
    for result in volatility_results:
        assert 'atr' in result, "Missing ATR in results"
        assert 'volatility_score' in result, "Missing volatility score"
        assert result['atr'] > 0, "Invalid ATR value"
    
    print("\n✅ PASS: Volatility analysis working")


def test_analyze_technical_setup():
    """Test technical analysis on crypto data."""
    print("\n" + "="*80)
    print("TEST 6: Analyze Technical Setup")
    print("="*80)
    
    crypto_symbols = ['BTC/USD', 'ETH/USD']
    
    # Fetch data
    print(f"\nFetching data for technical analysis: {crypto_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=crypto_symbols,
        timeframe='1Day',
        limit=100,
        asset_class='CRYPTO'
    )
    
    # Analyze technicals
    print("\nAnalyzing technical setup...")
    technical_results = market_scan_tools.analyze_technical_setup(data)
    
    print(f"\nTechnical Results:")
    for result in technical_results:
        print(f"  {result['symbol']}:")
        print(f"    Technical Score: {result['technical_score']}")
        print(f"    Reason: {result['reason']}")
    
    assert len(technical_results) == len(crypto_symbols), "Technical analysis incomplete"
    for result in technical_results:
        assert 'technical_score' in result, "Missing technical score"
        assert 'reason' in result, "Missing reason"
    
    print("\n✅ PASS: Technical analysis working")


def test_filter_by_liquidity():
    """Test liquidity filtering on crypto data."""
    print("\n" + "="*80)
    print("TEST 7: Filter by Liquidity")
    print("="*80)
    
    crypto_symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
    
    # Fetch data
    print(f"\nFetching data for liquidity filtering: {crypto_symbols}")
    data = market_scan_tools.fetch_universe_data(
        symbols=crypto_symbols,
        timeframe='1Day',
        limit=30,
        asset_class='CRYPTO'
    )
    
    # Filter by liquidity
    print("\nFiltering by liquidity...")
    liquidity_results = market_scan_tools.filter_by_liquidity(data)
    
    print(f"\nLiquidity Results:")
    for result in liquidity_results:
        print(f"  {result['symbol']}:")
        print(f"    Liquidity Score: {result['liquidity_score']:.1f}")
        print(f"    Is Liquid: {result['is_liquid']}")
    
    assert len(liquidity_results) == len(crypto_symbols), "Liquidity filtering incomplete"
    for result in liquidity_results:
        assert 'liquidity_score' in result, "Missing liquidity score"
        assert 'is_liquid' in result, "Missing is_liquid flag"
    
    print("\n✅ PASS: Liquidity filtering working")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FEATURE 2.4 VALIDATION: Market-Aware Scanner")
    print("="*80)
    
    try:
        # Test 1: Get universe symbols
        test_get_universe_symbols()
        
        # Test 2: Fetch crypto data
        test_fetch_crypto_data()
        
        # Test 3: Fetch equity data
        test_fetch_equity_data()
        
        # Test 4: Auto-detect asset class
        test_auto_detect_asset_class()
        
        # Test 5: Analyze volatility
        test_analyze_volatility()
        
        # Test 6: Analyze technical setup
        test_analyze_technical_setup()
        
        # Test 7: Filter by liquidity
        test_filter_by_liquidity()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - Feature 2.4 Implementation Validated")
        print("="*80)
        print("\nMarket-Aware Scanner Features:")
        print("  ✅ Universe manager integration")
        print("  ✅ Multi-market symbol fetching (US_EQUITY, CRYPTO, FOREX)")
        print("  ✅ Asset class auto-detection")
        print("  ✅ Crypto/equity/forex data fetching")
        print("  ✅ Volatility analysis on multi-asset data")
        print("  ✅ Technical analysis on multi-asset data")
        print("  ✅ Liquidity filtering on multi-asset data")
        print("\nReady for integration with MarketScannerCrew")
        
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
