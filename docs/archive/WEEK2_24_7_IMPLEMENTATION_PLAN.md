# Week 2-3: True 24/7 Multi-Market Trading Implementation Plan

**Created**: November 2, 2025  
**Priority**: HIGH - Unlocks autonomous 24/7 operation  
**Status**: Ready to Begin (Week 1 Complete ✅)

---

## Quick Reference: Why This Matters

**Current Limitation**: System only trades US equities during market hours (9:30 AM - 4:00 PM ET)
- **Uptime**: 6.5 hours/day = 27% coverage
- **Idle Time**: 17.5 hours/day when market is closed
- **Lost Opportunities**: Cannot trade crypto (24/7), forex (23/5), international markets

**Target Capability**: True 24/7 autonomous trading with intelligent market rotation
- **Uptime**: 24 hours/day = 100% coverage
- **Active Markets**: US equities (peak hours) + Crypto (always available)
- **Adaptive Strategy**: System selects best market and strategies based on time of day

---

## Implementation Checklist

### Prerequisites (Before Starting)

- [x] **Week 1 Complete** - All critical bugs fixed ✅
- [x] **✅ Verify Alpaca Crypto Support** (COMPLETED - November 2, 2025)
  - ✅ IEX data feed includes FREE crypto data (no upgrade needed)
  - ✅ Tested endpoints: Successfully fetched BTC/USD historical bars
  - ✅ Available coins: 62 tradable pairs (BTC/USD, ETH/USD, SOL/USD, DOGE/USD, LINK/USD, AVAX/USD, etc.)
  - ✅ Data quality: Real-time crypto data (unlike 15-min delayed stocks)
  - ✅ Trading: Both paper and live crypto trading available
  - **Result**: NO SUBSCRIPTION UPGRADE REQUIRED
- [ ] **Download Crypto Historical Data** (4 hours)
  - Get 6-12 months OHLCV for top 20 cryptos from Alpaca API
  - Calculate baseline indicators (ATR, volatility, correlation)
  - Prepare backtesting datasets

**Estimated Setup Time**: 4 hours (reduced from 6h - crypto verification complete)

---

## Week 2: Core Multi-Market Infrastructure

### Day 1-2: Asset Classification & Data Layer (12-16 hours)

**Goal**: Enable system to identify and fetch data for crypto assets

#### Task 1.1: Create Asset Classifier (4 hours)
```bash
# Create new file
touch src/utils/asset_classifier.py
```

**Implementation**:
```python
# See project_resolution_roadmap.md Part 6, Section 1.1 for full code
class AssetClassifier:
    ASSET_CLASSES = {
        "CRYPTO": {"patterns": ["USD", "USDT", "BTC", "ETH"], ...},
        "FOREX": {"patterns": ["/"], ...},
        "US_EQUITY": {"patterns": ["^[A-Z]{1,5}$"], ...}
    }
    
    @staticmethod
    def classify(symbol: str) -> dict:
        # Returns: {"type": "CRYPTO", "client_type": "crypto", ...}
```

**Testing**:
```bash
# Unit test
pytest tests/test_utils/test_asset_classifier.py -v
# Expected: AAPL→US_EQUITY, BTC/USD→CRYPTO, EUR/USD→FOREX
```

#### Task 1.2: Enhance Alpaca Connector (6 hours)
```python
# Modify src/connectors/alpaca_connector.py
from alpaca.data.historical import CryptoHistoricalDataClient

class AlpacaConnectionManager:
    @property
    def crypto_client(self) -> CryptoHistoricalDataClient:
        # Lazy load crypto client
        
    def fetch_historical_bars(self, symbol, timeframe, limit, asset_class=None):
        # Auto-detect asset class, route to correct client
        if asset_class == "CRYPTO":
            return self._fetch_crypto_bars(...)
```

