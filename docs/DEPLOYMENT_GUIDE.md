# AutoAnalyst - Production Deployment Guide

**Last Updated**: November 4, 2025  
**System Status**: ✅ Production Ready  
**Test Coverage**: 80% (312 tests passing)  
**Deployment Mode**: Paper Trading Validated

---

## 🎯 Quick Start - Your First Live Paper Trade

### Prerequisites Checklist

✅ **Phase 3 Complete**: 312 tests passing, 80% coverage  
✅ **Paper Trading Account**: $99,431.01 available  
✅ **Configuration Validated**: All 10 Gemini keys + Alpaca API working  
✅ **System Tested**: Live workflow validated November 4, 2025  

### Step 1: Verify System Status

```bash
cd /home/planetazul3/autoanalyst
python scripts/run_crew.py status --detailed
```

**Expected Output:**
```
✓ Account Status: AccountStatus.ACTIVE
✓ Equity: $99,431.01
✓ Mode: Paper Trading
✓ Data Feed: IEX
✓ API keys found: 10
```

### Step 2: Enable Live Paper Trading

**Current Setting**: `DRY_RUN=true` (simulated orders only)

**To enable live paper trading:**
```bash
# Edit .env file
nano .env

# Change this line:
DRY_RUN=true

# To this:
DRY_RUN=false

# Save and exit (Ctrl+X, Y, Enter)
```

**⚠️ SAFETY CHECK**: Verify you're still using paper trading URL:
```bash
grep "ALPACA_BASE_URL" .env
# Should show: https://paper-api.alpaca.markets
```

### Step 3: Run Your First Live Paper Trade

**Wait for Market Open** (US Market: 9:30 AM - 4:00 PM EST)

```bash
# Check market status
python -c "from datetime import datetime; import pytz; print(f'NY Time: {datetime.now(pytz.timezone(\"America/New_York\")).strftime(\"%H:%M %Z\")}')"

# When market is open, run a test trade:
python scripts/run_crew.py run --symbols SPY --strategies 3ma
```

**What Happens:**
1. System asks for confirmation: `Are you sure you want to execute live trades? [y/N]:`
2. Type `y` and press Enter
3. 4-agent workflow executes:
   - Market Data Specialist: Fetches SPY data
   - Technical Analyst: Generates signal (BUY/SELL/HOLD)
   - Risk Officer: Validates constraints
   - Trading Desk: Places order (if approved)
4. Order details logged to `logs/trading_crew_*.log`

---

## 📊 Market Hours & Trading Windows

### US Equity Market (SPY, AAPL, etc.)
- **Trading Hours**: 9:30 AM - 4:00 PM EST (Mon-Fri)
- **Pre-Market**: 4:00 AM - 9:30 AM EST (limited data)
- **After-Hours**: 4:00 PM - 8:00 PM EST (limited data)

### Crypto Market (BTC/USD, ETH/USD)
- **Trading Hours**: 24/7 (including weekends)
- **Always Available**: No market closure

### Checking Market Status

```bash
# Quick check
python -c "from datetime import datetime; import pytz; now = datetime.now(pytz.timezone('America/New_York')); hour = now.hour; print('🟢 MARKET OPEN' if 9 <= hour < 16 and now.weekday() < 5 else '🔴 MARKET CLOSED')"
```

---

## 🤖 Trading Modes

### Mode 1: Single Symbol Trading (Recommended for Start)

```bash
# Trade SPY with 3MA strategy
python scripts/run_crew.py run --symbols SPY --strategies 3ma

# Trade AAPL with RSI breakout
python scripts/run_crew.py run --symbols AAPL --strategies rsi_breakout

# Trade crypto (24/7)
python scripts/run_crew.py run --symbols BTC/USD --strategies macd
```

### Mode 2: Multiple Strategies on One Symbol

```bash
# Test multiple strategies sequentially
python scripts/run_crew.py run --symbols SPY --strategies 3ma,rsi_breakout,macd
```

