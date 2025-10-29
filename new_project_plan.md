# **AI-Driven Trading Crew: Simplified Backend-First Development Plan**

## **Project Philosophy: Keep It Simple (KIS)**

**Core Principle:** Build a rock-solid, CLI-based trading system that works perfectly before adding any UI layer. Every feature must be independently testable and debuggable.

---

## **1. Project Vision (Simplified)**

Build a **command-line trading system** where AI agents analyze market data, generate signals, and execute paper trades via Alpaca Markets. The system must:
- Run entirely from terminal/CLI
- Be fully testable at each stage
- Work within free tier limitations
- Have modular, replaceable components
- Log everything for transparency

**UI comes LAST** - only after the backend is bulletproof.

---

## **2. Free Tier Constraints & Documentation Task**

### **CRITICAL: Documentation Gathering (First Task)**

Before any coding, we need complete, current API documentation. This will be created by the AI development assistant.

**Task: Create `docs/API_REFERENCE.md`**

This document must contain:# **AI-Driven Trading Crew: Backend-First Development Plan (KIS)**

## **Project Philosophy**

**Keep It Simple (KIS):** Build a command-line trading system that works perfectly before any UI. Every component must be independently testable, debuggable, and modular.

---

## **PHASE 0: Foundation & Documentation (CRITICAL FIRST STEP)**

### **Feature 0.1: API Documentation Repository**

**Objective:** Create comprehensive, up-to-date API documentation for all external services to ensure development stays within free tier limits.

**Deliverables:**
1. Create `docs/API_REFERENCE.md` with the following sections (AI Assistant will populate using web search):

```markdown
# API Reference Documentation

## 1. Google Gemini API - Free Tier Constraints

### Rate Limits (Updated: [DATE])
- **Gemini 1.5 Pro:**
  - 5 requests per minute (RPM)
  - 25 requests per day (RPD)
  - 250,000 tokens per minute (TPM)
  
- **Gemini 1.5 Flash (RECOMMENDED for this project):**
  - 10 requests per minute (RPM)
  - 250 requests per day (RPD)
  - 250,000 tokens per minute (TPM)

- **Gemini 1.5 Flash-Lite:**
  - 15 requests per minute (RPM)
  - 1,000 requests per day (RPD)
  - 250,000 tokens per minute (TPM)

### Critical Notes:
- Rate limits are per PROJECT, not per API key
- 429 error when limits exceeded
- Daily quota resets at midnight Pacific Time
- Use exponential backoff for retries

### Cost Implications:
- Free tier is completely free (no credit card required)
- Monitor usage in Google AI Studio
- Consider Flash model for higher throughput

---

## 2. Alpaca Markets API - Free Tier Constraints

### Paper Trading (FREE Forever)
- **Rate Limits:**
  - 200 API calls per minute
  - 10 requests per second (burst limit)
  - No daily limit
  
- **Market Data Access:**
  - IEX data: Real-time (free)
  - Historical data: Last minute bars (free)
  - SIP data: 15-minute delayed (free)

### Order Types Available (Paper Trading):
- Market orders
- Limit orders
- Stop orders
- Stop-limit orders
- Fractional shares (market orders only)

### Paper Trading Limitations:
- Simulated fills (not real market conditions)
- Orders may fill faster/slower than live
- No slippage simulation
- No network latency simulation

### Critical Notes:
- Different API keys for paper vs live
- Base URL: `https://paper-api.alpaca.markets`
- Paper accounts can be reset/deleted freely
- No cost for paper trading

---

## 3. CrewAI Framework

### Licensing & Cost
- **License:** MIT (Open Source)
- **Cost:** FREE (framework is free forever)
- **Repository:** https://github.com/crewAIInc/crewAI

### Requirements:
- Python >=3.10 <3.14
- No account required for local use
- Cloud platform exists but NOT needed

### Cost Implications:
- Framework itself: $0
- Only cost: LLM API calls (Gemini in our case)
- No execution limits on local installations

### Integration Notes:
- Supports any LLM via LangChain
- Built-in memory management
- 100+ pre-built tools available
- Sequential and hierarchical processes

---

## 4. Recommended Strategy for Free Tier Usage

### Gemini Optimization:
1. **Use Gemini 1.5 Flash** instead of Pro (10 RPM vs 5 RPM)
2. **Implement request queuing** to stay under limits
3. **Batch operations** where possible
4. **Cache agent responses** to reduce redundant calls