**Testing**:
```bash
# Manual test
python -c "
from src.connectors.alpaca_connector import alpaca_manager
df = alpaca_manager.fetch_historical_bars('BTC/USD', '1Hour', limit=100, asset_class='CRYPTO')
print(f'Fetched {len(df)} bars for BTC/USD')
print(df.head())
"
# Expected: 100 bars with OHLCV columns
```

#### Task 1.3: Create Universe Manager (4 hours)
```bash
touch src/tools/universe_manager.py
```

**Implementation**:
```python
class UniverseManager:
    UNIVERSES = {
        "US_EQUITY": {"source": "static", "symbols": SP_100_SYMBOLS},
        "CRYPTO": {
            "source": "dynamic",
            "filters": {"min_volume_24h": 10_000_000, "min_market_cap": 1_000_000_000}
        }
    }
    
    def get_active_universe(self, market: str) -> List[str]:
        # Returns tradable symbols for given market
```

**Testing**:
```bash
pytest tests/test_tools/test_universe_manager.py -v
# Expected: US_EQUITY returns 100 symbols, CRYPTO returns 10-20 top coins
```

**Deliverable**: System can detect crypto symbols and fetch crypto market data from Alpaca ✅

---

### Day 3-4: Scanner Enhancement (10-14 hours)

**Goal**: Market scanner can analyze crypto during US market closed hours

#### Task 2.1: Modify Scanner Crew (6 hours)
```python
# Modify src/crew/market_scanner_crew.py
class MarketScannerCrew:
    def __init__(self, target_market: str = None, skip_init: bool = False):
        if target_market is None:
            # Auto-detect active market
            target_market = self._detect_active_market()
        
        self.target_market = target_market
        self.universe_manager = UniverseManager()
```

#### Task 2.2: Update Scan Tools (4 hours)
```python
# Modify src/tools/market_scan_tools.py
class MarketScanTools:
    @staticmethod
    @tool("Fetch Universe Data")
    def fetch_universe_data(symbols: List[str], asset_class: str = "US_EQUITY"):
        # Pass asset_class to alpaca_manager.fetch_historical_bars()
```

#### Task 2.3: Integration Testing (3 hours)
```bash
# Test scanner with crypto during US closed hours
python scripts/run_crew.py scan --market CRYPTO

# Expected output:
# - Scanning 15-20 crypto symbols
# - Data fetched for BTC/USD, ETH/USD, etc.
# - Top 5 crypto opportunities identified
# - Completion time: <2 minutes
```

**Deliverable**: Scanner successfully identifies crypto trading opportunities ✅

---

### Day 5: Strategy Adaptation (8-12 hours)

**Goal**: Strategies automatically adjust parameters for crypto vs equities

#### Task 3.1: Enhance Base Strategy (4 hours)
```python
# Modify src/strategies/base_strategy.py
class TradingStrategy(ABC):
    def __init__(self, asset_class: str = "US_EQUITY"):
        self.asset_class = asset_class
        self.params = self._get_asset_specific_params()
    
    def _get_asset_specific_params(self) -> dict:
        if self.asset_class == "CRYPTO":
            return {
                "min_bars_required": 100,
                "volume_weight": 0.5,  # Less emphasis for 24/7 markets
                "volatility_multiplier": 1.5,
                "atr_periods": 20
            }
```

#### Task 3.2: Update Existing Strategies (4 hours)
```python
# Modify all 4 strategies: triple_ma.py, rsi_breakout.py, macd_crossover.py, bollinger_bands_reversal.py
# Add asset_class parameter to __init__
# Call parent __init__(asset_class=asset_class)
```

#### Task 3.3: Backtesting Validation (3 hours)
```bash
# Backtest each strategy with crypto data
python scripts/run_crew.py backtest --symbol BTC/USD --strategy 3ma --asset-class CRYPTO --start 2024-01-01 --end 2024-10-31

# Expected: 
# - Win rate: 50-55% (conservative for crypto)
# - Max drawdown: <15%
# - Profit factor: >1.2
```

