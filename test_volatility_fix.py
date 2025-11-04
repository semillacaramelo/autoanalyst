#!/usr/bin/env python3
"""Quick test to verify volatility analysis tool handles dict-to-DataFrame conversion."""

import pandas as pd
from src.tools.market_scan_tools import MarketScanTools

# Simulate LLM passing serialized dict (what we saw in logs)
test_data = {
    "BTC/USD": {
        "timestamp": ["2025-10-01", "2025-10-02", "2025-10-03"] * 10,  # 30 timestamps
        "open": [60000.0, 61000.0, 59000.0] * 10,
        "high": [61500.0, 62000.0, 60000.0] * 10,
        "low": [59500.0, 60000.0, 58000.0] * 10,
        "close": [61000.0, 59500.0, 59800.0] * 10,
        "volume": [1000000.0, 1200000.0, 900000.0] * 10,
    },
    "ETH/USD": {
        "timestamp": ["2025-10-01", "2025-10-02", "2025-10-03"] * 10,
        "open": [3000.0, 3100.0, 2900.0] * 10,
        "high": [3150.0, 3200.0, 3000.0] * 10,
        "low": [2950.0, 3000.0, 2850.0] * 10,
        "close": [3100.0, 2950.0, 2980.0] * 10,
        "volume": [500000.0, 600000.0, 450000.0] * 10,
    }
}

print("Testing volatility analysis with dict input (simulating LLM serialization)...")
print(f"Input type: {type(test_data)}")
print(f"BTC data type: {type(test_data['BTC/USD'])}")
print(f"BTC data keys: {list(test_data['BTC/USD'].keys())}")
print(f"BTC timestamp count: {len(test_data['BTC/USD']['timestamp'])}")

# Call the tool with dict data (should auto-convert to DataFrame)
results = MarketScanTools.analyze_volatility(test_data)

print(f"\n✓ Results: {len(results)} symbols analyzed")
for result in results:
    print(f"  - {result['symbol']}: ATR={result['atr']:.2f}, Score={result['volatility_score']:.1f}")

# Verify we got expected results
assert len(results) == 2, f"Expected 2 results, got {len(results)}"
assert results[0]['symbol'] in ['BTC/USD', 'ETH/USD']
assert 'atr' in results[0]
assert 'volatility_score' in results[0]

print("\n✅ Dict-to-DataFrame conversion works! Tool can now handle LLM-serialized data.")