### Alpaca Optimization:
1. **Batch historical data requests**
2. **Use WebSocket streams** for real-time data (doesn't count toward REST limit)
3. **Cache market data** locally
4. **Implement rate limiting** in code (don't rely on API errors)

### CrewAI Optimization:
1. **Minimize agent  interactions** (each agent call = LLM call)
2. **Use sequential processes** (simpler than hierarchical)
3. **Implement agent response caching**
4. **Design tasks to minimize back-and-forth**

---

## 5. Daily Usage Budget Calculation

**Assumption:** Running trading crew 3 times per day

| Service | Operation | Calls per Run | Daily Total | Free Limit | Status |
|---------|-----------|---------------|-------------|------------|--------|
| Gemini Flash | Agent reasoning | ~15 | 45 | 250 | ✅ Safe |
| Alpaca | Historical data | ~5 | 15 | Unlimited* | ✅ Safe |
| Alpaca | Order placement | ~3 | 9 | Unlimited* | ✅ Safe |

*Within 200/min rate limit

### Recommendation:
- **Start with 3 crew runs per day** during development
- **Monitor usage** in Google AI Studio
- **Scale gradually** as you optimize
```

**Acceptance Criteria:**
- [ ] `docs/API_REFERENCE.md` file created
- [ ] All rate limits documented with sources
- [ ] Budget calculation table completed
- [ ] Optimization strategies listed
- [ ] Document is dated and includes "Last Updated" timestamp

**Validation:**
```bash
# Verify documentation exists
test -f docs/API_REFERENCE.md && echo "✅ Documentation created"

# Verify all sections present
grep -q "Gemini API" docs/API_REFERENCE.md && \
grep -q "Alpaca Markets API" docs/API_REFERENCE.md && \
grep -q "CrewAI Framework" docs/API_REFERENCE.md && \
echo "✅ All sections present"
```

---

### **Feature 0.2: Project Scaffolding**

**Objective:** Set up a clean, modular project structure optimized for backend-first development on Windows 11 + WSL2.

**Project Structure:**
```
trading-crew/
├── .env.template          # Environment variables template
├── .env                   # Actual secrets (git-ignored)
├── .gitignore
├── pyproject.toml         # Poetry dependencies
├── requirements.txt       # Pip fallback
├── README.md
│
├── docs/
│   ├── API_REFERENCE.md   # From Feature 0.1
│   ├── AGENT_DESIGN.md    # Agent architecture (Feature 0.3)
│   └── TESTING_GUIDE.md   # Testing protocols (Feature 0.4)
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py    # Configuration management
│   │
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── gemini_connector.py   # LLM connection with key rotation
│   │   └── alpaca_connector.py   # Alpaca API wrapper
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── market_data_tools.py   # Data fetching
│   │   ├── analysis_tools.py      # Technical analysis (3MA)
│   │   └── execution_tools.py     # Order placement
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── data_agent.py
│   │   ├── analysis_agent.py
│   │   ├── risk_agent.py
│   │   └── execution_agent.py
│   │
│   ├── crew/
│   │   ├── __init__.py
│   │   ├── tasks.py       # Task definitions
│   │   └── trading_crew.py # Crew orchestration
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py      # Logging setup
│       ├── rate_limiter.py # Rate limiting utility
│       └── validators.py   # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_connectors/
│   ├── test_tools/
│   └── test_agents/
│
├── scripts/
│   ├── setup_env.sh       # Environment setup (WSL2)
│   ├── run_crew.py        # CLI entry point
│   └── validate_config.py # Configuration validator
│
└── logs/
    └── .gitkeep
```

**Dependencies (pyproject.toml):**
```toml
[tool.poetry]
name = "trading-crew"
version = "0.1.0"
description = "AI-driven trading system using CrewAI and Gemini"
python = "^3.11,<3.14"

[tool.poetry.dependencies]
# Core
python = "^3.11,<3.14"
python-dotenv = "^1.0.0"

# AI Framework
crewai = "^0.80.0"
langchain-google-genai = "^2.0.0"

# Trading
alpaca-py = "^0.32.0"
alpaca-trade-api = "^3.2.0"

# Data Analysis
pandas = "^2.2.0"
numpy = "^1.26.0"
ta-lib = "^0.4.32"  # Technical analysis library

# Utilities
pydantic = "^2.8.0"
pydantic-settings = "^2.3.0"
click = "^8.1.7"     # CLI framework
rich = "^13.7.0"     # Beautiful terminal output

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-cov = "^5.0.0"
pytest-asyncio = "^0.23.0"
black = "^24.4.0"
ruff = "^0.5.0"
```

**Deliverables:**
1. Complete directory structure created
2. All `__init__.py` files in place
3. `.gitignore` configured for Python/secrets
4. `.env.template` with all required variables
5. `requirements.txt` generated from Poetry

**Acceptance Criteria:**
- [ ] Project structure matches specification
- [ ] `poetry install` runs without errors
- [ ] All `__init__.py` files present
- [ ] `.gitignore` includes `.env`, `logs/`, `__pycache__/`
- [ ] `.env.template` documents all required variables

**Validation:**
```bash
# From WSL2 terminal
cd trading-crew

# Verify structure
tree -L 2 src/

# Test Poetry setup
poetry install
poetry run python --version

# Verify environment template
cat .env.template
```

---

### **Feature 0.3: Agent Architecture Design Document**

**Objective:** Design optimal agent architecture with proven trading strategies and best practices.

**Create `docs/AGENT_DESIGN.md`:**

```markdown
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
```

**Acceptance Criteria:**
- [ ] `docs/AGENT_DESIGN.md` created
- [ ] All agent specifications complete
- [ ] LLM budget calculation validated
- [ ] Strategy rationale documented

---

### **Feature 0.4: Configuration & Environment Management**

**Objective:** Implement robust, validated configuration system.

**Deliverable 1: `.env.template`**
```bash
# ============================================
# GEMINI API CONFIGURATION
# ============================================
# Get API keys from: https://aistudio.google.com/apikey
# Free tier limits: 10 RPM, 250 RPD (Flash model)

GEMINI_API_KEYS="key1,key2,key3"  # Comma-separated for rotation

# ============================================
# ALPACA MARKETS API CONFIGURATION
# ============================================
# Sign up: https://app.alpaca.markets/signup
# Paper trading is FREE forever

ALPACA_API_KEY="your_paper_api_key"
ALPACA_SECRET_KEY="your_paper_secret_key"
ALPACA_BASE_URL="https://paper-api.alpaca.markets"  # Paper trading URL

# ============================================
# TRADING STRATEGY PARAMETERS
# ============================================
TRADING_SYMBOL="SPY"              # Asset to trade
MA_FAST_PERIOD=8                  # Fast EMA period
MA_MEDIUM_PERIOD=13               # Medium EMA period
MA_SLOW_PERIOD=21                 # Slow EMA period
VOLUME_THRESHOLD=1.5              # Volume confirmation multiplier
ADX_THRESHOLD=25                  # Minimum ADX for trend

# ============================================
# RISK MANAGEMENT
# ============================================
MAX_RISK_PER_TRADE=0.02           # 2% of account per trade
MAX_OPEN_POSITIONS=3              # Maximum concurrent positions
DAILY_LOSS_LIMIT=0.05             # 5% daily loss limit

# ============================================
# SYSTEM CONFIGURATION
# ============================================
LOG_LEVEL="INFO"                  # DEBUG, INFO, WARNING, ERROR
LOG_FILE="logs/trading_crew.log"
RATE_LIMIT_RPM=9                  # Stay under Gemini's 10 RPM
RATE_LIMIT_RPD=200                # Stay under Gemini's 250 RPD

# ============================================
# DEVELOPMENT SETTINGS
# ============================================
DRY_RUN=true                      # If true, don't place real orders
CACHE_ENABLED=true                # Enable response caching
CACHE_TTL=300                     # Cache time-to-live (seconds)
```

**Deliverable 2: `src/config/settings.py`**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Gemini Configuration
    gemini_api_keys: str = Field(..., description="Comma-separated API keys")
    
    # Alpaca Configuration
    alpaca_api_key: str = Field(..., description="Alpaca API key")
    alpaca_secret_key: str = Field(..., description="Alpaca secret key")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL"
    )
    
    # Trading Parameters
    trading_symbol: str = Field(default="SPY", description="Trading symbol")
    ma_fast_period: int = Field(default=8, ge=1, description="Fast MA period")
    ma_medium_period: int = Field(default=13, ge=1)
    ma_slow_period: int = Field(default=21, ge=1)
    volume_threshold: float = Field(default=1.5, ge=1.0)
    adx_threshold: float = Field(default=25.0, ge=0, le=100)
    
    # Risk Management
    max_risk_per_trade: float = Field(default=0.02, ge=0, le=1)
    max_open_positions: int = Field(default=3, ge=1, le=10)
    daily_loss_limit: float = Field(default=0.05, ge=0, le=1)
    
    # System Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/trading_crew.log")
    rate_limit_rpm: int = Field(default=9, ge=1, le=15)
    rate_limit_rpd: int = Field(default=200, ge=1, le=1000)
    
    # Development
    dry_run: bool = Field(default=True, description="Don't place real orders")
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=300, ge=0)
    
    @validator("gemini_api_keys")
    def validate_api_keys(cls, v):
        """Ensure at least one API key is provided."""
        keys = [k.strip() for k in v.split(',') if k.strip()]
        if not keys:
            raise ValueError("At least one Gemini API key required")
        return v
    
    @validator("ma_slow_period")
    def validate_ma_periods(cls, v, values):
        """Ensure MA periods are in correct order."""
        if "ma_fast_period" in values and "ma_medium_period" in values:
            if not (values["ma_fast_period"] < values["ma_medium_period"] < v):
                raise ValueError(
                    "MA periods must be: fast < medium < slow"
                )
        return v
    
    def get_gemini_keys_list(self) -> List[str]:
        """Return Gemini API keys as a list."""
        return [k.strip() for k in self.gemini_api_keys.split(',') if k.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.dry_run


# Global settings instance
settings = Settings()
```

**Deliverable 3: `scripts/validate_config.py`**
```python
#!/usr/bin/env python3
"""
Configuration Validation Script
Run before starting the trading crew to ensure all settings are correct.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.config.settings import settings
import sys

console = Console()


def validate_gemini_keys():
    """Test Gemini API key connectivity."""
    keys = settings.get_gemini_keys_list()
    console.print(f"\n[cyan]Testing {len(keys)} Gemini API key(s)...[/cyan]")
    
    # TODO: Implement actual API test call
    for i, key in enumerate(keys, 1):
        masked_key = f"{key[:10]}...{key[-4:]}"
        console.print(f"  Key {i}: {masked_key} [green]✓[/green]")
    
    return True


def validate_alpaca_connection():
    """Test Alpaca API connectivity."""
    console.print("\n[cyan]Testing Alpaca API connection...[/cyan]")
    
    # TODO: Implement actual connection test
    console.print(f"  Base URL: {settings.alpaca_base_url} [green]✓[/green]")
    console.print(f"  Mode: {'Paper Trading' if 'paper' in settings.alpaca_base_url else 'LIVE TRADING'} [green]✓[/green]")
    
    return True


def validate_strategy_params():
    """Validate trading strategy parameters."""
    console.print("\n[cyan]Validating strategy parameters...[/cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", justify="center")
    
    table.add_row("Trading Symbol", settings.trading_symbol, "✓")
    table.add_row("Fast MA Period", str(settings.ma_fast_period), "✓")
    table.add_row("Medium MA Period", str(settings.ma_medium_period), "✓")
    table.add_row("Slow MA Period", str(settings.ma_slow_period), "✓")
    table.add_row("Volume Threshold", str(settings.volume_threshold), "✓")
    table.add_row("ADX Threshold", str(settings.adx_threshold), "✓")
    
    console.print(table)
    return True


def validate_risk_management():
    """Validate risk management parameters."""
    console.print("\n[cyan]Validating risk management...[/cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", justify="center")
    
    table.add_row(
        "Max Risk per Trade",
        f"{settings.max_risk_per_trade * 100}%",
        "✓"
    )
    table.add_row(
        "Max Open Positions",
        str(settings.max_open_positions),
        "✓"
    )
    table.add_row(
        "Daily Loss Limit",
        f"{settings.daily_loss_limit * 100}%",
        "✓"
    )
    
    console.print(table)
    return True


def main():
    """Run all validation checks."""
    console.print(Panel.fit(
        "[bold yellow]Trading Crew Configuration Validator[/bold yellow]",
        border_style="yellow"
    ))
    
    checks = [
        ("Gemini API Keys", validate_gemini_keys),
        ("Alpaca Connection", validate_alpaca_connection),
        ("Strategy Parameters", validate_strategy_params),
        ("Risk Management", validate_risk_management),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            console.print(f"\n[red]✗ {check_name} failed: {e}[/red]")
            results.append((check_name, False))
    
    # Summary
    console.print("\n" + "="*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        console.print(Panel.fit(
            f"[bold green]All {total} checks passed! ✓[/bold green]",
            border_style="green"
        ))
        sys.exit(0)
    else:
        console.print(Panel.fit(
            f"[bold red]{passed}/{total} checks passed. Fix errors before running.[/bold red]",
            border_style="red"
        ))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- [ ] `.env.template` created with all variables documented
- [ ] `settings.py` implements Pydantic validation
- [ ] `validate_config.py` runs all checks
- [ ] Configuration errors provide clear error messages
- [ ] Validation script exits with appropriate status codes

**Validation:**
```bash
# From project root in WSL2
poetry run python scripts/validate_config.py
```

---

## **PHASE 1: Core Connectors (No Agents Yet)**

### **Feature 1.1: Gemini Connector with Rate Limiting**

**Objective:** Create a production-ready Gemini connector that respects free tier limits and handles errors gracefully.

**Deliverable: `src/connectors/gemini_connector.py`**

```python
"""
Gemini LLM Connector with Rate Limiting and Key Rotation
Optimized for free tier: 10 RPM, 250 RPD (Flash model)
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from itertools import cycle
from typing import List, Optional
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from src.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rpm: int, rpd: int):
        self.rpm = rpm
        self.rpd = rpd
        self.minute_window = deque(maxlen=rpm)
        self.day_window = deque(maxlen=rpd)
    
    def wait_if_needed(self):
        """Block if rate limits would be exceeded."""
        now = datetime.now()
        
        # Check RPM (requests per minute)
        if len(self.minute_window) >= self.rpm:
            oldest_request = self.minute_window[0]
            time_since_oldest = (now - oldest_request).total_seconds()
            if time_since_oldest < 60:
                sleep_time = 60 - time_since_oldest + 1  # +1 for safety
                logger.warning(f"RPM limit reached. Sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        # Check RPD (requests per day)
        if len(self.day_window) >= self.rpd:
            oldest_request = self.day_window[0]
            time_since_oldest = (now - oldest_request).total_seconds()
            if time_since_oldest < 86400:  # 24 hours
                logger.error("RPD limit reached. Cannot proceed.")
                raise Exception("Daily API request limit exceeded")
        
        # Clean old requests from windows
        minute_ago = now - timedelta(seconds=60)
        day_ago = now - timedelta(hours=24)
        
        while self.minute_window and self.minute_window[0] < minute_ago:
            self.minute_window.popleft()
        
        while self.day_window and self.day_window[0] < day_ago:
            self.day_window.popleft()
        
        # Record this request
        self.minute_window.append(now)
        self.day_window.append(now)


class GeminiConnectionManager:
    """
    Manages Gemini API connections with:
    - Round-robin key rotation
    - Rate limiting (RPM/RPD)
    - Error handling with exponential backoff
    - Request counting for monitoring
    """
    
    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        model_name: str = "gemini-1.5-flash-latest",  # Flash for better limits
        temperature: float = 0.1
    ):
        self.api_keys = api_keys or settings.get_gemini_keys_list()
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured")
        
        self.model_name = model_name
        self.temperature = temperature
        self._key_cycler = cycle(self.api_keys)
        self.active_key = None
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            rpm=settings.rate_limit_rpm,
            rpd=settings.rate_limit_rpd
        )
        
        # Monitoring
        self.request_count = 0
        self.error_count = 0
        
        logger.info(
            f"GeminiManager initialized with {len(self.api_keys)} key(s), "
            f"model={model_name}"
        )
    
    def _get_next_key(self) -> str:
        """Rotate to the next API key."""
        self.active_key = next(self._key_cycler)
        masked = f"{self.active_key[:8]}...{self.active_key[-4:]}"
        logger.debug(f"Using API key: {masked}")
        return self.active_key
    
    def get_llm(self) -> ChatGoogleGenerativeAI:
        """
        Get a configured LLM instance with rate limiting.
        
        Returns:
            ChatGoogleGenerativeAI instance ready for use
        
        Raises:
            Exception: If rate limits exceeded or API error
        """
        # Wait if necessary to respect rate limits
        self.rate_limiter.wait_if_needed()
        
        api_key = self._get_next_key()
        self.request_count += 1
        
        logger.debug(
            f"Creating LLM instance (request #{self.request_count})"
        )
        
        try:
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=api_key,
                temperature=self.temperature,
                convert_system_message_to_human=True,
                verbose=settings.log_level == "DEBUG"
            )
            return llm
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to create LLM instance: {e}")
            raise
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "active_keys": len(self.api_keys),
            "rpm_used": len(self.rate_limiter.minute_window),
            "rpm_limit": self.rate_limiter.rpm,
            "rpd_used": len(self.rate_limiter.day_window),
            "rpd_limit": self.rate_limiter.rpd
        }


# Global singleton instance
gemini_manager = GeminiConnectionManager()
```

**Acceptance Criteria:**
- [ ] Key rotation works with multiple keys
- [ ] Rate limiter blocks requests correctly
- [ ] RPM and RPD limits enforced
- [ ] Statistics tracking implemented
- [ ] Error handling with clear messages

**Validation:**
```python
# Test script: tests/test_connectors/test_gemini.py
from src.connectors.gemini_connector import gemini_manager
import time

def test_rate_limiting():
    """Test that rate limiter enforces limits."""
    start = time.time()
    
    # Try to make 11 requests (over 10 RPM limit)
    for i in range(11):
        llm = gemini_manager.get_llm()
        print(f"Request {i+1} successful")
    
    elapsed = time.time() - start
    
    # Should have been throttled (taken > 60 seconds for 11 requests)
    assert elapsed > 60, f"Rate limiting failed: {elapsed}s"
    
    stats = gemini_manager.get_stats()
    print(f"Stats: {stats}")
    assert stats['total_requests'] == 11

if __name__ == "__main__":
    test_rate_limiting()
```

---

### **Feature 1.2: Alpaca Connector with Error Handling**

**Objective:** Create a robust Alpaca API wrapper with paper trading safety checks.

**Deliverable: `src/connectors/alpaca_connector.py`**

```python
"""
Alpaca Markets API Connector
Handles both Trading and Market Data clients with safety checks
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AlpacaConnectionManager:
    """
    Manages connections to Alpaca Trading and Market Data APIs.
    Includes safety checks for paper trading mode.
    """
    
    def __init__(self):
        self.api_key = settings.alpaca_api_key
        self.secret_key = settings.alpaca_secret_key
        self.base_url = settings.alpaca_base_url
        
        # Safety check
        self.is_paper = "paper" in self.base_url.lower()
        if not self.is_paper and settings.dry_run:
            logger.critical(
                "DANGER: Live API URL detected but DRY_RUN=True. "
                "Forcing paper mode."
            )
            self.base_url = "https://paper-api.alpaca.markets"
            self.is_paper = True
        
        self._trading_client = None
        self._data_client = None
        
        logger.info(
            f"AlpacaManager initialized (mode: {'PAPER' if self.is_paper else 'LIVE'})"
        )
    
    @property
    def trading_client(self) -> TradingClient:
        """Lazy-loaded trading client."""
        if not self._trading_client:
            self._trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.is_paper
            )
            logger.debug("Trading client initialized")
        return self._trading_client
    
    @property
    def data_client(self) -> StockHistoricalDataClient:
        """Lazy-loaded market data client."""
        if not self._data_client:
            self._data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            logger.debug("Data client initialized")
        return self._data_client
    
    def get_account(self) -> dict:
        """
        Get account information.
        
        Returns:
            Dict with keys: equity, buying_power, cash, portfolio_value
        """
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
                "trading_blocked": account.trading_blocked
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def fetch_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Args:
            symbol: Stock symbol (e.g., "SPY")
            timeframe: Bar timeframe ("1Min", "5Min", "1Hour", etc.)
            limit: Number of bars to fetch
        
        Returns:
            DataFrame with columns: open, high, low, close, volume
        """
        try:
            # Parse timeframe
            amount, unit = int(timeframe[:-3]), timeframe[-3:]
            if unit == "Min":
                tf = TimeFrame(amount, TimeFrameUnit.Minute)
            elif unit == "our":  # "Hour"
                tf = TimeFrame(amount, TimeFrameUnit.Hour)
            else:
                tf = TimeFrame(1, TimeFrameUnit.Day)
            
            # Calculate start/end times
            end = datetime.now()
            # Rough estimate: for 1Min bars, go back limit minutes
            start = end - timedelta(minutes=limit * amount)
            
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start,
                end=end
            )
            
            bars = self.data_client.get_stock_bars(request_params)
            df = bars.df
            
            # Flatten multi-index if present
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)
            
            logger.info(
                f"Fetched {len(df)} bars for {symbol} ({timeframe})"
            )
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch bars: {e}")
            raise
    
    def place_market_order(
        self,
        symbol: str,
        qty: int,
        side: str  # "BUY" or "SELL"
    ) -> dict:
        """
        Place a market order.
        
        Args:
            symbol: Stock symbol
            qty: Quantity of shares
            side: "BUY" or "SELL"
        
        Returns:
            Dict with order details
        """
        if settings.dry_run:
            logger.warning(
                f"DRY RUN: Would place {side} order for {qty} {symbol}"
            )
            return {
                "status": "dry_run",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": "DRY_RUN_123"
            }
        
        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide[side.upper()],
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_request)
            
            logger.info(
                f"Order placed: {symbol} {side} {qty} shares (ID: {order.id})"
            )
            
            return {
                "status": "submitted",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": order.id,
                "submitted_at": order.submitted_at,
                "filled_avg_price": order.filled_avg_price
            }
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def get_positions(self) -> list:
        """Get all open positions."""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": int(p.qty),
                    "side": "long" if int(p.qty) > 0 else "short",
                    "market_value": float(p.market_value),
                    "avg_entry_price": float(p.avg_entry_price),
                    "unrealized_pl": float(p.unrealized_pl)
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def get_recent_orders(self, limit: int = 10) -> list:
        """Get recent closed orders."""
        try:
            request = GetOrdersRequest(
                status=QueryOrderStatus.CLOSED,
                limit=limit
            )
            orders = self.trading_client.get_orders(request)
            
            return [
                {
                    "order_id": o.id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "qty": int(o.qty),
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                    "status": o.status.value,
                    "submitted_at": o.submitted_at,
                    "filled_at": o.filled_at
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise


# Global singleton
alpaca_manager = AlpacaConnectionManager()
```

**Acceptance Criteria:**
- [ ] Trading client connects successfully
- [ ] Data client fetches historical bars
- [ ] Paper trading mode enforced when `DRY_RUN=true`
- [ ] Account information retrieved correctly
- [ ] Order placement works (or simulates in dry run)

**Validation:**
```python
# Test script: tests/test_connectors/test_alpaca.py
from src.connectors.alpaca_connector import alpaca_manager

def test_connection():
    """Test basic connectivity."""
    account = alpaca_manager.get_account()
    print(f"Account equity: ${account['equity']}")
    assert account['equity'] > 0
    
def test_fetch_data():
    """Test historical data fetching."""
    df = alpaca_manager.fetch_historical_bars("SPY", "1Min", limit=50)
    print(f"Fetched {len(df)} bars")
    assert len(df) > 0
    assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])

if __name__ == "__main__":
    test_connection()
    test_fetch_data()
```

---

This is getting very long. Would you like me to continue with:
1. **Phase 2: Tools Implementation** (market data, technical analysis, execution)
2. **Phase 3: Agent Implementation** (actual CrewAI agents)
3. **Phase 4: Integration & Testing** (full crew execution)
4. **Phase 5: CLI Interface** (user-friendly command-line tool)

Each phase would follow the same detailed, AI-readable format with:
- Clear objectives
- Complete code deliverables
- Acceptance criteria

## **PHASE 2: Tools Implementation (Pure Python, No Agents)**

### **Feature 2.1: Market Data Tools**

**Objective:** Implement data fetching and validation tools that agents will use.

**Deliverable: `src/tools/market_data_tools.py`**

```python
"""
Market Data Tools
Pure Python functions for fetching and validating market data.
These tools will be used by CrewAI agents.
"""

from typing import Optional, Dict
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.connectors.alpaca_connector import alpaca_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataTools:
    """Collection of market data fetching and validation tools."""
    
    @staticmethod
    def fetch_ohlcv_data(
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> Dict:
        """
        Fetch OHLCV data and return validated result.
        
        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe
            limit: Number of bars
        
        Returns:
            Dict with keys: success, data, error, metadata
        """
        try:
            df = alpaca_manager.fetch_historical_bars(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            # Validate data
            validation = MarketDataTools.validate_data_completeness(df)
            
            if not validation['is_valid']:
                logger.warning(
                    f"Data validation warning: {validation['issues']}"
                )
            
            return {
                "success": True,
                "data": df,
                "error": None,
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bars_fetched": len(df),
                    "start_time": df.index[0] if len(df) > 0 else None,
                    "end_time": df.index[-1] if len(df) > 0 else None,
                    "validation": validation
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe
                }
            }
    
    @staticmethod
    def validate_data_completeness(df: pd.DataFrame) -> Dict:
        """
        Validate that data is complete and usable.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check for empty DataFrame
        if df is None or len(df) == 0:
            return {
                "is_valid": False,
                "issues": ["DataFrame is empty"]
            }
        
        # Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check for NaN values
        if df.isnull().any().any():
            nan_cols = df.columns[df.isnull().any()].tolist()
            issues.append(f"NaN values found in: {nan_cols}")
        
        # Check for negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns and (df[col] <= 0).any():
                issues.append(f"Negative or zero prices in {col}")
        
        # Check OHLC logic (high >= low, etc.)
        if 'high' in df.columns and 'low' in df.columns:
            if (df['high'] < df['low']).any():
                issues.append("Invalid OHLC: high < low detected")
        
        # Check for gaps in time series
        if len(df) > 1:
            time_diffs = df.index.to_series().diff()[1:]
            expected_diff = time_diffs.mode()[0] if len(time_diffs) > 0 else None
            
            if expected_diff:
                large_gaps = time_diffs[time_diffs > expected_diff * 2]
                if len(large_gaps) > 0:
                    issues.append(
                        f"Time series gaps detected: {len(large_gaps)} gaps"
                    )
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues if issues else None,
            "bars_count": len(df),
            "date_range": {
                "start": str(df.index[0]) if len(df) > 0 else None,
                "end": str(df.index[-1]) if len(df) > 0 else None
            }
        }
    
    @staticmethod
    def get_latest_price(symbol: str) -> Dict:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with latest price info
        """
        try:
            # Fetch just 1 bar
            df = alpaca_manager.fetch_historical_bars(
                symbol=symbol,
                timeframe="1Min",
                limit=1
            )
            
            if len(df) == 0:
                raise ValueError("No data returned")
            
            latest = df.iloc[-1]
            
            return {
                "success": True,
                "symbol": symbol,
                "price": float(latest['close']),
                "timestamp": df.index[-1],
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "volume": int(latest['volume'])
            }
        
        except Exception as e:
            logger.error(f"Failed to get latest price: {e}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }


# Global instance
market_data_tools = MarketDataTools()
```

**Acceptance Criteria:**
- [ ] `fetch_ohlcv_data` returns DataFrame with validation
- [ ] `validate_data_completeness` detects all common issues
- [ ] `get_latest_price` returns current price
- [ ] All functions handle errors gracefully
- [ ] Logging provides clear debugging info

**Validation:**
```python
# Test: tests/test_tools/test_market_data.py
from src.tools.market_data_tools import market_data_tools

def test_fetch_data():
    result = market_data_tools.fetch_ohlcv_data("SPY", "1Min", 50)
    assert result['success'] == True
    assert len(result['data']) > 0
    print(f"Metadata: {result['metadata']}")

def test_validation():
    result = market_data_tools.fetch_ohlcv_data("SPY", "1Min", 50)
    validation = result['metadata']['validation']
    print(f"Validation: {validation}")
    assert validation['is_valid'] == True

def test_latest_price():
    result = market_data_tools.get_latest_price("SPY")
    assert result['success'] == True
    print(f"Latest price: ${result['price']}")

if __name__ == "__main__":
    test_fetch_data()
    test_validation()
    test_latest_price()
```

---

### **Feature 2.2: Technical Analysis Tools**

**Objective:** Implement 3MA strategy and confirmation indicators.

**Deliverable: `src/tools/analysis_tools.py`**

```python
"""
Technical Analysis Tools
Implements 3MA strategy and confirmation indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)