**Deliverable**: Strategies adapt parameters automatically for crypto markets ✅

---

## Week 3: Intelligent Orchestration

### Day 1-2: Market Rotation Logic (10-12 hours)

**Goal**: System intelligently selects which market to trade based on time and conditions

#### Task 4.1: Create Market Rotation Strategy (6 hours)
```bash
touch src/crew/market_rotation_strategy.py
```

**Implementation**:
```python
class MarketRotationStrategy:
    def select_active_market(self) -> str:
        """
        Priority logic:
        1. US market open (9:30-4:00 ET) → US_EQUITY (best liquidity)
        2. US market closed → CRYPTO (24/7 availability)
        3. Consider recent performance per market
        """
        calendar = MarketCalendar()
        active = calendar.get_active_markets(datetime.now(pytz.utc), settings.target_markets)
        
        if "US_EQUITY" in active:
            return "US_EQUITY"  # Prioritize when US market is open
        elif active:
            return self._select_by_performance(active)
        else:
            return "CRYPTO"  # Default to 24/7 market
```

#### Task 4.2: Add Performance Tracking (4 hours)
```python
# Modify src/utils/state_manager.py
# Add market_performance tracking:
# {
#   "US_EQUITY": {"trades": 50, "win_rate": 0.58, "avg_profit": 0.015, "score": 0.87},
#   "CRYPTO": {"trades": 30, "win_rate": 0.52, "avg_profit": 0.022, "score": 0.79}
# }
```

**Testing**:
```bash
# Test market selection at different times
python -c "
from src.crew.market_rotation_strategy import MarketRotationStrategy
import pytz
from datetime import datetime

# Simulate US market hours (10:00 AM ET = 3:00 PM UTC)
# Expected: US_EQUITY selected

# Simulate US closed (8:00 PM ET = 1:00 AM UTC)
# Expected: CRYPTO selected
"
```

**Deliverable**: System automatically chooses best market to trade ✅

---

### Day 3-4: Enhanced Scheduler (12-14 hours)

**Goal**: Global scheduler uses market rotation and adaptive intervals

#### Task 5.1: Integrate Market Rotation (6 hours)
```python
# Modify src/utils/global_scheduler.py
class AutoTradingScheduler:
    def __init__(self):
        self.market_rotation = MarketRotationStrategy()
        # ...existing code...
    
    def run_forever(self):
        while True:
            # Select best market
            target_market = self.market_rotation.select_active_market()
            
            # Run scanner for that market
            scanner = MarketScannerCrew(target_market=target_market)
            results = scanner.run()
            
            # Trade top opportunities with market-appropriate strategies
            for asset in results["top_assets"]:
                asset_class = AssetClassifier.classify(asset["symbol"])["type"]
                strategies = StrategyRegistry.get_best_strategies(asset_class)
                # Execute trades...
```

#### Task 5.2: Adaptive Scan Intervals (4 hours)
```python
def _calculate_adaptive_interval(self, market: str) -> int:
    """
    - US_EQUITY hours: 5 min (high activity)
    - CRYPTO peak hours (US evening): 15 min
    - CRYPTO off-peak: 30 min
    """
    if market == "US_EQUITY":
        return 5 * 60
    elif market == "CRYPTO":
        hour_utc = datetime.now(pytz.utc).hour
        return 15 * 60 if 12 <= hour_utc <= 4 else 30 * 60
```

#### Task 5.3: Integration Testing (3 hours)
```bash
# Run 1-hour simulation across market transition
# Start at 3:50 PM ET (10 min before US close)
# Verify system switches from US_EQUITY → CRYPTO at 4:00 PM
python scripts/run_crew.py autonomous --duration 3600
```

**Deliverable**: Scheduler intelligently rotates markets and adapts scan frequency ✅

---

### Day 5: Full 24-Hour Integration Test (8-10 hours)

**Goal**: Validate complete 24/7 operation with market switching

#### Test Scenarios

