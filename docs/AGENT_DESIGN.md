# Agent Architecture & Trading Strategy

## 1. Trading Strategy: Enhanced Triple Moving Average (3MA)

### Core Strategy
The system uses a triple-moving-average crossover strategy optimized for 1-minute timeframes with confirmation layers.

### Technical Specifications

**Moving Averages:**
- **Fast MA:** 8-period EMA (Exponential Moving Average)
- **Medium MA:** 13-period EMA
- **Slow MA:** 21-period EMA

**Signal Generation:**
- **BUY Signal:** Fast MA crosses above Medium MA AND Medium MA crosses above Slow MA
- **SELL Signal:** Fast MA crosses below Medium MA AND Medium MA crosses below Slow MA
- **HOLD:** Any other configuration

**Confirmation Layers** (Reduce false signals):
1. **Volume Confirmation:** Current volume > 1.5x average volume (20-period)
2. **Volatility Filter:** ATR (Average True Range) within acceptable range
3. **Trend Strength:** ADX (Average Directional Index) > 25

### Why This Works
- **Multiple timeframes:** 8/13/21 periods follow Fibonacci ratios
- **Momentum confirmation:** Volume surge indicates real breakouts
- **Noise filtering:** Volatility checks avoid choppy markets
- **Proven track record:** Widely used in algo trading with 55-60% win rate

---

## 2. Agent Architecture

### Agent Hierarchy (Sequential Process)

```
┌─────────────────────────────────────────┐
│   1. DataCollectorAgent                 │
│   Fetches OHLCV data                    │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   2. SignalGeneratorAgent               │
│   Calculates 3MA + indicators           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   3. SignalValidatorAgent               │
│   Applies confirmation layers           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   4. RiskManagerAgent                   │
│   Portfolio-level risk checks           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   5. ExecutionAgent                     │
│   Places orders via Alpaca             │
└─────────────────────────────────────────┘
```

### Agent Specifications

#### Agent 1: DataCollectorAgent
**Role:** Market Data Specialist  
**Goal:** Fetch accurate, complete OHLCV data for analysis  
**Backstory:** "You are a meticulous data collector ensuring every bar is complete and validated."

**Tools:**
- `fetch_historical_bars(symbol, timeframe, limit)` → Returns DataFrame
- `validate_data_completeness(df)` → Checks for gaps/nulls

**Output Format:**
```python
{
	"symbol": "SPY",
	"status": "complete"
}
```

**LLM Usage:** Minimal (only for error interpretation)  
**Estimated Calls/Run:** 1-2

---

#### Agent 2: SignalGeneratorAgent
**Role:** Quantitative Technical Analyst  
**Goal:** Calculate precise technical indicators and generate raw signals  
**Backstory:** "You are a mathematician obsessed with perfect indicator calculations."

**Tools:**
- `calculate_ema(df, period)` → EMA values
- `calculate_volume_avg(df, period)` → Volume average
- `calculate_atr(df, period)` → ATR values
- `calculate_adx(df, period)` → ADX values
- `generate_3ma_signal(df)` → RAW signal (BUY/SELL/HOLD)

**Output Format:**
```python
{
	"signal": "BUY",
	"confidence": "raw"  # Not yet validated
}
```

**LLM Usage:** Low (reasoning about indicator values)  
**Estimated Calls/Run:** 2-3

---

#### Agent 3: SignalValidatorAgent
**Role:** Chief Quality Officer  
**Goal:** Apply confirmation filters and validate signal quality  
**Backstory:** "You are a skeptic who trusts no signal until proven by multiple confirmations."

**Tools:**
- `check_volume_confirmation(current_vol, avg_vol, threshold=1.5)` → Boolean
# Agent Architecture & Trading Strategy

## 1. Trading Strategy: Enhanced Triple Moving Average (3MA)

### Core Strategy
The system uses a triple-moving-average crossover strategy optimized for 1-minute timeframes with confirmation layers.

### Technical Specifications

**Moving Averages:**
- **Fast MA:** 8-period EMA (Exponential Moving Average)
- **Medium MA:** 13-period EMA
- **Slow MA:** 21-period EMA