### Mode 3: Parallel Multi-Symbol Trading

```bash
# Trade multiple symbols in parallel (max 3 concurrent by default)
python scripts/run_crew.py run --symbols SPY,QQQ,IWM --strategies 3ma --parallel
```

**⚠️ Rate Limit Note**: Parallel mode uses more API quota. With 10 keys, you have:
- 100 RPM total (10 keys × 10 RPM)
- Recommend starting with 1-2 parallel crews

### Mode 4: Autonomous 24/7 Trading

**Requires**: `AUTONOMOUS_MODE_ENABLED=true` in `.env`

```bash
# Automatically schedules trades based on market hours
python scripts/run_crew.py autonomous
```

**Features:**
- Detects market hours automatically
- Trades equities during US market hours
- Trades crypto 24/7
- Respects market calendar (holidays, closures)
- Auto-adjusts scan frequency based on volatility

---

## 🔧 Configuration Options

### Risk Management (`.env`)

```bash
# Position sizing
MAX_RISK_PER_TRADE=0.02    # 2% of account per trade

# Portfolio limits
MAX_OPEN_POSITIONS=3        # Maximum 3 concurrent positions
DAILY_LOSS_LIMIT=0.05       # Stop trading if down 5% for the day

# Trading limits
MAX_DAILY_TRADES=10         # Maximum 10 trades per day
```

### Strategy Parameters

```bash
# Moving Average Strategy (3MA)
MA_FAST_PERIOD=8
MA_MEDIUM_PERIOD=13
MA_SLOW_PERIOD=21

# Volume confirmation
VOLUME_THRESHOLD=1.5        # Volume must be 1.5x average

# Trend strength
ADX_THRESHOLD=25.0          # ADX must be > 25 for strong trend
```

### LLM Configuration

```bash
# Model selection (auto-managed)
DEFAULT_LLM_MODEL=google/gemini-2.5-flash
PRIMARY_LLM_MODELS=gemini-2.5-flash
FALLBACK_LLM_MODELS=gemini-2.5-pro

# Rate limiting (per key)
RATE_LIMIT_RPM=10          # Flash: 10 RPM, Pro: 2 RPM
RATE_LIMIT_RPD=250         # Flash: 250 RPD, Pro: 50 RPD
```

---

## 📈 Monitoring & Logs

### Real-Time Monitoring

```bash
# Check account status
python scripts/run_crew.py status

# View detailed API health
python scripts/run_crew.py status --detailed

# Interactive dashboard (planned for Phase 4)
python scripts/run_crew.py interactive
```

### Log Files

**Location**: `logs/trading_crew_YYYYMMDD.log`

**What's Logged:**
- All agent decisions and reasoning
- Data fetched from Alpaca
- Signals generated by strategies
- Risk checks and approvals
- Orders placed (with IDs)
- Errors and warnings

**View Logs:**
```bash
# Today's log
tail -f logs/trading_crew_$(date +%Y%m%d).log

# Search for orders placed
grep "Order placed" logs/trading_crew_*.log

# Search for signals
grep "signal.*BUY\|signal.*SELL" logs/trading_crew_*.log
```

---

## ⚠️ Safety Guidelines

### Before Going Live

1. **✅ Validate Configuration**
   ```bash
   python scripts/run_crew.py validate
   ```

2. **✅ Verify Paper Trading Mode**
   ```bash
   grep "ALPACA_BASE_URL" .env
   # Must show: https://paper-api.alpaca.markets
   ```

3. **✅ Test with DRY_RUN First**
   - Run several test cycles with `DRY_RUN=true`
   - Verify signals make sense
   - Check log output

4. **✅ Start Small**
   - Use conservative position sizes
   - Trade liquid symbols (SPY, QQQ)
   - Monitor first 5-10 trades closely

### Red Flags to Watch