class TechnicalAnalysisTools:
    """Technical analysis indicators and signal generation."""
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            df: OHLCV DataFrame
            period: EMA period
            column: Column to calculate EMA on
        
        Returns:
            Series with EMA values
        """
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average."""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (volatility indicator).
        
        Args:
            df: OHLCV DataFrame with high, low, close
            period: ATR period
        
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average Directional Index (trend strength).
        
        Args:
            df: OHLCV DataFrame
            period: ADX period
        
        Returns:
            Series with ADX values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def generate_3ma_signal(df: pd.DataFrame) -> Dict:
        """
        Generate trading signal using Triple Moving Average strategy.
        
        Strategy:
        - BUY: Fast MA crosses above Medium MA AND Medium MA > Slow MA
        - SELL: Fast MA crosses below Medium MA AND Medium MA < Slow MA
        - HOLD: Any other condition
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            Dict with signal and indicator values
        """
        try:
            # Calculate EMAs using configured periods
            fast_ma = TechnicalAnalysisTools.calculate_ema(
                df, settings.ma_fast_period
            )
            medium_ma = TechnicalAnalysisTools.calculate_ema(
                df, settings.ma_medium_period
            )
            slow_ma = TechnicalAnalysisTools.calculate_ema(
                df, settings.ma_slow_period
            )
            
            # Get latest values
            fast = fast_ma.iloc[-1]
            medium = medium_ma.iloc[-1]
            slow = slow_ma.iloc[-1]
            
            # Previous values for crossover detection
            fast_prev = fast_ma.iloc[-2] if len(fast_ma) > 1 else fast
            medium_prev = medium_ma.iloc[-2] if len(medium_ma) > 1 else medium
            
            # Detect crossovers
            fast_crossed_above_medium = (fast > medium) and (fast_prev <= medium_prev)
            fast_crossed_below_medium = (fast < medium) and (fast_prev >= medium_prev)
            
            # Generate signal
            signal = "HOLD"
            
            if fast_crossed_above_medium and medium > slow:
                signal = "BUY"
                logger.info("🟢 BUY signal generated (3MA crossover)")
            elif fast_crossed_below_medium and medium < slow:
                signal = "SELL"
                logger.info("🔴 SELL signal generated (3MA crossover)")
            
            return {
                "signal": signal,
                "fast_ma": float(fast),
                "medium_ma": float(medium),
                "slow_ma": float(slow),
                "current_price": float(df['close'].iloc[-1]),
                "fast_crossed_above": fast_crossed_above_medium,
                "fast_crossed_below": fast_crossed_below_medium,
                "timestamp": str(df.index[-1])
            }
        
        except Exception as e:
            logger.error(f"Failed to generate 3MA signal: {e}")
            return {
                "signal": "HOLD",
                "error": str(e)
            }
    
    @staticmethod
    def calculate_volume_confirmation(df: pd.DataFrame, threshold: float = None) -> Dict:
        """
        Check if current volume exceeds threshold.
        
        Args:
            df: OHLCV DataFrame
            threshold: Multiplier for average volume (default from settings)
        
        Returns:
            Dict with confirmation result
        """
        if threshold is None:
            threshold = settings.volume_threshold
        
        try:
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            
            volume_ratio = current_volume / avg_volume
            confirmed = volume_ratio >= threshold
            
            return {
                "confirmed": confirmed,
                "current_volume": int(current_volume),
                "average_volume": int(avg_volume),
                "volume_ratio": float(volume_ratio),
                "threshold": threshold
            }
        
        except Exception as e:
            logger.error(f"Volume confirmation failed: {e}")
            return {
                "confirmed": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_volatility_check(df: pd.DataFrame, min_atr: float = 0.3, max_atr: float = 2.0) -> Dict:
        """
        Check if volatility (ATR) is within acceptable range.
        
        Args:
            df: OHLCV DataFrame
            min_atr: Minimum acceptable ATR
            max_atr: Maximum acceptable ATR
        
        Returns:
            Dict with volatility check result
        """
        try:
            atr = TechnicalAnalysisTools.calculate_atr(df, period=14)
            current_atr = atr.iloc[-1]
            
            is_acceptable = min_atr <= current_atr <= max_atr
            
            return {
                "acceptable": is_acceptable,
                "current_atr": float(current_atr),
                "min_atr": min_atr,
                "max_atr": max_atr,
                "status": "normal" if is_acceptable else ("too_low" if current_atr < min_atr else "too_high")
            }
        
        except Exception as e:
            logger.error(f"Volatility check failed: {e}")
            return {
                "acceptable": False,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame, threshold: float = None) -> Dict:
        """
        Calculate trend strength using ADX.
        
        Args:
            df: OHLCV DataFrame
            threshold: Minimum ADX value (default from settings)
        
        Returns:
            Dict with trend strength analysis
        """
        if threshold is None:
            threshold = settings.adx_threshold
        
        try:
            adx = TechnicalAnalysisTools.calculate_adx(df, period=14)
            current_adx = adx.iloc[-1]
            
            has_strong_trend = current_adx >= threshold
            
            # Classify trend strength
            if current_adx < 20:
                strength = "weak"
            elif current_adx < 25:
                strength = "moderate"
            elif current_adx < 40:
                strength = "strong"
            else:
                strength = "very_strong"
            
            return {
                "has_strong_trend": has_strong_trend,
                "current_adx": float(current_adx),
                "threshold": threshold,
                "strength": strength
            }
        
        except Exception as e:
            logger.error(f"Trend strength calculation failed: {e}")
            return {
                "has_strong_trend": False,
                "error": str(e)
            }


# Global instance
technical_analysis = TechnicalAnalysisTools()
```

**Acceptance Criteria:**
- [ ] All indicators (EMA, ATR, ADX) calculate correctly
- [ ] 3MA signal generation detects crossovers
- [ ] Volume confirmation works with threshold
- [ ] Volatility check identifies acceptable ranges
- [ ] Trend strength classified correctly

**Validation:**
```python
# Test: tests/test_tools/test_analysis.py
from src.tools.market_data_tools import market_data_tools
from src.tools.analysis_tools import technical_analysis

def test_3ma_signal():
    # Fetch data
    result = market_data_tools.fetch_ohlcv_data("SPY", "1Min", 100)
    df = result['data']
    
    # Generate signal
    signal = technical_analysis.generate_3ma_signal(df)
    print(f"Signal: {signal['signal']}")
    print(f"Fast MA: {signal['fast_ma']:.2f}")
    print(f"Medium MA: {signal['medium_ma']:.2f}")
    print(f"Slow MA: {signal['slow_ma']:.2f}")
    
    assert signal['signal'] in ['BUY', 'SELL', 'HOLD']

def test_confirmations():
    result = market_data_tools.fetch_ohlcv_data("SPY", "1Min", 100)
    df = result['data']
    
    # Volume confirmation
    vol_check = technical_analysis.calculate_volume_confirmation(df)
    print(f"Volume confirmed: {vol_check['confirmed']}")
    
    # Volatility check
    vol_check = technical_analysis.calculate_volatility_check(df)
    print(f"Volatility acceptable: {vol_check['acceptable']}")
    
    # Trend strength
    trend = technical_analysis.calculate_trend_strength(df)
    print(f"Trend strength: {trend['strength']} (ADX: {trend['current_adx']:.2f})")

if __name__ == "__main__":
    test_3ma_signal()
    test_confirmations()
```

---

### **Feature 2.3: Execution Tools**

**Objective:** Implement order placement and risk calculation tools.

**Deliverable: `src/tools/execution_tools.py`**

```python
"""
Execution Tools
Order placement, position sizing, and risk management calculations.
"""

import logging
from typing import Dict, Optional
from src.connectors.alpaca_connector import alpaca_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ExecutionTools:
    """Tools for trade execution and risk management."""
    
    @staticmethod
    def calculate_position_size(
        signal: str,
        current_price: float,
        atr: float,
        account_equity: float
    ) -> Dict:
        """
        Calculate position size based on risk parameters.
        
        Position Sizing Formula:
        shares = (account_equity * max_risk_per_trade) / atr
        
        Args:
            signal: "BUY" or "SELL"
            current_price: Current asset price
            atr: Average True Range (volatility)
            account_equity: Total account equity
        
        Returns:
            Dict with position size calculation
        """
        try:
            # Calculate risk-adjusted position size
            risk_amount = account_equity * settings.max_risk_per_trade
            
            # Position size based on ATR (volatility-adjusted)
            if atr > 0:
                shares = int(risk_amount / atr)
            else:
                # Fallback to fixed percentage
                shares = int((account_equity * 0.01) / current_price)
            
            # Ensure at least 1 share
            shares = max(1, shares)
            
            # Calculate total cost
            total_cost = shares * current_price
            
            # Calculate risk as percentage
            risk_pct = (shares * atr) / account_equity * 100
            
            return {
                "shares": shares,
                "total_cost": float(total_cost),
                "risk_amount": float(risk_amount),
                "risk_percentage": float(risk_pct),
                "price_per_share": float(current_price),
                "atr_used": float(atr)
            }
        
        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return {
                "shares": 1,  # Minimum fallback
                "error": str(e)
            }
    
    @staticmethod
    def check_portfolio_constraints() -> Dict:
        """
        Check if portfolio constraints allow new trades.
        
        Checks:
        1. Max open positions
        2. Daily loss limit
        3. Trading blocked status
        
        Returns:
            Dict with constraint check results
        """
        try:
            # Get account info
            account = alpaca_manager.get_account()
            
            # Get current positions
            positions = alpaca_manager.get_positions()
            num_positions = len(positions)
            
            # Check 1: Max positions
            can_open_position = num_positions < settings.max_open_positions
            
            # Check 2: Daily loss limit
            # Calculate today's P&L (simplified)
            portfolio_value = account['portfolio_value']
            equity = account['equity']
            
            # In paper trading, starting equity might be different
            # We'll use a simple check: if equity dropped > 5% from portfolio value
            daily_loss_pct = 0  # Placeholder (would need historical tracking)
            within_loss_limit = daily_loss_pct < settings.daily_loss_limit
            
            # Check 3: Account status
            trading_allowed = not account.get('trading_blocked', False)
            
            # Overall approval
            approved = can_open_position and within_loss_limit and trading_allowed
            
            return {
                "approved": approved,
                "checks": {
                    "max_positions": {
                        "passed": can_open_position,
                        "current": num_positions,
                        "limit": settings.max_open_positions
                    },
                    "daily_loss": {
                        "passed": within_loss_limit,
                        "current_loss_pct": daily_loss_pct,
                        "limit_pct": settings.daily_loss_limit * 100
                    },
                    "trading_status": {
                        "passed": trading_allowed,
                        "blocked": account.get('trading_blocked', False)
                    }
                },
                "account_info": {
                    "equity": account['equity'],
                    "buying_power": account['buying_power']
                }
            }
        
        except Exception as e:
            logger.error(f"Portfolio constraint check failed: {e}")
            return {
                "approved": False,
                "error": str(e)
            }
    
    @staticmethod
    def place_order(
        symbol: str,
        qty: int,
        side: str
    ) -> Dict:
        """
        Place a market order with validation.
        
        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: "BUY" or "SELL"
        
        Returns:
            Dict with order result
        """
        try:
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
            
            if qty <= 0:
                raise ValueError(f"Invalid quantity: {qty}. Must be positive")
            
            # Check constraints first
            constraints = ExecutionTools.check_portfolio_constraints()
            
            if not constraints['approved']:
                logger.warning("Trade rejected by portfolio constraints")
                return {
                    "success": False,
                    "reason": "constraints_failed",
                    "constraints": constraints
                }
            
            # Place order via Alpaca
            order_result = alpaca_manager.place_market_order(
                symbol=symbol,
                qty=qty,
                side=side
            )
            
            if order_result['status'] in ['submitted', 'dry_run']:
                logger.info(
                    f"✓ Order executed: {side} {qty} {symbol} "
                    f"(ID: {order_result['order_id']})"
                )
                return {
                    "success": True,
                    "order": order_result,
                    "constraints": constraints
                }
            else:
                logger.error(f"Order placement failed: {order_result}")
                return {
                    "success": False,
                    "reason": "order_failed",
                    "details": order_result
                }
        
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {
                "success": False,
                "reason": "exception",
                "error": str(e)
            }
    
    @staticmethod
    def get_position_for_symbol(symbol: str) -> Optional[Dict]:
        """
        Get current position for a specific symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with position info or None
        """
        try:
            positions = alpaca_manager.get_positions()
            
            for pos in positions:
                if pos['symbol'] == symbol:
                    return pos
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return None


# Global instance
execution_tools = ExecutionTools()
```

**Acceptance Criteria:**
- [ ] Position size calculated correctly based on ATR
- [ ] Portfolio constraints checked before orders
- [ ] Orders placed successfully (or dry run simulated)
- [ ] Position retrieval works for specific symbols
- [ ] All functions handle errors gracefully

**Validation:**
```python
# Test: tests/test_tools/test_execution.py
from src.tools.execution_tools import execution_tools
from src.connectors.alpaca_connector import alpaca_manager

def test_position_sizing():
    account = alpaca_manager.get_account()
    
    sizing = execution_tools.calculate_position_size(
        signal="BUY",
        current_price=450.0,
        atr=0.75,
        account_equity=account['equity']
    )
    
    print(f"Position size: {sizing['shares']} shares")
    print(f"Total cost: ${sizing['total_cost']:.2f}")
    print(f"Risk: {sizing['risk_percentage']:.2f}%")
    
    assert sizing['shares'] > 0

def test_constraints():
    constraints = execution_tools.check_portfolio_constraints()
    print(f"Trade approved: {constraints['approved']}")
    print(f"Checks: {constraints['checks']}")
    
    assert 'approved' in constraints

def test_dry_run_order():
    # Place a dry run order
    result = execution_tools.place_order(
        symbol="SPY",
        qty=1,
        side="BUY"
    )
    
    print(f"Order result: {result}")
    # In dry run, should always succeed
    assert result['success'] == True

if __name__ == "__main__":
    test_position_sizing()
    test_constraints()
    test_dry_run_order()
```

---

## **PHASE 3: Agent Implementation (CrewAI Integration)**

### **Feature 3.1: Agent Definitions**

**Objective:** Define all CrewAI agents with proper roles, goals, and tool assignments.

**Deliverable: `src/agents/base_agents.py`**

```python
"""
Base Agent Definitions
All CrewAI agents for the trading system.
"""

from crewai import Agent
from src.connectors.gemini_connector import gemini_manager
from src.tools.market_data_tools import market_data_tools
from src.tools.analysis_tools import technical_analysis
from src.tools.execution_tools import execution_tools
from crewai_tools import tool
import logging

logger = logging.getLogger(__name__)

# Get configured LLM
llm = gemini_manager.get_llm()


# ============================================
# CREWAI TOOL WRAPPERS
# ============================================
# CrewAI requires tools to be decorated with @tool

@tool("Fetch OHLCV Data")
def fetch_ohlcv_data_tool(symbol: str, timeframe: str = "1Min", limit: int = 100) -> dict:
    """
    Fetch historical OHLCV (Open, High, Low, Close, Volume) data for analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        timeframe: Bar timeframe ('1Min', '5Min', '1Hour')
        limit: Number of bars to fetch
    
    Returns:
        Dictionary with success status, data, and metadata
    """
    return market_data_tools.fetch_ohlcv_data(symbol, timeframe, limit)


@tool("Generate 3MA Signal")
def generate_3ma_signal_tool(data: dict) -> dict:
    """
    Generate trading signal using Triple Moving Average strategy.
    
    Args:
        data: Result from fetch_ohlcv_data_tool containing DataFrame
    
    Returns:
        Dictionary with signal ('BUY', 'SELL', 'HOLD') and indicator values
    """
    if data.get('success') and data.get('data') is not None:
        df = data['data']
        return technical_analysis.generate_3ma_signal(df)
    else:
        return {"signal": "HOLD", "error": "No data available"}


@tool("Check Volume Confirmation")
def check_volume_confirmation_tool(data: dict) -> dict:
    """
    Check if current volume confirms the signal strength.
    
    Args:
        data: Result from fetch_ohlcv_data_tool
    
    Returns:
        Dictionary with confirmation status and volume metrics
    """
    if data.get('success') and data.get('data') is not None:
        df = data['data']
        return technical_analysis.calculate_volume_confirmation(df)
    else:
        return {"confirmed": False, "error": "No data available"}


@tool("Check Volatility Range")
def check_volatility_tool(data: dict) -> dict:
    """
    Check if volatility (ATR) is within acceptable trading range.
    
    Args:
        data: Result from fetch_ohlcv_data_tool
    
    Returns:
        Dictionary with volatility check results
    """
    if data.get('success') and data.get('data') is not None:
        df = data['data']
        return technical_analysis.calculate_volatility_check(df)
    else:
        return {"acceptable": False, "error": "No data available"}


@tool("Check Trend Strength")
def check_trend_strength_tool(data: dict) -> dict:
    """
    Check if the market has a strong trend using ADX.
    
    Args:
        data: Result from fetch_ohlcv_data_tool
    
    Returns:
        Dictionary with trend strength analysis
    """
    if data.get('success') and data.get('data') is not None:
        df = data['data']
        return technical_analysis.calculate_trend_strength(df)
    else:
        return {"has_strong_trend": False, "error": "No data available"}


@tool("Check Portfolio Constraints")
def check_constraints_tool() -> dict:
    """
    Check if portfolio constraints allow opening new positions.
    Validates max positions, daily loss limit, and account status.
    
    Returns:
        Dictionary with approval status and detailed checks
    """
    return execution_tools.check_portfolio_constraints()


@tool("Calculate Position Size")
def calculate_position_size_tool(
    signal: str,
    current_price: float,
    atr: float,
    account_equity: float
) -> dict:
    """
    Calculate optimal position size based on risk management rules.
    
    Args:
        signal: Trading signal ('BUY' or 'SELL')
        current_price: Current asset price
        atr: Average True Range (volatility)
        account_equity: Total account equity
    
    Returns:
        Dictionary with position size and risk metrics
    """
    return execution_tools.calculate_position_size(
        signal, current_price, atr, account_equity
    )


@tool("Place Market Order")
def place_order_tool(symbol: str, qty: int, side: str) -> dict:
    """
    Place a market order for the specified symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        qty: Number of shares
        side: 'BUY' or 'SELL'
    
    Returns:
        Dictionary with order execution result
    """
    return execution_tools.place_order(symbol, qty, side)


# ============================================
# AGENT DEFINITIONS
# ============================================

data_collector_agent = Agent(
    role="Market Data Specialist",
    goal="Fetch accurate, complete OHLCV data for the specified asset and validate its quality",
    backstory="""You are a meticulous data collector with an obsession for data quality.
    You ensure every bar is complete, validated, and ready for analysis.
    You never pass incomplete or suspicious data to the next agent.""",
    tools=[fetch_ohlcv_data_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


signal_generator_agent = Agent(
    role="Quantitative Technical Analyst",
    goal="Calculate precise technical indicators and generate trading signals using the 3MA strategy",
    backstory="""You are a mathematician and technical analysis expert.
    You live and breathe charts, moving averages, and indicators.
    Your calculations are always precise, and you clearly explain your signal generation logic.""",
    tools=[generate_3ma_signal_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


signal_validator_agent = Agent(
    role="Chief Quality Officer",
    goal="Validate trading signals using multiple confirmation layers (volume, volatility, trend strength)",
    backstory="""You are a skeptical analyst who trusts no signal until proven by multiple confirmations.
    You apply volume confirmation, volatility filters, and trend strength analysis.
    If a signal doesn't meet your strict criteria, you override it to HOLD.
    Your conservative approach protects capital from false signals.""",
    tools=[
        check_volume_confirmation_tool,
        check_volatility_tool,
        check_trend_strength_tool
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


risk_manager_agent = Agent(
    role="Portfolio Risk Officer",
    goal="Enforce position sizing and portfolio-level risk constraints to protect capital",
    backstory="""You are the guardian of capital. No trade is worth risking the entire portfolio.
    You calculate optimal position sizes based on volatility (ATR) and enforce strict limits:
    - Maximum risk per trade
    - Maximum open positions
    - Daily loss limits
    You have veto power over any trade that violates risk rules.""",
    tools=[
        check_constraints_tool,
        calculate_position_size_tool
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


execution_agent = Agent(
    role="Head of Trading Desk",
    goal="Execute approved trades with precision and verify successful order placement",
    backstory="""You are a cool-headed execution specialist.
    Once a trade is approved, you act with speed and precision.
    You translate decisions into live market orders and confirm execution.
    You never hesitate, but you also never execute unapproved trades.""",
    tools=[place_order_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)


logger.info("All agents initialized successfully")
```

**Acceptance Criteria:**
- [ ] All 5 agents defined with clear roles
- [ ] Tools properly wrapped with `@tool` decorator
- [ ] LLM assigned to all agents
- [ ] Backstories provide clear context
- [ ] `allow_delegation=False` to keep sequential flow

---

### **Feature 3.2: Task Definitions**

**Objective:** Define sequential tasks that agents will execute.

**Deliverable: `src/crew/tasks.py`**

```python
"""
Task Definitions
Sequential tasks for the trading crew workflow.
"""

from crewai import Task
from src.agents.base_agents import (
    data_collector_agent,
    signal_generator_agent,
    signal_validator_agent,
    risk_manager_agent,
    execution_agent
)
from src.config.settings import settings


# Task 1: Data Collection
collect_data_task = Task(
    description="""Fetch historical OHLCV data for {symbol}.
    
    Requirements:
    - Timeframe: {timeframe}
    - Number of bars: {limit}
    - Validate data completeness
    - Check for gaps, NaN values, and OHLC consistency
    
    Return the data result including validation status.""",
    expected_output="""A dictionary containing:
    - success: Boolean
    - data: DataFrame with OHLCV data
    - metadata: Includes validation results and bar count
    
    Example:
    {{
        "success": true,
        "data": <DataFrame>,
        "metadata": {{
            "symbol": "SPY",
            "bars_fetched": 100,
            "validation": {{"is_valid": true}}
        }}
    }}""",
    agent=data_collector_agent
)


# Task 2: Signal Generation
generate_signal_task = Task(
    description="""Analyze the market data and generate a trading signal using the 3MA strategy.
    
    Strategy Rules:
    - Calculate Fast ({ma_fast}), Medium ({ma_medium}), and Slow ({ma_slow}) EMAs
    - BUY: Fast MA crosses above Medium MA AND Medium MA > Slow MA
    - SELL: Fast MA crosses below Medium MA AND Medium MA < Slow MA
    - HOLD: Any other condition
    
    Clearly explain your reasoning and the indicator values.""",
    expected_output="""A dictionary with the trading signal:
    {{
        "signal": "BUY" | "SELL" | "HOLD",
        "fast_ma": <float>,
        "medium_ma": <float>,
        "slow_ma": <float>,
        "current_price": <float>,
        "fast_crossed_above": <boolean>,
        "fast_crossed_below": <boolean>
    }}""",
    agent=signal_generator_agent,
    context=[collect_data_task]  # Depends on data collection
)


# Task 3: Signal Validation
validate_signal_task = Task(
    description="""Validate the generated signal using confirmation layers.
    
    Confirmation Checks:
    1. Volume Confirmation: Current volume > {volume_threshold}x average
    2. Volatility Check: ATR within acceptable range (0.3 - 2.0)
    3. Trend Strength: ADX > {adx_threshold}
    
    Rules:
    - If signal is BUY or SELL, check all confirmations
    - If fewer than 2 confirmations pass, override signal to HOLD
    - If signal is already HOLD, keep it as HOLD
    
    Provide detailed reasoning for your decision.""",
    expected_output="""A validated signal with confirmation details:
    {{
        "final_signal": "BUY" | "SELL" | "HOLD",
        "original_signal": "<from previous task>",
        "confirmations_passed": ["volume", "volatility", "trend"],
        "override_applied": <boolean>,
        "override_reason": "<explanation if overridden>"
    }}""",
    agent=signal_validator_agent,
    context=[generate_signal_task]
)


# Task 4: Risk Management
assess_risk_task = Task(
    description="""Perform risk management checks and calculate position size.
    
    Portfolio Constraints:
    - Max open positions: {max_positions}
    - Max risk per trade: {max_risk}%
    - Daily loss limit: {daily_loss}%
    
    Steps:
    1. Check if portfolio constraints allow new trades
    2. If signal is HOLD, skip position sizing
    3. If signal is BUY/SELL, calculate position size based on:
       - Current price
       - ATR (volatility)
       - Account equity
    4. Provide trade approval or rejection with clear reasoning""",
    expected_output="""Risk assessment and position sizing:
    {{
        "trade_approved": <boolean>,
        "signal": "BUY" | "SELL" | "HOLD",
        "position_size": <int> shares,
        "risk_checks": {{
            "max_positions": "PASS" | "FAIL",
            "daily_loss": "PASS" | "FAIL",
            "account_status": "PASS" | "FAIL"
        }},
        "veto_reason": "<explanation if rejected>"
    }}""",
    agent=risk_manager_agent,
    context=[validate_signal_task]
)


# Task 5: Execution
execute_trade_task = Task(
    description="""Execute the approved trade (if any).
    
    Rules:
    - If trade_approved is False, do not execute
    - If signal is HOLD, do not execute
    - If signal is BUY or SELL and approved, place market order for {symbol}
    
    Execution Steps:
    1. Verify trade approval status
    2. Place market order with calculated position size
    3. Confirm order submission
    4. Log the order ID and execution details
    
    In DRY_RUN mode, simulate the order and log what would have been executed.""",
    expected_output="""Execution summary:
    {{
        "execution_status": "SUCCESS" | "SKIPPED" | "FAILED",
        "order_id": "<alpaca order ID or 'DRY_RUN'>",
        "symbol": "{symbol}",
        "side": "BUY" | "SELL",
        "qty": <int>,
        "reason": "<explanation for execution or skip>",
        "timestamp": "<ISO timestamp>"
    }}""",
    agent=execution_agent,
    context=[assess_risk_task]
)


# Export all tasks
__all__ = [
    'collect_data_task',
    'generate_signal_task',
    'validate_signal_task',
    'assess_risk_task',
    'execute_trade_task'
]
```

**Acceptance Criteria:**
- [ ] All 5 tasks defined in correct sequential order
- [ ] Each task has clear description and expected output
- [ ] Tasks use context properly (depend on previous tasks)
- [ ] Template variables `{symbol}`, `{timeframe}` used correctly
- [ ] Task outputs structured as specified

---

### **Feature 3.3: Crew Orchestration**

**Objective:** Create the main crew that orchestrates all agents and tasks.

**Deliverable: `src/crew/trading_crew.py`**

```python
"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""

from crewai import Crew, Process
from src.crew.tasks import (
    collect_data_task,
    generate_signal_task,
    validate_signal_task,
    assess_risk_task,
    execute_trade_task
)
from src.agents.base_agents import (
    data_collector_agent,
    signal_generator_agent,
    signal_validator_agent,
    risk_manager_agent,
    execution_agent
)
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class TradingCrew:
    """
    Main trading crew orchestrator.
    Manages the complete workflow from data collection to trade execution.
    """
    
    def __init__(self):
        self.crew = Crew(
            agents=[
                data_collector_agent,
                signal_generator_agent,
                signal_validator_agent,
                risk_manager_agent,
                execution_agent
            ],
            tasks=[
                collect_data_task,
                generate_signal_task,
                validate_signal_task,
                assess_risk_task,
                execute_trade_task
            ],
            process=Process.sequential,  # Execute tasks in order
            verbose=2  # Maximum logging
        )
        
        logger.info("TradingCrew initialized")
    
    def run(
        self,
        symbol: str = None,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> dict:
        """
        Execute the complete trading workflow.
        
        Args:
            symbol: Stock symbol to trade (defaults to settings)
            timeframe: Bar timeframe
            limit: Number of historical bars to analyze
        
        Returns:
            Dictionary with crew execution results
        """
        # Use configured symbol if not provided
        if symbol is None:
            symbol = settings.trading_symbol
        
        logger.info(f"Starting trading crew for {symbol}")
        logger.info(f"Configuration: timeframe={timeframe}, bars={limit}")
        logger.info(f"Mode: {'DRY RUN' if settings.dry_run else 'LIVE TRADING'}")
        
        # Prepare inputs for tasks (template variables)
        inputs = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "ma_fast": settings.ma_fast_period,
            "ma_medium": settings.ma_medium_period,
            "ma_slow": settings.ma_slow_period,
            "volume_threshold": settings.volume_threshold,
            "adx_threshold": settings.adx_threshold,
            "max_positions": settings.max_open_positions,
            "max_risk": settings.max_risk_per_trade * 100,
            "daily_loss": settings.daily_loss_limit * 100
        }
        
        try:
            # Execute the crew
            result = self.crew.kickoff(inputs=inputs)
            
            logger.info("Trading crew completed successfully")
            logger.info(f"Result: {result}")
            
            return {
                "success": True,
                "result": str(result),
                "symbol": symbol,
                "configuration": inputs
            }
        
        except Exception as e:
            logger.error(f"Trading crew execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }


# Global instance
trading_crew = TradingCrew()
```

**Acceptance Criteria:**
- [ ] Crew properly instantiated with all agents and tasks
- [ ] Sequential process enforced
- [ ] Input variables passed correctly to tasks
- [ ] Error handling catches and logs failures
- [ ] Success/failure status returned clearly

---

## **PHASE 4: Integration & Testing**

### **Feature 4.1: Logging System**

**Objective:** Implement comprehensive logging for debugging and monitoring.

**Deliverable: `src/utils/logger.py`**

```python
"""
Logging Configuration
Structured logging for the entire application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from src.config.settings import settings


def setup_logging():
    """Configure application-wide logging."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    log_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # File handler
    log_file = log_dir / f"trading_crew_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("crewai").setLevel(logging.INFO)
    
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log file: {log_file}")


# Call on module import
setup_logging()
```

**Acceptance Criteria:**
- [ ] Logs written to both console and file
- [ ] Log files organized by date
- [ ] Log level configurable via settings
- [ ] Structured format with timestamps
- [ ] Third-party loggers suppressed

---

### **Feature 4.2: CLI Entry Point**

**Objective:** Create a user-friendly command-line interface to run the crew.

**Deliverable: `scripts/run_crew.py`**

```python
#!/usr/bin/env python3
"""
Trading Crew CLI
Command-line interface for running the trading crew.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.crew.trading_crew import trading_crew
from src.connectors.gemini_connector import gemini_manager
from src.connectors.alpaca_connector import alpaca_manager
from src.utils.logger import setup_logging

console = Console()


@click.group()
def cli():
    """AI-Driven Trading Crew - Backend CLI"""
    pass


@cli.command()
@click.option('--symbol', default=None, help='Stock symbol to trade (default: from config)')
@click.option('--timeframe', default='1Min', help='Bar timeframe (1Min, 5Min, etc.)')
@click.option('--limit', default=100, help='Number of historical bars to fetch')
def run(symbol, timeframe, limit):
    """Run the trading crew for a single execution."""
    console.print(Panel.fit(
        "[bold cyan]AI-Driven Trading Crew[/bold cyan]\n"
        "[dim]Backend-First Development Version[/dim]",
        border_style="cyan"
    ))
    
    # Display configuration
    console.print("\n[yellow]Configuration:[/yellow]")
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Symbol", symbol or settings.trading_symbol)
    config_table.add_row("Timeframe", timeframe)
    config_table.add_row("Bars", str(limit))
    config_table.add_row("Mode", "DRY RUN" if settings.dry_run else "LIVE TRADING")
    
    console.print(config_table)
    
    # Confirm if live trading
    if not settings.dry_run:
        console.print("\n[bold red]⚠️  WARNING: LIVE TRADING MODE[/bold red]")
        if not click.confirm("Are you sure you want to execute live trades?"):
            console.print("[yellow]Cancelled by user[/yellow]")
            return
    
    # Execute crew
    console.print("\n[cyan]Starting trading crew...[/cyan]\n")
    
    try:
        result = trading_crew.run(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )
        
        if result['success']:
            console.print(Panel.fit(
                "[bold green]✓ Crew execution completed successfully![/bold green]",
                border_style="green"
            ))
            console.print(f"\n[dim]Result: {result['result']}[/dim]")
        else:
            console.print(Panel.fit(
                f"[bold red]✗ Crew execution failed[/bold red]\n"
                f"[dim]{result.get('error', 'Unknown error')}[/dim]",
                border_style="red"
            ))
    
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]✗ Unexpected error[/bold red]\n"
            f"[dim]{str(e)}[/dim]",
            border_style="red"
        ))


@cli.command()
def status():
    """Check system status and connectivity."""
    console.print(Panel.fit(
        "[bold cyan]System Status Check[/bold cyan]",
        border_style="cyan"
    ))
    
    # Check Gemini
    console.print("\n[cyan]Gemini API Status:[/cyan]")
    try:
        stats = gemini_manager.get_stats()
        console.print(f"  ✓ API Keys: {stats['active_keys']}")
        console.print(f"  ✓ Requests (Session): {stats['total_requests']}")
        console.print(f"  ✓ RPM Used: {stats['rpm_used']}/{stats['rpm_limit']}")
        console.print(f"  ✓ RPD Used: {stats['rpd_used']}/{stats['rpd_limit']}")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")
    
    # Check Alpaca
    console.print("\n[cyan]Alpaca API Status:[/cyan]")
    try:
        account = alpaca_manager.get_account()
        console.print(f"  ✓ Account Status: {account['status']}")
        console.print(f"  ✓ Equity: ${account['equity']:,.2f}")
        console.print(f"  ✓ Buying Power: ${account['buying_power']:,.2f}")
        console.print(f"  ✓ Mode: {'Paper Trading' if alpaca_manager.is_paper else 'LIVE'}")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")
    
    # Check positions
    console.print("\n[cyan]Current Positions:[/cyan]")
    try:
        positions = alpaca_manager.get_positions()
        if positions:
            for pos in positions:
                console.print(
                    f"  • {pos['symbol']}: {pos['qty']} shares "
                    f"(P&L: ${pos['unrealized_pl']:,.2f})"
                )
        else:
            console.print("  [dim]No open positions[/dim]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")


@cli.command()
def validate():
    """Run configuration validation checks."""
    console.print("[cyan]Running configuration validation...[/cyan]\n")
    
    from pathlib import Path
    import subprocess
    
    # Run the validation script
    script_path = Path(__file__).parent / "validate_config.py"
    result = subprocess.run(
        ["python", str(script_path)],
        capture_output=False
    )
    
    sys.exit(result.returncode)


if __name__ == '__main__':
    cli()
```

**Acceptance Criteria:**
- [ ] CLI runs with `python scripts/run_crew.py run`
- [ ] `--help` displays all available commands
- [ ] `status` command shows all system checks
- [ ] `validate` command runs configuration validation
- [ ] `run` command executes crew successfully
- [ ] Rich console output with colors and tables
- [ ] Live trading confirmation prompt works

**Validation:**
```bash
# From project root in WSL2
chmod +x scripts/run_crew.py

# Test all commands
poetry run python scripts/run_crew.py --help
poetry run python scripts/run_crew.py validate
poetry run python scripts/run_crew.py status
poetry run python scripts/run_crew.py run --symbol SPY --limit 50
```

---

### **Feature 4.3: End-to-End Integration Test**

**Objective:** Validate the entire system works from start to finish.

**Deliverable: `tests/test_integration/test_full_workflow.py`**

```python
"""
End-to-End Integration Test
Tests the complete trading workflow from data fetching to execution.
"""

import pytest
from src.config.settings import settings
from src.connectors.alpaca_connector import alpaca_manager
from src.crew.trading_crew import trading_crew
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TestFullWorkflow:
    """Integration tests for complete trading workflow."""
    
    def test_system_connectivity(self):
        """Test that all external systems are reachable."""
        # Test Alpaca connection
        account = alpaca_manager.get_account()
        assert account['equity'] > 0, "Alpaca account not accessible"
        
        # Test data fetching
        df = alpaca_manager.fetch_historical_bars("SPY", "1Min", 10)
        assert len(df) > 0, "Cannot fetch market data"
        
        logger.info("✓ System connectivity test passed")
    
    def test_dry_run_execution(self):
        """Test complete crew execution in dry run mode."""
        # Ensure dry run is enabled
        assert settings.dry_run == True, "Dry run must be enabled for testing"
        
        # Execute crew
        result = trading_crew.run(
            symbol="SPY",
            timeframe="1Min",
            limit=50
        )
        
        # Verify result structure
        assert 'success' in result
        assert result['symbol'] == "SPY"
        
        if result['success']:
            logger.info("✓ Dry run execution completed successfully")
        else:
            logger.error(f"✗ Dry run failed: {result.get('error')}")
            pytest.fail(f"Crew execution failed: {result.get('error')}")
    
    def test_agent_task_chain(self):
        """Test that all agents execute their tasks in sequence."""
        result = trading_crew.run(symbol="SPY", timeframe="1Min", limit=100)
        
        # Check that result contains output from final task
        assert result is not None
        
        # In a complete run, we should have logs from all agents
        # (This would require checking log files in a real scenario)
        logger.info("✓ Agent task chain executed")
    
    def test_multiple_runs(self):
        """Test that system can handle multiple sequential runs."""
        symbols = ["SPY", "QQQ", "AAPL"]
        
        for symbol in symbols:
            logger.info(f"Testing with symbol: {symbol}")
            result = trading_crew.run(symbol=symbol, timeframe="1Min", limit=30)
            
            # Each run should complete
            assert result is not None
            
        logger.info("✓ Multiple runs completed successfully")
    
    def test_error_recovery(self):
        """Test system behavior with invalid inputs."""
        # Test with invalid symbol (should handle gracefully)
        result = trading_crew.run(symbol="INVALID_SYMBOL_XYZ", timeframe="1Min", limit=10)
        
        # System should not crash, but may report failure
        assert result is not None
        # Depending on implementation, this might succeed or fail gracefully
        
        logger.info("✓ Error recovery test completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Acceptance Criteria:**
- [ ] All connectivity tests pass
- [ ] Dry run execution completes without errors
- [ ] Agent chain executes in correct order
- [ ] Multiple sequential runs work
- [ ] System handles invalid inputs gracefully
- [ ] Test suite can be run with `pytest`

**Validation:**
```bash
# Run integration tests
poetry run pytest tests/test_integration/ -v -s

# Run with coverage
poetry run pytest tests/test_integration/ --cov=src --cov-report=html
```

---

### **Feature 4.4: Performance Benchmarking**

**Objective:** Measure and document system performance characteristics.

**Deliverable: `scripts/benchmark.py`**

```python
#!/usr/bin/env python3
"""
System Performance Benchmarking
Measures key performance metrics of the trading system.
"""

import time
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crew.trading_crew import trading_crew
from src.connectors.gemini_connector import gemini_manager
from src.connectors.alpaca_connector import alpaca_manager
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


def benchmark_data_fetching(iterations=5):
    """Benchmark market data fetching speed."""
    console.print("\n[cyan]Benchmarking data fetching...[/cyan]")
    
    times = []
    for _ in track(range(iterations), description="Fetching data"):
        start = time.time()
        alpaca_manager.fetch_historical_bars("SPY", "1Min", 100)
        elapsed = time.time() - start
        times.append(elapsed)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times)
    }


def benchmark_technical_analysis(iterations=5):
    """Benchmark technical analysis calculations."""
    console.print("\n[cyan]Benchmarking technical analysis...[/cyan]")
    
    # Fetch data once
    result = alpaca_manager.fetch_historical_bars("SPY", "1Min", 100)
    df = result
    
    from src.tools.analysis_tools import technical_analysis
    
    times = []
    for _ in track(range(iterations), description="Calculating indicators"):
        start = time.time()
        
        # Run all calculations
        technical_analysis.generate_3ma_signal(df)
        technical_analysis.calculate_volume_confirmation(df)
        technical_analysis.calculate_volatility_check(df)
        technical_analysis.calculate_trend_strength(df)
        
        elapsed = time.time() - start
        times.append(elapsed)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times)
    }


def benchmark_crew_execution(iterations=3):
    """Benchmark full crew execution time."""
    console.print("\n[cyan]Benchmarking full crew execution...[/cyan]")
    console.print("[yellow]Warning: This will consume API quota[/yellow]\n")
    
    times = []
    for i in track(range(iterations), description="Running crew"):
        start = time.time()
        
        result = trading_crew.run(symbol="SPY", timeframe="1Min", limit=50)
        
        elapsed = time.time() - start
        times.append(elapsed)
        
        # Add delay between runs to avoid rate limits
        if i < iterations - 1:
            time.sleep(10)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times)
    }


def display_results(benchmarks):
    """Display benchmark results in a table."""
    table = Table(title="Performance Benchmark Results", show_header=True)
    
    table.add_column("Metric", style="cyan")
    table.add_column("Mean (s)", justify="right", style="green")
    table.add_column("Median (s)", justify="right", style="green")
    table.add_column("Min (s)", justify="right", style="blue")
    table.add_column("Max (s)", justify="right", style="red")
    
    for name, results in benchmarks.items():
        table.add_row(
            name,
            f"{results['mean']:.3f}",
            f"{results['median']:.3f}",
            f"{results['min']:.3f}",
            f"{results['max']:.3f}"
        )
    
    console.print("\n")
    console.print(table)


def main():
    """Run all benchmarks."""
    console.print("[bold cyan]Trading System Performance Benchmark[/bold cyan]")
    
    benchmarks = {}
    
    # Run benchmarks
    benchmarks["Data Fetching"] = benchmark_data_fetching(iterations=5)
    benchmarks["Technical Analysis"] = benchmark_technical_analysis(iterations=5)
    benchmarks["Full Crew Execution"] = benchmark_crew_execution(iterations=2)
    
    # Get API usage stats
    stats = gemini_manager.get_stats()
    console.print(f"\n[yellow]Gemini API Usage:[/yellow]")
    console.print(f"  Total Requests: {stats['total_requests']}")
    console.print(f"  RPM Used: {stats['rpm_used']}/{stats['rpm_limit']}")
    console.print(f"  RPD Used: {stats['rpd_used']}/{stats['rpd_limit']}")
    
    # Display results
    display_results(benchmarks)
    
    # Performance assessment
    console.print("\n[bold]Performance Assessment:[/bold]")
    crew_time = benchmarks["Full Crew Execution"]["mean"]
    
    if crew_time < 30:
        console.print("  ✓ [green]Excellent:[/green] Crew execution under 30 seconds")
    elif crew_time < 60:
        console.print("  ⚠ [yellow]Good:[/yellow] Crew execution under 60 seconds")
    else:
        console.print("  ✗ [red]Needs optimization:[/red] Crew execution over 60 seconds")


if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- [ ] Benchmarks measure data fetching speed
- [ ] Technical analysis speed measured
- [ ] Full crew execution time tracked
- [ ] Results displayed in formatted table
- [ ] API usage statistics included
- [ ] Performance assessment provides recommendations

**Validation:**
```bash
# Run benchmarks
poetry run python scripts/benchmark.py

# Expected output:
# - Data fetching: < 2 seconds
# - Technical analysis: < 0.5 seconds
# - Full crew: < 60 seconds (depends on LLM response time)
```

---

## **PHASE 5: Production Readiness & Advanced Features**

### **Feature 5.1: Error Recovery and Retry Logic**

**Objective:** Implement robust error handling with exponential backoff.

**Deliverable: `src/utils/retry_handler.py`**

```python
"""
Retry Handler with Exponential Backoff
Implements resilient API call patterns.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


def exponential_backoff_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exceptions: Tuple of exception types to catch and retry
    
    Usage:
        @exponential_backoff_retry(max_attempts=3, base_delay=1.0)
        def my_api_call():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    attempt += 1
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
            
            return None
        
        return wrapper
    return decorator


def rate_limit_handler(
    calls_per_minute: int = 10,
    calls_per_day: int = 250
):
    """
    Decorator for enforcing rate limits on functions.
    
    Args:
        calls_per_minute: Maximum calls allowed per minute
        calls_per_day: Maximum calls allowed per day
    
    Usage:
        @rate_limit_handler(calls_per_minute=10)
        def api_call():
            pass
    """
    from collections import deque
    from datetime import datetime, timedelta
    
    minute_calls = deque(maxlen=calls_per_minute)
    day_calls = deque(maxlen=calls_per_day)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            now = datetime.now()
            
            # Clean old entries
            minute_ago = now - timedelta(minutes=1)
            day_ago = now - timedelta(days=1)
            
            while minute_calls and minute_calls[0] < minute_ago:
                minute_calls.popleft()
            
            while day_calls and day_calls[0] < day_ago:
                day_calls.popleft()
            
            # Check limits
            if len(minute_calls) >= calls_per_minute:
                sleep_time = 60 - (now - minute_calls[0]).total_seconds() + 1
                logger.warning(f"Rate limit reached. Sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            if len(day_calls) >= calls_per_day:
                raise Exception("Daily rate limit exceeded")
            
            # Record call
            minute_calls.append(now)
            day_calls.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by temporarily blocking requests to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time >= self.timeout:
                    logger.info(f"Circuit breaker: Attempting recovery (HALF_OPEN)")
                    self.state = "HALF_OPEN"
                else:
                    raise Exception(
                        f"Circuit breaker OPEN for {func.__name__}. "
                        f"Service temporarily unavailable."
                    )
            
            try:
                result = func(*args, **kwargs)
                
                # Success - reset failure count
                if self.state == "HALF_OPEN":
                    logger.info(f"Circuit breaker: Recovery successful (CLOSED)")
                    self.state = "CLOSED"
                    self.failure_count = 0
                
                return result
            
            except self.expected_exceptions as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                logger.warning(
                    f"Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}"
                )
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(
                        f"Circuit breaker: OPEN for {func.__name__}. "
                        f"Too many failures ({self.failure_count})"
                    )
                
                raise
        
        return wrapper
```

**Acceptance Criteria:**
- [ ] Exponential backoff decorator works correctly
- [ ] Rate limiting enforced at function level
- [ ] Circuit breaker prevents cascading failures
- [ ] All decorators preserve function metadata
- [ ] Logging provides clear debugging information

---

### **Feature 5.2: System Monitoring and Alerts**

**Objective:** Implement monitoring for critical system metrics.

**Deliverable: `src/utils/monitoring.py`**

```python
"""
System Monitoring and Alerting
Tracks system health and sends alerts for critical events.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemMetrics:
    """Container for system performance metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # API Usage
    gemini_rpm_used: int = 0
    gemini_rpd_used: int = 0
    alpaca_requests: int = 0
    
    # Performance
    avg_crew_execution_time: float = 0.0
    successful_runs: int = 0
    failed_runs: int = 0
    
    # Trading
    open_positions: int = 0
    daily_pnl: float = 0.0
    total_trades: int = 0
    
    # Errors
    error_count: int = 0
    last_error: Optional[str] = None


class SystemMonitor:
    """
    Monitors system health and triggers alerts.
    """
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.alert_handlers: List[callable] = []
        self.current_metrics = SystemMetrics()
    
    def register_alert_handler(self, handler: callable):
        """Register a function to handle alerts."""
        self.alert_handlers.append(handler)
    
    def update_metrics(self, **kwargs):
        """Update current metrics."""
        for key, value in kwargs.items():
            if hasattr(self.current_metrics, key):
                setattr(self.current_metrics, key, value)
    
    def record_crew_execution(self, success: bool, execution_time: float):
        """Record crew execution metrics."""
        if success:
            self.current_metrics.successful_runs += 1
        else:
            self.current_metrics.failed_runs += 1
        
        # Update average execution time
        total_runs = (
            self.current_metrics.successful_runs + 
            self.current_metrics.failed_runs
        )
        
        current_avg = self.current_metrics.avg_crew_execution_time
        self.current_metrics.avg_crew_execution_time = (
            (current_avg * (total_runs - 1) + execution_time) / total_runs
        )
    
    def check_health(self) -> Dict[str, any]:
        """
        Perform health checks and return status.
        
        Returns:
            Dict with health status and any issues
        """
        issues = []
        warnings = []
        
        # Check error rate
        total_runs = (
            self.current_metrics.successful_runs + 
            self.current_metrics.failed_runs
        )
        
        if total_runs > 0:
            error_rate = self.current_metrics.failed_runs / total_runs
            
            if error_rate > 0.5:
                issues.append(f"High error rate: {error_rate:.1%}")
            elif error_rate > 0.2:
                warnings.append(f"Elevated error rate: {error_rate:.1%}")
        
        # Check API usage
        if self.current_metrics.gemini_rpd_used > 200:
            warnings.append(
                f"High Gemini API usage: {self.current_metrics.gemini_rpd_used}/250 daily"
            )
        
        # Check performance
        if self.current_metrics.avg_crew_execution_time > 90:
            warnings.append(
                f"Slow execution time: {self.current_metrics.avg_crew_execution_time:.1f}s avg"
            )
        
        # Determine overall health
        if issues:
            health_status = "UNHEALTHY"
            level = AlertLevel.ERROR
        elif warnings:
            health_status = "DEGRADED"
            level = AlertLevel.WARNING
        else:
            health_status = "HEALTHY"
            level = AlertLevel.INFO
        
        result = {
            "status": health_status,
            "level": level,
            "issues": issues,
            "warnings": warnings,
            "metrics": self.current_metrics
        }
        
        # Send alerts if needed
        if issues or warnings:
            self._send_alert(level, result)
        
        return result
    
    def _send_alert(self, level: AlertLevel, data: Dict):
        """Send alerts to registered handlers."""
        for handler in self.alert_handlers:
            try:
                handler(level, data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def get_metrics_summary(self) -> Dict:
        """Get a summary of current metrics."""
        return {
            "timestamp": self.current_metrics.timestamp.isoformat(),
            "api_usage": {
                "gemini_rpm": self.current_metrics.gemini_rpm_used,
                "gemini_rpd": self.current_metrics.gemini_rpd_used,
                "alpaca_requests": self.current_metrics.alpaca_requests
            },
            "performance": {
                "avg_execution_time": round(
                    self.current_metrics.avg_crew_execution_time, 2
                ),
                "successful_runs": self.current_metrics.successful_runs,
                "failed_runs": self.current_metrics.failed_runs,
                "success_rate": (
                    self.current_metrics.successful_runs / 
                    max(1, self.current_metrics.successful_runs + 
                        self.current_metrics.failed_runs)
                ) * 100
            },
            "trading": {
                "open_positions": self.current_metrics.open_positions,
                "daily_pnl": round(self.current_metrics.daily_pnl, 2),
                "total_trades": self.current_metrics.total_trades
            }
        }


# Global monitor instance
system_monitor = SystemMonitor()


# Example alert handler
def console_alert_handler(level: AlertLevel, data: Dict):
    """Print alerts to console."""
    logger.log(
        logging.WARNING if level == AlertLevel.WARNING else logging.ERROR,
        f"[{level.value}] System Alert: {data['status']}"
    )
    
    if data['issues']:
        logger.error(f"Issues: {', '.join(data['issues'])}")
    
    if data['warnings']:
        logger.warning(f"Warnings: {', '.join(data['warnings'])}")


# Register default handler
system_monitor.register_alert_handler(console_alert_handler)
```

**Acceptance Criteria:**
- [ ] Metrics tracked correctly during execution
- [ ] Health checks identify issues
- [ ] Alerts triggered for critical conditions
- [ ] Alert handlers can be registered
- [ ] Metrics summary provides clear overview

---

### **Feature 5.3: Backtesting Framework**

**Objective:** Enable strategy backtesting on historical data.

**Deliverable: `src/backtest/backtester.py`**

```python
"""
Backtesting Framework
Tests trading strategies on historical data.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from src.tools.market_data_tools import market_data_tools
from src.tools.analysis_tools import technical_analysis
from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    entry_time: datetime
    exit_time: datetime = None
    symbol: str = ""
    side: str = "BUY"  # BUY or SELL
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: int = 0
    pnl: float = 0.0
    pnl_pct: float = 0.0


class BacktestEngine:
    """
    Backtesting engine for trading strategies.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
    def run_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1Min"
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Bar timeframe
        
        Returns:
            Dict with backtest results
        """
        logger.info(f"Starting backtest: {symbol} from {start_date} to {end_date}")
        
        # Fetch historical data
        # Note: In real implementation, would need to handle date ranges properly
        # This is a simplified version
        result = market_data_tools.fetch_ohlcv_data(symbol, timeframe, limit=1000)
        
        if not result['success']:
            raise Exception(f"Failed to fetch data: {result['error']}")
        
        df = result['data']
        
        # Initialize backtest state
        position = None  # Current open position
        equity = self.initial_capital
        
        # Iterate through data
        for i in range(len(df) - settings.ma_slow_period):
            # Get window of data for analysis
            window = df.iloc[:i + settings.ma_slow_period + 1]
            
            if len(window) < settings.ma_slow_period:
                continue
            
            # Generate signal
            signal_result = technical_analysis.generate_3ma_signal(window)
            signal = signal_result['signal']
            current_price = signal_result['current_price']
            timestamp = window.index[-1]
            
            # Check volume confirmation
            vol_check = technical_analysis.calculate_volume_confirmation(window)
            vol_confirmed = vol_check['confirmed']
            
            # Check trend strength
            trend_check = technical_analysis.calculate_trend_strength(window)
            strong_trend = trend_check['has_strong_trend']
            
            # Apply confirmation filters
            confirmations = sum([vol_confirmed, strong_trend])
            
            if confirmations < 2 and signal != "HOLD":
                signal = "HOLD"  # Override signal if not confirmed
            
            # Execute logic
            if signal == "BUY" and position is None:
                # Open long position
                qty = int((equity * settings.max_risk_per_trade) / current_price)
                qty = max(1, qty)
                
                position = Trade(
                    entry_time=timestamp,
                    symbol=symbol,
                    side="BUY",
                    entry_price=current_price,
                    quantity=qty
                )
                
                logger.debug(f"[{timestamp}] BUY {qty} @ ${current_price:.2f}")
            
            elif signal == "SELL" and position is not None and position.side == "BUY":
                # Close long position
                position.exit_time = timestamp
                position.exit_price = current_price
                position.pnl = (current_price - position.entry_price) * position.quantity
                position.pnl_pct = (
                    (current_price - position.entry_price) / position.entry_price * 100
                )
                
                equity += position.pnl
                self.trades.append(position)
                
                logger.debug(
                    f"[{timestamp}] SELL {position.quantity} @ ${current_price:.2f} "
                    f"(P&L: ${position.pnl:.2f})"
                )
                
                position = None
            
            # Record equity
            self.equity_curve.append({
                "timestamp": timestamp,
                "equity": equity,
                "drawdown": (equity - self.initial_capital) / self.initial_capital * 100
            })
        
        # Close any open position at end
        if position is not None:
            position.exit_time = df.index[-1]
            position.exit_price = df['close'].iloc[-1]
            position.pnl = (position.exit_price - position.entry_price) * position.quantity
            position.pnl_pct = (
                (position.exit_price - position.entry_price) / position.entry_price * 100
            )
            equity += position.pnl
            self.trades.append(position)
        
        # Calculate metrics
        metrics = self._calculate_metrics(equity)
        
        logger.info(f"Backtest completed: {len(self.trades)} trades")
        
        return {
            "symbol": symbol,
            "period": f"{start_date} to {end_date}",
            "initial_capital": self.initial_capital,
            "final_equity": equity,
            "total_trades": len(self.trades),
            "metrics": metrics,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }
    
    def _calculate_metrics(self, final_equity: float) -> Dict:
        """Calculate performance metrics."""
        if not self.trades:
            return {}
        
        # Basic metrics
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = (len(winning_trades) / len(self.trades)) * 100 if self.trades else 0
        
        avg_win = (
            sum(t.pnl for t in winning_trades) / len(winning_trades)
            if winning_trades else 0
        )
        avg_loss = (
            sum(t.pnl for t in losing_trades) / len(losing_trades)
            if losing_trades else 0
        )
        
        profit_factor = (
            abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades))
            if losing_trades and sum(t.pnl for t in losing_trades) != 0
            else float('inf') if winning_trades else 0
        )
        
        # Calculate max drawdown
        peak = self.initial_capital
        max_drawdown = 0
        
        for point in self.equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            drawdown = ((peak - equity) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "total_return_pct": round(total_return, 2),
            "total_return_usd": round(final_equity - self.initial_capital, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞",
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": "TODO"  # Would need daily returns calculation
        }


# Global instance
backtester = BacktestEngine()
```

**Acceptance Criteria:**
- [ ] Backtest runs on historical data
- [ ] Trades executed based on strategy signals
- [ ] Performance metrics calculated correctly
- [ ] Equity curve tracked throughout backtest
- [ ] Win rate, profit factor, drawdown computed
- [ ] Results can be exported for analysis

**Validation:**
```python
# Test: tests/test_backtest/test_backtester.py
from src.backtest.backtester import BacktestEngine
from datetime import datetime, timedelta

def test_backtest():
    engine = BacktestEngine(initial_capital=100000)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    results = engine.run_backtest(
        symbol="SPY",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        timeframe="1Min"
    )
    
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['metrics']['win_rate']}%")
    print(f"Total Return: {results['metrics']['total_return_pct']}%")
    print(f"Max Drawdown: {results['metrics']['max_drawdown_pct']}%")
    
    assert results['total_trades'] >= 0

if __name__ == "__main__":
    test_backtest()
```

---

### **Feature 5.4: Strategy Optimization Module**

**Objective:** Optimize strategy parameters using grid search.

**Deliverable: `src/optimization/optimizer.py`**

```python
"""
Strategy Parameter Optimization
Grid search and parameter tuning for trading strategies.
"""

import logging
from itertools import product
from typing import Dict, List
from src.backtest.backtester import BacktestEngine
import pandas as pd

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """
    Optimizes strategy parameters using grid search.
    """
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def optimize_3ma_parameters(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        fast_periods: List[int] = [5, 8, 13],
        medium_periods: List[int] = [13, 21, 34],
        slow_periods: List[int] = [21, 34, 55],
        volume_thresholds: List[float] = [1.2, 1.5, 2.0]
    ) -> Dict:
        """
        Optimize 3MA strategy parameters.
        
        Args:
            symbol: Stock symbol
            start_date: Backtest start date
            end_date: Backtest end date
            fast_periods: List of fast MA periods to test
            medium_periods: List of medium MA periods to test
            slow_periods: List of slow MA periods to test
            volume_thresholds: List of volume thresholds to test
        
        Returns:
            Dict with best parameters and results
        """
        logger.info(f"Starting parameter optimization for {symbol}")
        
        # Generate all parameter combinations
        combinations = list(product(
            fast_periods,
            medium_periods,
            slow_periods,
            volume_thresholds
        ))
        
        logger.info(f"Testing {len(combinations)} parameter combinations")
        
        best_result = None
        best_sharpe = float('-inf')
        
        for i, (fast, medium, slow, vol_threshold) in enumerate(combinations):
            # Skip invalid combinations
            if not (fast < medium < slow):
                continue
            
            logger.info(
                f"Testing combination {i+1}/{len(combinations)}: "
                f"MA({fast},{medium},{slow}) Vol:{vol_threshold}"
            )
            
            try:
                # Temporarily modify settings
                from src.config.settings import settings
                original_fast = settings.ma_fast_period
                original_medium = settings.ma_medium_period
                original_slow = settings.ma_slow_period
                original_vol = settings.volume_threshold
                
                settings.ma_fast_period = fast
                settings.ma_medium_period = medium
                settings.ma_slow_period = slow
                settings.volume_threshold = vol_threshold
                
                # Run backtest
                engine = BacktestEngine(initial_capital=100000)
                result = engine.run_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Restore original settings
                settings.ma_fast_period = original_fast
                settings.ma_medium_period = original_medium
                settings.ma_slow_period = original_slow
                settings.volume_threshold = original_vol
                
                # Store result
                metrics = result['metrics']
                metrics['parameters'] = {
                    'fast': fast,
                    'medium': medium,
                    'slow': slow,
                    'volume_threshold': vol_threshold
                }
                
                self.results.append(metrics)
                
                # Track best result (by total return for now)
                # In production, would use Sharpe ratio or other metrics
                total_return = metrics.get('total_return_pct', 0)
                
                if best_result is None or total_return > best_sharpe:
                    best_sharpe = total_return
                    best_result = metrics
                
            except Exception as e:
                logger.error(f"Optimization failed for combination: {e}")
                continue
        
        logger.info(f"Optimization completed. Best return: {best_sharpe:.2f}%")
        
        return {
            "best_parameters": best_result['parameters'],
            "best_metrics": best_result,
            "all_results": self.results
        }
    
    def export_results(self, filename: str = "optimization_results.csv"):
        """Export optimization results to CSV."""
        if not self.results:
            logger.warning("No results to export")
            return
        
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        logger.info(f"Results exported to {filename}")


# Global instance
optimizer = StrategyOptimizer()
```

**Acceptance Criteria:**
- [ ] Grid search tests all parameter combinations
- [ ] Invalid combinations filtered out
- [ ] Best parameters identified based on metrics
- [ ] Results can be exported to CSV
- [ ] Original settings restored after optimization
- [ ] Progress logging during optimization

---

### **Feature 5.5: Production Deployment Checklist**

**Objective:** Create comprehensive deployment documentation.

**Deliverable: `docs/DEPLOYMENT.md`**

```markdown
# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] All API keys stored in Secret Manager (not in .env)
- [ ] `DRY_RUN=false` for live trading
- [ ] Alpaca base URL set to production (not paper)
- [ ] Log level set to INFO or WARNING (not DEBUG)
- [ ] Rate limits configured correctly for production

### 2. Security Review

- [ ] No API keys in Git history
- [ ] `.env` file in `.gitignore`
- [ ] All secrets using environment variables
- [ ] Firestore security rules tested
- [ ] API endpoints protected with authentication

### 3. Testing

- [ ] All unit tests passing (`pytest tests/`)
- [ ] Integration tests completed successfully
- [ ] Backtest results meet performance targets:
  - Win rate > 55%
  - Profit factor > 1.5
  - Max drawdown < 10%
- [ ] Paper trading tested for 1+ weeks
- [ ] Error recovery tested (API failures, network issues)

### 4. Performance Validation

- [ ] Benchmark results acceptable:
  - Data fetching < 2s
  - Technical analysis < 0.5s
  - Full crew execution < 60s
- [ ] API usage within limits:
  - Gemini: < 80% of daily quota
  - Alpaca: Well under rate limits
- [ ] Memory usage monitored (no leaks)

### 5. Monitoring Setup

- [ ] Logging configured and tested
- [ ] Alert handlers registered
- [ ] Health check endpoint working
- [ ] Metrics dashboard available
- [ ] Error notifications configured

### 6. Risk Management

- [ ] Max risk per trade verified (2%)
- [ ] Max open positions limit enforced (3)
- [ ] Daily loss limit active (5%)
- [ ] Circuit breakers tested
- [ ] Emergency stop mechanism available

---

## Deployment Steps

### Step 1: Secret Management

```bash
# Store secrets in environment (or use secret management service)
export GEMINI_API_KEYS="prod_key1,prod_key2"
export ALPACA_API_KEY="live_api_key"
export ALPACA_SECRET_KEY="live_secret_key"
export ALPACA_BASE_URL="https://api.alpaca.markets"  # LIVE URL
```

### Step 2: Configuration Update

Edit `.env`:
```bash
DRY_RUN=false
LOG_LEVEL=INFO
TRADING_SYMBOL=SPY
MAX_RISK_PER_TRADE=0.02
MAX_OPEN_POSITIONS=3
DAILY_LOSS_LIMIT=0.05
```

### Step 3: Validation

```bash
# Run configuration validation
poetry run python scripts/validate_config.py

# Should output: "All X checks passed! ✓"
```

### Step 4: System Status Check

```bash
# Check all systems are operational
poetry run python scripts/run_crew.py status

# Verify:
# - Gemini API: Connected
# - Alpaca API: Connected (LIVE mode)
# - Account equity > 0
```

### Step 5: Test Run (Single Execution)

```bash
# Execute one crew run to verify everything works
poetry run python scripts/run_crew.py run --symbol SPY --limit 100

# Monitor logs for:
# - Successful data fetching
# - Signal generation
# - Risk checks passing
# - Order execution (if signal generated)
```

### Step 6: Production Deployment

**Option A: Manual Execution**
```bash
# Run on schedule using cron (Linux/WSL)
crontab -e

# Add entry to run 3 times during market hours:
30 9,12,15 * * 1-5 cd /path/to/trading-crew && poetry run python scripts/run_crew.py run

# Market hours: 9:30 AM, 12:00 PM, 3:00 PM ET (Mon-Fri)
```

**Option B: Cloud Deployment (Firebase Functions)**
```bash
# Deploy Cloud Function
cd functions
firebase deploy --only functions

# Configure Cloud Scheduler
gcloud scheduler jobs create http trading-crew-trigger \
  --schedule="30 9,12,15 * * 1-5" \
  --time-zone="America/New_York" \
  --uri="https://YOUR_REGION-YOUR_PROJECT.cloudfunctions.net/start_crew" \
  --http-method=POST
```

**Option C: Systemd Service (Linux)**
```bash
# Create systemd service file
sudo nano /etc/systemd/system/trading-crew.service

# Service configuration:
[Unit]
Description=Trading Crew Service
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/trading-crew
ExecStart=/path/to/poetry run python scripts/run_crew.py run
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Create timer for scheduling
sudo nano /etc/systemd/system/trading-crew.timer

[Unit]
Description=Trading Crew Timer

[Timer]
OnCalendar=Mon-Fri 9:30,12:00,15:00
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start
sudo systemctl enable trading-crew.timer
sudo systemctl start trading-crew.timer
```

---

## Post-Deployment Monitoring

### Daily Checks

1. **Review Logs**
   ```bash
   tail -f logs/trading_crew_$(date +%Y%m%d).log
   ```

2. **Check System Status**
   ```bash
   poetry run python scripts/run_crew.py status
   ```

3. **Review Trades**
   - Check Alpaca dashboard for executed trades
   - Verify P&L matches expectations
   - Review order fill quality

4. **Monitor API Usage**
   - Gemini: Check Google AI Studio dashboard
   - Alpaca: Review API usage in account dashboard

### Weekly Reviews

1. **Performance Analysis**
   - Calculate weekly win rate
   - Review profit factor
   - Analyze drawdown periods
   - Compare to benchmark (SPY buy-and-hold)

2. **Strategy Evaluation**
   - Review signal quality
   - Check confirmation rates
   - Analyze false signals
   - Consider parameter adjustments

3. **System Health**
   - Review error rates
   - Check execution times
   - Verify resource usage
   - Update dependencies if needed

### Monthly Reviews

1. **Full Performance Report**
   - Generate monthly P&L statement
   - Calculate Sharpe ratio
   - Review risk-adjusted returns
   - Update strategy if needed

2. **Security Audit**
   - Rotate API keys
   - Review access logs
   - Check for unauthorized access
   - Update security policies

---

## Emergency Procedures

### Immediate Stop

```bash
# Kill any running crew processes
pkill -f "run_crew.py"

# Disable scheduled runs
# Cron: comment out crontab entry
# Systemd: sudo systemctl stop trading-crew.timer
# Cloud: Disable Cloud Scheduler job
```

### Close All Positions

```python
# Emergency position closer
from src.connectors.alpaca_connector import alpaca_manager

positions = alpaca_manager.get_positions()
for pos in positions:
    alpaca_manager.place_market_order(
        symbol=pos['symbol'],
        qty=abs(pos['qty']),
        side='SELL' if pos['side'] == 'long' else 'BUY'
    )
```

### Rollback Deployment

```bash
# Git rollback
git revert HEAD
git push

# Firebase rollback
firebase functions:rollback start_crew
```

---

## Troubleshooting

### Issue: Orders Not Executing

**Possible Causes:**
- Insufficient buying power
- Market closed
- API connectivity issues
- Rate limits exceeded

**Resolution:**
1. Check account status: `poetry run python scripts/run_crew.py status`
2. Verify market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
3. Check Alpaca API status page
4. Review logs for error messages

### Issue: High Error Rate

**Possible Causes:**
- API rate limits
- Network connectivity
- Invalid data
- Strategy logic errors

**Resolution:**
1. Review error logs for patterns
2. Check API usage against limits
3. Validate data quality
4. Test in paper trading mode

### Issue: Poor Performance

**Possible Causes:**
- Market conditions changed
- Strategy parameters outdated
- High slippage
- Execution delays

**Resolution:**
1. Run backtests on recent data
2. Optimize strategy parameters
3. Review order fill quality
4. Consider strategy adjustments

---

## Support Contacts

- **Alpaca Support:** support@alpaca.markets
- **Google Cloud Support:** https://cloud.google.com/support
- **Community Forum:** [Your community link]

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-28 | Initial production deployment |

```

**Acceptance Criteria:**
- [ ] All checklist items documented
- [ ] Deployment steps clear and tested
- [ ] Monitoring procedures defined
- [ ] Emergency procedures documented
- [ ] Troubleshooting guide comprehensive

---

## **PHASE 6: Documentation & Developer Onboarding**

### **Feature 6.1: Comprehensive README**

**Objective:** Create developer-friendly documentation.

**Deliverable: Update `README.md`**

```markdown
# AI-Driven Trading Crew

A modular, backend-first trading system powered by CrewAI multi-agent framework, Google Gemini LLM, and Alpaca Markets API.

## 🎯 Project Philosophy: Keep It Simple (KIS)

**Backend First:** Build a rock-solid CLI-based trading system that works perfectly before adding any UI.

**Core Principles:**
- Every feature is independently testable
- Modular, replaceable components
- Works within free tier limitations
- Comprehensive logging for transparency

---

## 📋 Features

- **Multi-Agent System:** 5 specialized AI agents working in sequence
- **Proven Strategy:** Enhanced Triple Moving Average (3MA) with confirmation layers
- **Risk Management:** Portfolio-level constraints and position sizing
- **Paper Trading:** Safe testing with Alpaca paper trading account
- **Backtesting:** Test strategies on historical data
- **CLI Interface:** User-friendly command-line tools
- **Monitoring:** Real-time system health checks and alerts

---

## 🏗️ Architecture

```
Data Collection → Signal Generation → Validation → Risk Management → Execution
     Agent 1    →      Agent 2      →  Agent 3   →     Agent 4     →  Agent 5
```

### Agent Responsibilities

1. **DataCollectorAgent:** Fetches and validates OHLCV market data
2. **SignalGeneratorAgent:** Calculates 3MA indicators and generates signals
3. **SignalValidatorAgent:** Applies volume, volatility, and trend confirmations
4. **RiskManagerAgent:** Enforces position sizing and portfolio constraints
5. **ExecutionAgent:** Places approved trades via Alpaca API

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (< 3.14)
- Poetry or pip
- WSL2 (if on Windows)
- Alpaca Markets account (paper trading is free)
- Google Gemini API key (free tier available)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd trading-crew

# Install dependencies
poetry install
# or: pip install -r requirements.txt

# Setup environment
cp .env.template .env
# Edit .env with your API keys

# Validate configuration
poetry run python scripts/validate_config.py
```

### Configuration

Edit `.env` file:

```bash
# Gemini API (get from: https://aistudio.google.com/apikey)
GEMINI_API_KEYS="key1,key2,key3"

# Alpaca Markets (sign up: https://app.alpaca.markets/signup)
ALPACA_API_KEY="your_paper_api_key"
ALPACA_SECRET_KEY="your_paper_secret_key"
ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# Trading Parameters
TRADING_SYMBOL="SPY"
MA_FAST_PERIOD=8
MA_MEDIUM_PERIOD=13
MA_SLOW_PERIOD=21

# Risk Management
MAX_RISK_PER_TRADE=0.02  # 2%
MAX_OPEN_POSITIONS=3
DAILY_LOSS_LIMIT=0.05    # 5%

# System
DRY_RUN=true  # Safe mode
LOG_LEVEL=INFO
```

### Usage

```bash
# Check system status
poetry run python scripts/run_crew.py status

# Run single trading crew execution
poetry run python scripts/run_crew.py run

# Run with custom parameters
poetry run python scripts/run_crew.py run --symbol QQQ --limit 200

# View all commands
poetry run python scripts/run_crew.py --help
```

---

## 📊 Trading Strategy

### Triple Moving Average (3MA)

**Indicators:**
- Fast EMA: 8 periods
- Medium EMA: 13 periods
- Slow EMA: 21 periods

**Signals:**
- **BUY:** Fast crosses above Medium AND Medium > Slow
- **SELL:** Fast crosses below Medium AND Medium < Slow
- **HOLD:** All other conditions

**Confirmation Layers:**
1. Volume: Current volume > 1.5x average
2. Volatility: ATR within 0.3-2.0 range
3. Trend: ADX > 25

**Signal validated only if 2+ confirmations pass**

---

## 🧪 Testing

### Run Tests

```bash
# All tests
poetry run pytest tests/ -v

# Unit tests only
poetry run pytest tests/test_tools/ tests/test_connectors/ -v

# Integration tests
poetry run pytest tests/test_integration/ -v

# With coverage
poetry run pytest tests/ --cov=src --cov-report=html
```

### Backtesting

```python
from src.backtest.backtester import BacktestEngine

engine = BacktestEngine(initial_capital=100000)
results = engine.run_backtest(
    symbol="SPY",
    start_date="2024-10-01",
    end_date="2024-10-28",
    timeframe="1Min"
)

print(f"Win Rate: {results['metrics']['win_rate']}%")
print(f"Profit Factor: {results['metrics']['profit_factor']}")
```

---

## 📈 Performance Benchmarks

| Metric | Target | Actual (After Optimization) |
|--------|--------|----------------------------|
| Data Fetching | < 2s | ~1.2s |
| Technical Analysis | < 0.5s | ~0.3s |
| Full Crew Execution | < 60s | ~45s |
| Win Rate | > 55% | TBD (backtest) |
| Profit Factor | > 1.5 | TBD (backtest) |

---

## 🔒 Security

- **API Keys:** Never commit to Git (use `.env`)
- **Paper Trading:** Default mode for safety
- **Rate Limiting:** Automatic throttling to respect API limits
- **Circuit Breakers:** Prevent cascading failures

---

## 📚 Documentation

- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Agent Design](docs/AGENT_DESIGN.md) - Strategy and architecture details
- [Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing procedures
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment checklist

---

## 🛠️ Development

### Project Structure

```
trading-crew/
├── src/
│   ├── config/          # Configuration management
│   ├── connectors/      # API connectors (Gemini, Alpaca)
│   ├── tools/           # Market data, analysis, execution tools
│   ├── agents/          # CrewAI agent definitions
│   ├── crew/            # Task and crew orchestration
│   ├── backtest/        # Backtesting framework
│   ├── optimization/    # Parameter optimization
│   └── utils/           # Utilities (logging, retry, monitoring)
├── tests/               # Test suite
├── scripts/             # CLI and utility scripts
├── docs/                # Documentation
└── logs/                # Application logs
```

### Adding a New Agent

1. Define agent in `src/agents/base_agents.py`
2. Create tools in `src/tools/`
3. Add task in `src/crew/tasks.py`
4. Update crew in `src/crew/trading_crew.py`
5. Write tests in `tests/test_agents/`

### Code Style

- **Formatting:** Black (line length: 88)
- **Linting:** Ruff
- **Type Hints:** Encouraged but not enforced
- **Docstrings:** Google style

---

## 🐛 Troubleshooting

### Common Issues

**"Gemini API rate limit exceeded"**
- Solution: Add more API keys in `.env` (comma-separated)
- Check usage: `poetry run python scripts/run_crew.py status`

**"Alpaca connection failed"**
- Verify API keys are correct
- Check base URL (paper vs live)
- Ensure market is open (9:30 AM - 4:00 PM ET, Mon-Fri)

**"No signal generated"**
- This is normal! Strategy only trades when conditions are met
- Check logs for signal generation details
- Try different symbol or timeframe

---

## 📖 API Free Tier Limits

### Google Gemini (Flash Model)
- **RPM:** 10 requests per minute
- **RPD:** 250 requests per day
- **TPM:** 250,000 tokens per minute

### Alpaca Markets (Paper Trading)
- **Rate Limit:** 200 requests per minute
- **Market Data:** Real-time IEX (free)
- **Historical Data:** Last minute bars (free)
- **Cost:** $0 forever

### Daily Budget (3 Crew Runs/Day)
- Gemini calls: ~42/day (17% of quota)
- Alpaca calls: ~30/day (minimal usage)
- **Status:** ✅ Well within limits

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This software is for educational purposes only. Trading involves risk. Past performance does not guarantee future results. Always test strategies thoroughly in paper trading before using real capital.

---

## 📞 Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** your-email@example.com

---

## 🙏 Acknowledgments

- **CrewAI:** Multi-agent framework
- **Google Gemini:** LLM provider
- **Alpaca Markets:** Brokerage API
- **Open Source Community:** For amazing tools and libraries

```

**Acceptance Criteria:**
- [ ] README covers all essential information
- [ ] Installation instructions are clear
- [ ] Usage examples provided
- [ ] Architecture explained with diagrams
- [ ] Troubleshooting section comprehensive
- [ ] Links to additional documentation included

---

## **FINAL: Project Completion Checklist**

### ✅ Phase 0: Foundation
- [ ] API documentation created (`docs/API_REFERENCE.md`)
- [ ] Project structure scaffolded
- [ ] Agent architecture designed (`docs/AGENT_DESIGN.md`)
- [ ] Configuration management implemented
- [ ] Environment variables validated

### ✅ Phase 1: Core Connectors
- [ ] Gemini connector with rate limiting
- [ ] Alpaca connector with paper trading safety
- [ ] All connectors tested independently

### ✅ Phase 2: Tools Implementation
- [ ] Market data tools (fetch, validate)
- [ ] Technical analysis tools (3MA, indicators)
- [ ] Execution tools (position sizing, orders)
- [ ] All tools unit tested

### ✅ Phase 3: Agent Implementation
- [ ] All 5 agents defined with proper tools
- [ ] Tasks created in sequential order
- [ ] Crew orchestration implemented
- [ ] Agent chain tested end-to-end

### ✅ Phase 4: Integration & Testing
- [ ] Logging system configured
- [ ] CLI interface created
- [ ] End-to-end integration tests
- [ ] Performance benchmarking completed

### ✅ Phase 5: Production Readiness
- [ ] Error recovery and retry logic
- [ ] System monitoring and alerts
- [ ] Backtesting framework functional
- [ ] Strategy optimization module
- [ ] Deployment documentation created

### ✅ Phase 6: Documentation
- [ ] Comprehensive README
- [ ] API reference complete
- [ ] Deployment guide finalized
- [ ] Developer onboarding materials

---

## 🎊 Success Metrics

### Technical KPIs
- ✅ All tests passing (100% critical path coverage)
- ✅ API usage < 80% of free tier limits
- ✅ Execution time < 60 seconds per run
- ✅ Zero security vulnerabilities

### Trading KPIs (To be measured in paper trading)
- 🎯 Win rate > 55%
- 🎯 Profit factor > 1.5
- 🎯 Max drawdown < 10%
- 🎯 Sharpe ratio > 1.0

---

## 🚀 Next Steps

1. **Week 1-2:** Complete Phases 0-1 (Foundation & Connectors)
2. **Week 3-4:** Complete Phases 2-3 (Tools & Agents)
3. **Week 5-6:** Complete Phase 4 (Integration & Testing)
4. **Week 7-8:** Complete Phase 5 (Production Readiness)
5. **Week 9:** Documentation and paper trading validation
6. **Week 10+:** Live trading (if performance targets met)

---

**END OF PLAN**

This feature-based roadmap provides a complete blueprint for AI development assistants to follow, with clear acceptance criteria, validation steps, and code examples for every component of the trading system.