**Signal Generation:**
- **BUY Signal:** Fast MA crosses above Medium MA AND Medium MA crosses above Slow MA
- **SELL Signal:** Fast MA crosses below Medium MA AND Medium MA crosses below Slow MA
- **HOLD:** Any other configuration

**Confirmation Layers** (Reduce false signals):
1. **Volume Confirmation:** Current volume > 1.5x average volume (20-period)
2. **Volatility Filter:** ATR (Average True Range) within acceptable range
3. **Trend Strength:** ADX (Average Directional Index) > 25

### Why This Works
- **Multiple timeframes:** 8/13/21 periods follow Fibonacci ratios
- **Momentum confirmation:** Volume surge indicates real breakouts
- **Noise filtering:** Volatility checks avoid choppy markets
- **Proven track record:** Widely used in algo trading with 55-60% win rate

---

## 2. Agent Architecture

### Agent Hierarchy (Sequential Process)

```
┌─────────────────────────────────────────┐
│   1. DataCollectorAgent                 │
│   Fetches OHLCV data                    │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   2. SignalGeneratorAgent               │
│   Calculates 3MA + indicators           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   3. SignalValidatorAgent               │
│   Applies confirmation layers           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   4. RiskManagerAgent                   │
│   Portfolio-level risk checks           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   5. ExecutionAgent                     │
│   Places orders via Alpaca             │
└─────────────────────────────────────────┘
```

### Agent Specifications

#### Agent 1: DataCollectorAgent
**Role:** Market Data Specialist  
**Goal:** Fetch accurate, complete OHLCV data for analysis  
**Backstory:** "You are a meticulous data collector ensuring every bar is complete and validated."

**Tools:**
- `fetch_historical_bars(symbol, timeframe, limit)` → Returns DataFrame
- `validate_data_completeness(df)` → Checks for gaps/nulls

**Output Format:**
```python
{
	"symbol": "SPY",
	"timeframe": "1Min",
	"bars": 100,
	"data": DataFrame,
	"status": "complete"
}
```

**LLM Usage:** Minimal (only for error interpretation)  
**Estimated Calls/Run:** 1-2

---

#### Agent 2: SignalGeneratorAgent
**Role:** Quantitative Technical Analyst  
**Goal:** Calculate precise technical indicators and generate raw signals  
**Backstory:** "You are a mathematician obsessed with perfect indicator calculations."

**Tools:**
- `calculate_ema(df, period)` → EMA values
- `calculate_volume_avg(df, period)` → Volume average
- `calculate_atr(df, period)` → ATR values
- `calculate_adx(df, period)` → ADX values
- `generate_3ma_signal(df)` → RAW signal (BUY/SELL/HOLD)

**Output Format:**
```python
{
	"signal": "BUY",
	"fast_ma": 450.25,
	"medium_ma": 449.80,
	"slow_ma": 448.90,
	"current_price": 450.50,
	"volume": 1250000,
	"volume_avg": 800000,
	"atr": 0.75,
	"adx": 32.5,
	"confidence": "raw"  # Not yet validated
}
```

**LLM Usage:** Low (reasoning about indicator values)  
**Estimated Calls/Run:** 2-3

---

#### Agent 3: SignalValidatorAgent
**Role:** Chief Quality Officer  
**Goal:** Apply confirmation filters and validate signal quality  
**Backstory:** "You are a skeptic who trusts no signal until proven by multiple confirmations."

**Tools:**
- `check_volume_confirmation(current_vol, avg_vol, threshold=1.5)` → Boolean
- `check_volatility_range(atr, min_atr, max_atr)` → Boolean
- `check_trend_strength(adx, threshold=25)` → Boolean
- `calculate_signal_confidence(confirmations)` → Score (0-100)

**Logic:**
```python
confirmations = []
if volume > 1.5 * volume_avg:
	confirmations.append("volume")
if 0.3 < atr < 2.0:  # Adjustable
	confirmations.append("volatility")
if adx > 25:
	confirmations.append("trend")

if len(confirmations) >= 2:
	signal = ORIGINAL_SIGNAL
	confidence = len(confirmations) / 3 * 100
else:
	signal = "HOLD"
	confidence = 0
```