**Scenario 1: US Market Hours (9:30 AM - 4:00 PM ET)**
- Expected: Trade US equities only
- Scan interval: 5 minutes
- Strategies: All 4 strategies suitable for equities
- Verify: No crypto trades during this period

**Scenario 2: US Market Closed, Evening (4:00 PM - 12:00 AM ET)**
- Expected: Switch to crypto trading
- Scan interval: 15 minutes (peak crypto activity)
- Strategies: Crypto-adapted parameters
- Verify: US equity positions closed, crypto positions opened

**Scenario 3: US Market Closed, Late Night (12:00 AM - 9:30 AM ET)**
- Expected: Continue crypto trading
- Scan interval: 30 minutes (quieter hours)
- Strategies: Same crypto-adapted parameters
- Verify: Lower trade frequency, maintain risk limits

**Scenario 4: Market Transition (3:55 PM - 4:05 PM ET)**
- Expected: Smooth transition from US → Crypto
- Actions: Close US positions, scan crypto universe, open crypto trades
- Verify: No errors, state persisted correctly

#### Test Execution
```bash
# Run full 24-hour test in DRY_RUN mode
DRY_RUN=true python scripts/run_crew.py autonomous

# Monitor logs in real-time
tail -f logs/trading_crew_$(date +%Y%m%d).log

# Check state after 24 hours
python -c "
from src.utils.state_manager import StateManager
state = StateManager().load_state()
print('Trades executed:', len(state['trade_history']))
print('Market breakdown:')
print('  US_EQUITY:', sum(1 for t in state['trade_history'] if t['market'] == 'US_EQUITY'))
print('  CRYPTO:', sum(1 for t in state['trade_history'] if t['market'] == 'CRYPTO'))
print('Total API calls:', state['api_calls_24h'])
print('Uptime:', state['uptime_percentage'], '%')
"
```

#### Success Criteria
- [ ] System runs for 24 hours without crashes
- [ ] Market transitions happen automatically at correct times
- [ ] Both US equity and crypto trades executed
- [ ] API quota usage <80% of daily limit
- [ ] No duplicate trades or state corruption
- [ ] All trades respect risk limits (max 3 open positions)
- [ ] Logs show clear market switching logic

**Deliverable**: System demonstrates true 24/7 autonomous operation ✅

---

## Rollout Plan

### Phase 1: Testing (Week 2-3)
- All development in DRY_RUN mode
- Use Alpaca paper trading only (62 crypto pairs available)
- Extensive backtesting with historical crypto data (FREE via IEX)
- Monitor for 1 week (7 days × 24 hours) to validate stability
- **Note**: Crypto data is real-time and free (no delays like equity data)

### Phase 2: Limited Live (Week 4)
- Enable live crypto trading with $500 test capital
- Keep US equity in paper trading
- Monitor first 100 crypto trades closely
- Limit crypto position size to 0.5% risk per trade

### Phase 3: Full Production (Month 2)
- Enable both US equity and crypto live trading
- Gradually increase position sizes
- Monitor for 2-4 weeks before considering "hands-off"
- Set up alerting system (email/SMS for critical errors)

---

## Risk Mitigation Checklist
**Before Going Live**:
- [x] ✅ Verify Alpaca crypto support - CONFIRMED (free with IEX)
- [ ] Backtest all strategies on 12 months crypto data (use Alpaca API)
- [ ] Backtest all strategies on 12 months crypto data
- [ ] Test wash trading detection on known pump & dump examples
- [ ] Implement daily loss limits per market (5% US, 7% crypto)
- [ ] Set up monitoring alerts (error rate, quota usage, drawdown)
- [ ] Document rollback procedure (how to stop autonomous mode safely)
- [ ] Consult tax/legal advisor on crypto trading implications
- [ ] Create backup of state files before each trading session