🚨 **Stop Trading If:**
- Daily loss limit hit (5% by default)
- Unusual number of consecutive losses (>5)
- API errors persist (rate limits, connection issues)
- Unexpected account balance changes

🚨 **Review Immediately If:**
- Signals seem random or illogical
- Orders failing to execute
- Risk checks being bypassed
- Log files show errors

### Emergency Stop

```bash
# Immediate stop: Set DRY_RUN back to true
sed -i 's/DRY_RUN=false/DRY_RUN=true/' .env

# Close all positions manually via Alpaca dashboard:
# https://paper-api.alpaca.markets/dashboard
```

---

## 🎓 Understanding the Workflow

### The 4-Agent Trading Process

**1. Market Data Specialist**
- Fetches historical OHLCV data from Alpaca
- Validates data completeness and quality
- Checks for gaps and anomalies

**2. Quantitative Technical Analyst**
- Calculates technical indicators (MA, RSI, MACD, etc.)
- Applies strategy rules
- Generates signal: BUY, SELL, or HOLD
- Provides confidence score and reasoning

**3. Portfolio Risk Officer**
- Checks account constraints:
  - Current open positions < MAX_OPEN_POSITIONS
  - Daily loss < DAILY_LOSS_LIMIT
  - Available buying power sufficient
- Calculates position size based on:
  - Account equity
  - Volatility (ATR)
  - Risk per trade (2% default)
- Approves or rejects trade

**4. Head of Trading Desk**
- Places market orders if approved
- Logs execution details
- Returns order ID and fill price
- Skips execution if signal is HOLD or rejected

### Signal Types

**BUY Signal**
- Conditions met for long position
- Analyst identifies bullish setup
- Risk checks pass
- → System places BUY market order

**SELL Signal**
- Conditions met for short position (if enabled)
- Analyst identifies bearish setup
- Risk checks pass
- → System places SELL market order (or closes long)

**HOLD Signal**
- No clear trading opportunity
- Conditions not met
- Insufficient data
- → System does nothing

---

## 📊 Available Strategies

### 1. Triple Moving Average (3ma)
**Best For**: Trending markets  
**Signals**:
- BUY: Fast MA > Medium MA > Slow MA (all aligned)
- SELL: Fast MA < Medium MA < Slow MA (all aligned)
- Requires: Volume confirmation + ADX > 25

### 2. RSI Breakout (rsi_breakout)
**Best For**: Reversals and oversold/overbought  
**Signals**:
- BUY: RSI < 30 (oversold) then crosses above 30
- SELL: RSI > 70 (overbought) then crosses below 70
- Requires: Volume confirmation

### 3. MACD Crossover (macd)
**Best For**: Momentum trading  
**Signals**:
- BUY: MACD line crosses above signal line
- SELL: MACD line crosses below signal line
- Requires: Histogram confirmation

### 4. Bollinger Bands Reversal (bollinger_bands_reversal)
**Best For**: Range-bound markets  
**Signals**:
- BUY: Price touches lower band + reversal confirmation
- SELL: Price touches upper band + reversal confirmation
- Requires: RSI confirmation

---

## 🔍 Troubleshooting

### Issue: No Data Fetched (0 bars)

**Cause**: Market is closed  
**Solution**:
- Check market hours (9:30 AM - 4:00 PM EST)
- Trade crypto if outside equity market hours
- Use autonomous mode for automatic scheduling

### Issue: "All API keys exhausted"

**Cause**: Rate limit hit on all 10 Gemini keys  
**Solution**:
- Wait 60 seconds for RPM reset
- Reduce parallel crews
- System auto-rotates keys (should self-recover)

### Issue: Signal is Always HOLD

**Cause**: Market conditions not meeting strategy criteria  
**Solution**:
- Try different strategy
- Check if market is trending vs ranging
- Review indicator values in logs
- This is normal - HOLD is valid signal

### Issue: Orders Not Executing