**Output Format:**
```python
{
	"final_signal": "BUY",  # or "HOLD" if failed validation
	"confidence": 100,       # 0-100 scale
	"confirmations": ["volume", "volatility", "trend"],
	"override_reason": None or "Failed volume confirmation"
}
```

**LLM Usage:** Medium (reasoning about market conditions)  
**Estimated Calls/Run:** 3-4

---

#### Agent 4: RiskManagerAgent
**Role:** Portfolio Risk Officer  
**Goal:** Enforce position sizing and portfolio-level risk constraints  
**Backstory:** "You protect capital above all else. No trade is worth risking the portfolio."

**Tools:**
- `get_account_info()` → Buying power, portfolio value
- `get_open_positions()` → Current positions
- `calculate_position_size(signal, account, max_risk_per_trade=0.02)` → Shares
- `check_max_positions(current, max=3)` → Boolean
- `check_daily_loss_limit(today_pnl, account_value, max_loss=0.05)` → Boolean

**Risk Rules:**
1. **Max risk per trade:** 2% of account value
2. **Max open positions:** 3 concurrent
3. **Daily loss limit:** 5% of account value
4. **Position sizing:** `shares = (account_value * 0.02) / atr`

**Output Format:**
```python
{
	"trade_approved": True,
	"position_size": 10,  # shares
	"risk_checks": {
		"position_limit": "PASS",
		"daily_loss": "PASS",
		"buying_power": "PASS"
	},
	"veto_reason": None or "Daily loss limit exceeded"
}
```

**LLM Usage:** Medium (interpreting risk scenarios)  
**Estimated Calls/Run:** 2-3

---

#### Agent 5: ExecutionAgent
**Role:** Head of Trading Desk  
**Goal:** Execute approved trades with precision  
**Backstory:** "You translate decisions into action. Every order must be perfect."

**Tools:**
- `place_market_order(symbol, qty, side)` → Order confirmation
- `verify_order_fill(order_id)` → Fill status
- `log_trade_execution(order_details)` → Database entry

**Output Format:**
```python
{
	"execution_status": "SUCCESS",
	"order_id": "abc-123-def",
	"symbol": "SPY",
	"side": "BUY",
	"qty": 10,
	"filled_avg_price": 450.52,
	"timestamp": "2025-10-28T14:30:00Z",
	"error": None
}
```

**LLM Usage:** Minimal (only for error logging)  
**Estimated Calls/Run:** 1-2

---

## 3. Total LLM Call Budget per Crew Run

| Agent | Calls per Run | Cumulative |
|-------|---------------|------------|
| DataCollector | 1-2 | 2 |
| SignalGenerator | 2-3 | 5 |
| SignalValidator | 3-4 | 9 |
| RiskManager | 2-3 | 12 |
| Execution | 1-2 | 14 |

**Total: ~14 LLM calls per crew execution**

**Daily Budget:** 14 calls/run × 3 runs/day = **42 calls/day**  
**Gemini Flash Limit:** 250 calls/day  
**Safety Margin:** 208 calls (83% buffer) ✅

---

## 4. Optimization Strategies

### Reduce LLM Dependency
- **Pre-compute indicators:** Use pure Python/NumPy (no LLM)
- **Rule-based validation:** Simple if/else logic (no LLM)
- **Only use LLM for:** Error interpretation, complex reasoning

### Caching Strategy
```python
@lru_cache(maxsize=128)
def get_agent_response(agent_id, task_hash):
	# Cache agent responses for identical inputs
	pass
```

### Rate Limiting
```python
class GeminiRateLimiter:
	def __init__(self, rpm=10, rpd=250):
		self.rpm = rpm
		self.rpd = rpd
		# Token bucket implementation
```

---

## 5. Testing Strategy

### Unit Tests (Per Agent)
- Test each tool independently
- Mock LLM responses
- Validate output formats

### Integration Tests
- Test full crew execution
- Use real Alpaca paper trading
- Monitor LLM call count

### Backtesting
- Historical data simulation
- Performance metrics:
  - Win rate (target: >55%)
  - Profit factor (target: >1.5)
  - Max drawdown (target: <10%)