**During Testing**:
- [ ] Monitor API quota usage every 6 hours
- [ ] Check for false signals in crypto (higher volatility = more noise)
- [ ] Verify strategy parameters are adapting correctly per asset class
- [ ] Test emergency stop procedure (close all positions, halt trading)
- [ ] Validate state persistence across restarts

**Ongoing (After Rollout)**:
- [ ] Weekly performance review per market (US vs crypto win rates)
- [ ] Monthly strategy rebalancing (adjust parameters based on results)
- [ ] Quarterly backtest validation (strategies still effective?)
- [ ] Track API costs (Alpaca subscription, Gemini LLM usage)

---

## Key Files to Modify/Create

### New Files (5)
1. `src/utils/asset_classifier.py` - Asset class detection
2. `src/tools/universe_manager.py` - Dynamic asset universe management
3. `src/crew/market_rotation_strategy.py` - Intelligent market selection
4. `src/strategies/crypto_adaptations.py` - Crypto-specific helpers
5. `tests/test_utils/test_asset_classifier.py` - Unit tests

### Modified Files (8)
1. `src/connectors/alpaca_connector.py` - Add crypto client
2. `src/crew/market_scanner_crew.py` - Target market parameter
3. `src/tools/market_scan_tools.py` - Handle crypto symbols
4. `src/strategies/base_strategy.py` - Asset-specific parameters
5. `src/strategies/triple_ma.py` - Add asset_class parameter
6. `src/strategies/rsi_breakout.py` - Add asset_class parameter
7. `src/strategies/macd_crossover.py` - Add asset_class parameter
8. `src/strategies/bollinger_bands_reversal.py` - Add asset_class parameter
9. `src/utils/global_scheduler.py` - Market rotation integration
10. `src/utils/state_manager.py` - Performance tracking per market
11. `src/strategies/registry.py` - Asset-class-to-strategy mapping

**Total Estimated Changes**: ~2000-3000 lines of code across 16 files

---

## Expected Outcomes

**By End of Week 3**:
- ✅ System trades US equities during market hours (9:30-4:00 ET)
- ✅ System switches to crypto when US market closes
- ✅ Strategies automatically adapt parameters for crypto
- ✅ Scanner discovers crypto opportunities (BTC, ETH, SOL, etc.)
- ✅ Market rotation based on time of day and performance
- ✅ Adaptive scan intervals (5-30 min depending on market)
- ✅ True 24/7 operation validated with 24-hour test
- ✅ API quota usage optimized (<80% of daily limit)

**Performance Targets**:
- US Equity: 55-60% win rate (maintain existing baseline)
- Crypto: 50-55% win rate (conservative for higher volatility)
- Uptime: 95%+ across 24 hours (vs current 27%)
- Daily Trades: 8-12 across both markets (within limits)
- Max Drawdown: 10% overall, 5% per market

**Business Impact**:
- 3.7x increase in trading uptime (27% → 100%)
- Diversification across asset classes (reduces correlation risk)
- Ability to capitalize on overnight/weekend crypto moves
- Foundation for adding Forex, international equities later
- True "set it and forget it" autonomous system

---

## Support & Resources

**Documentation**:
- Full technical details: `project_resolution_roadmap.md` Part 6
- Week 1 achievements: `docs/WEEK1_COMPLETION_SUMMARY.md`
- Testing results: `TESTING_SUMMARY.md`

**APIs & SDKs**:
- Alpaca Crypto API: https://docs.alpaca.markets/docs/crypto-trading
- Alpaca Python SDK: https://github.com/alpacahq/alpaca-py
- Crypto Historical Data: https://docs.alpaca.markets/reference/cryptobars

**Next Steps**:
1. Review this plan with team/stakeholders
2. Verify Alpaca crypto support (2 hours)
3. Begin Week 2 Day 1 implementation
4. Report progress daily in `logs/week2_progress.md`

---

**Document Version**: 1.0  
**Last Updated**: November 2, 2025  
**Status**: Ready to Implement  
**Estimated Completion**: Week 3 (November 16-22, 2025)