**Check**:
1. `DRY_RUN=false` in `.env`
2. Market is open
3. Sufficient buying power
4. Risk checks passing (check logs)
5. Alpaca API connection working

---

## 📈 Performance Tracking

### Check Account Performance

```bash
# View account summary
python scripts/run_crew.py status

# Backtest a strategy
python scripts/run_crew.py backtest --symbol SPY --strategy 3ma --start 2024-01-01 --end 2024-06-30

# Compare multiple strategies
python scripts/run_crew.py compare --symbol SPY --strategies 3ma,rsi_breakout,macd --start 2024-01-01 --end 2024-06-30
```

### Metrics to Monitor

**Daily:**
- Number of trades executed
- Win rate (profitable trades / total trades)
- Average profit per trade
- Maximum drawdown
- Daily P&L vs account equity

**Weekly:**
- Cumulative return vs buy-and-hold
- Sharpe ratio (risk-adjusted returns)
- Maximum consecutive losses
- Strategy performance comparison

---

## 🚀 Scaling Up

### Phase 1: Validation (Week 1-2)
- [ ] Run 20+ test trades with DRY_RUN=true
- [ ] Enable live paper trading (DRY_RUN=false)
- [ ] Execute 10 live paper trades manually
- [ ] Validate all trades make sense
- [ ] Monitor logs for errors

### Phase 2: Automation (Week 3-4)
- [ ] Enable autonomous mode
- [ ] Start with 1-2 symbols
- [ ] Monitor for 1 week continuously
- [ ] Review performance metrics
- [ ] Adjust risk parameters as needed

### Phase 3: Production (Week 5+)
- [ ] Scale to 5-10 symbols
- [ ] Enable parallel execution (2-3 crews)
- [ ] Implement Phase 4 monitoring (optional)
- [ ] Consider live trading (real money)

---

## ⚡ Quick Reference Commands

```bash
# Validate configuration
python scripts/run_crew.py validate

# Check system status
python scripts/run_crew.py status --detailed

# Single trade (DRY_RUN)
python scripts/run_crew.py run --symbols SPY --strategies 3ma

# Enable live paper trading
sed -i 's/DRY_RUN=true/DRY_RUN=false/' .env

# Disable live trading (back to DRY_RUN)
sed -i 's/DRY_RUN=false/DRY_RUN=true/' .env

# View today's logs
tail -f logs/trading_crew_$(date +%Y%m%d).log

# Run all tests
pytest

# Check test coverage
pytest --cov=src tests/
```

---

## 📞 Support & Next Steps

### Documentation
- `README.md` - Project overview
- `FEATURE_ROADMAP.md` - Development roadmap
- `docs/PHASE3_COMPLETION_SUMMARY.md` - Testing validation
- `docs/MASTER_SDK_DOCUMENTATION.md` - Technical reference

### Phase 4 Planning (Optional)
After validating paper trading, consider Phase 4 enhancements:
- Structured logging (JSON format, rotation)
- Error recovery mechanisms (circuit breakers)
- Performance monitoring dashboard
- Configuration management UI
- CI/CD deployment pipeline

---

## ✅ Deployment Checklist

Before going live, verify:

- [x] Phase 3 tests passing (312/312) ✅
- [x] 80% code coverage achieved ✅
- [x] Configuration validated ✅
- [x] Paper trading account active ✅
- [x] Live workflow tested ✅
- [x] Safety confirmations working ✅
- [ ] First 10 DRY_RUN trades reviewed
- [ ] First 5 live paper trades monitored
- [ ] Performance acceptable (win rate, drawdown)
- [ ] Risk management working correctly
- [ ] Ready for autonomous mode

---

**System Status**: ✅ Ready for Paper Trading  
**Last Tested**: November 4, 2025  
**Version**: 0.3.0  
**Production Grade**: Yes (with paper trading)

**Happy Trading! 🚀**
