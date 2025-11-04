# AutoAnalyst - AI-Driven Algorithmic Trading System

## Project Overview

AutoAnalyst is a production-ready algorithmic trading system that combines multi-agent AI orchestration (CrewAI), Google Gemini LLM integration, and Alpaca Markets API for automated trading. The system employs a 4-agent workflow to analyze market data, generate signals, manage risk, and execute trades across multiple strategies.

**Core Capabilities:**
- Multi-agent trading crews with parallel execution (max 3 concurrent)
- Market scanning across S&P 100 for opportunity discovery
- 4 built-in trading strategies with data-feed-aware validation
- Backtesting and strategy comparison engine
- Autonomous 24/7 trading mode with market calendar awareness
- Thread-safe rate limiting and intelligent quota management

**Technology Stack:**
- **Language:** Python 3.11-3.13
- **AI Framework:** CrewAI 1.3.0+ with Google Gemini LLMs
- **Trading API:** Alpaca Markets (Paper & Live)
- **Data Processing:** pandas, numpy
- **Configuration:** Pydantic Settings with validation
- **CLI:** Click with Rich terminal UI

## Project Structure

```
/home/planetazul3/autoanalyst/
├── main.py                          # Main entry point for live trading loop
├── pyproject.toml                   # Poetry dependencies
├── requirements.txt                 # pip dependencies
├── .env                            # Environment configuration (git-ignored)
├── scripts/
│   ├── run_crew.py                 # Comprehensive CLI for all operations
│   ├── setup_env.sh                # Environment setup script
│   └── validate_config.py          # Configuration validator
├── src/
│   ├── agents/
│   │   ├── base_agents.py          # 4-agent trading workflow definitions
│   │   └── scanner_agents.py       # Market scanner agent definitions
│   ├── config/
│   │   └── settings.py             # Pydantic settings with validation
│   ├── connectors/
│   │   ├── alpaca_connector.py     # Trading & market data client
│   │   ├── gemini_connector.py     # Basic Gemini connector with key rotation
│   │   └── gemini_connector_enhanced.py # Dynamic model discovery & quota mgmt
│   ├── crew/
│   │   ├── crew_context.py         # Shared context singleton
│   │   ├── market_scanner_crew.py  # S&P 100 scanning crew
│   │   ├── orchestrator.py         # Parallel crew execution manager
│   │   ├── tasks.py                # Task definitions for agents
│   │   └── trading_crew.py         # Main 4-agent trading workflow
│   ├── strategies/
│   │   ├── base_strategy.py        # Abstract strategy interface
│   │   ├── triple_ma.py            # Triple moving average strategy
│   │   ├── rsi_breakout.py         # RSI breakout strategy
│   │   ├── macd_crossover.py       # MACD crossover strategy
│   │   ├── bollinger_bands_reversal.py # Bollinger Bands strategy
│   │   └── registry.py             # Strategy factory
│   ├── tools/
│   │   ├── analysis_tools.py       # Technical indicators (RSI, MACD, ADX, ATR, etc.)
│   │   ├── execution_tools.py      # Order placement & risk management
│   │   ├── market_data_tools.py    # OHLCV data fetching & validation
│   │   └── market_scan_tools.py    # S&P 100 scanning with parallel fetching
│   └── utils/
│       ├── backtester_v2.py        # Historical backtesting engine
│       ├── global_scheduler.py     # Autonomous 24/7 scheduler
│       ├── logger.py               # Structured logging setup
│       ├── market_calendar.py      # Market hours tracking
│       └── state_manager.py        # State persistence
├── tests/
│   ├── test_connectors/
│   └── test_tools/
└── logs/                           # Log files (auto-created)
```

## Key Architecture Patterns

### 0. CrewAI Tool Communication Architecture ⚠️ **CRITICAL**

**LLM-First Design Principle**: CrewAI routes ALL tool communication through the LLM with JSON serialization. This is fundamentally different from traditional Python function calling.

**🚫 What Does NOT Work (Anti-Patterns):**

1. **Passing Complex Python Objects Between Tools**
   ```python
   # ❌ WRONG: This will fail in production
   @tool
   def fetch_data() -> Dict[str, pd.DataFrame]:
       return {"SPY": dataframe}  # DataFrame gets serialized to string
   
   @tool
   def analyze(data: Dict[str, pd.DataFrame]):
       df = data["SPY"]  # This is now a STRING, not DataFrame
       return df['high'].mean()  # TypeError: string indices must be int
   ```

2. **Assuming Tool Output Passes Directly to Next Tool**
   - Reality: Tool A → Returns DataFrame → LLM sees string representation → CrewAI serializes to JSON → Tool B receives string
   - This breaks: DataFrames, NumPy arrays, custom classes, file handles

3. **Ignoring Serialization in Tool Design**
   - All tool parameters MUST be JSON-serializable: `str`, `int`, `float`, `bool`, `list`, `dict`
   - If you see `Dict[str, pd.DataFrame]` as a parameter type, it's a design error

**✅ What DOES Work (Correct Patterns):**

**Pattern 1: Independent Tool Fetching (Recommended)**
```python
# Each tool fetches its own data based on simple parameters
@tool
def analyze_volatility(symbol: str, timeframe: str = "1D") -> dict:
    """Analyze volatility for a symbol. Tool fetches its own data internally."""
    # Fetch data inside the tool
    connector = AlpacaConnector()
    df = connector.get_market_data(symbol, timeframe)
    
    # Calculate and return JSON-serializable results
    volatility = df['high'].std()
    return {
        "symbol": symbol,
        "volatility": float(volatility),
        "recommendation": "high" if volatility > threshold else "low"
    }
```

**Pattern 2: Knowledge Sources (for Large Datasets)**
```python
# Store data in ChromaDB, query by symbol
from crewai import KnowledgeSource

market_data_source = KnowledgeSource(
    name="market_data",
    storage_path="./data/market_knowledge"
)

# Load data as markdown/CSV text
market_data_source.add(
    content="BTC/USD OHLCV Data\n...\n2025-11-04,68500,69000,68000,68800,1200000",
    metadata={"symbol": "BTC/USD", "date_range": "2025-10-01_to_2025-11-04"}
)

# Agent queries knowledge source (text-based)
agent = Agent(
    knowledge_sources=[market_data_source],
    instructions="Query market_data knowledge source for symbol data"
)
```

**Pattern 3: Shared Memory (for Session State)**
```python
# Store simple state, not complex objects
from crewai import Crew

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True  # Enables short-term memory
)

# Store simple facts as text
# "SPY volatility is 15.3"
# "BTC/USD passed liquidity filter"
# "Last scan found 3 opportunities"
```

**Pattern 4: CrewAI Flows (for Complex Pipelines)**
```python
from crewai.flow.flow import Flow, listen, start

class TradingFlow(Flow):
    @start()
    def fetch_data(self):
        # Keep DataFrames in Flow code (not passed to Crews)
        self.market_data = {"SPY": fetch_dataframe()}
        return list(self.market_data.keys())  # Pass symbol list only
    
    @listen(fetch_data)
    def analyze_symbols(self, symbols: list[str]):
        # Crew receives symbol names (strings), not DataFrames
        results = crew.kickoff(inputs={"symbols": symbols})
        return results
```

**Critical Rules for AutoAnalyst Development:**

1. **🚨 NEVER pass DataFrames between tools** - Redesign tools to fetch their own data
2. **🚨 NEVER assume tool outputs pass directly** - LLM always intermediates
3. **✅ ALWAYS use simple types in tool parameters** - str, int, float, bool, list, dict
4. **✅ ALWAYS make tools self-sufficient** - Each tool fetches/computes what it needs
5. **✅ PREFER Independent Tool pattern** - Simplest and most reliable
6. **✅ USE Knowledge Sources for large data** - Market data, historical records
7. **✅ USE Memory for session state** - Simple facts, not objects
8. **✅ USE Flows for complex workflows** - Keep DataFrames in Flow, pass IDs to Crews

**For Complete Reference**: See `docs/CREWAI_REFERENCE.md` (70KB comprehensive guide)

**Current Impact**: Market scanner tools violate these rules (Phase 4 fixes this).

---

### 1. Multi-Agent Trading Workflow (4 Agents)
**Sequential execution with context passing:**
1. **Data Collector Agent** → Fetches & validates OHLCV data from Alpaca
2. **Signal Generator Agent** → Applies strategy to generate BUY/SELL/HOLD signals
3. **Risk Manager Agent** → Enforces position sizing & portfolio constraints
4. **Execution Agent** → Places approved trades (or logs in DRY_RUN mode)

**Implementation:** `src/crew/trading_crew.py`, `src/agents/base_agents.py`, `src/crew/tasks.py`

### 2. Parallel Crew Orchestration
- Thread pool execution (max 3 workers) via `ThreadPoolExecutor`
- Thread-safe rate limiting using locks in `gemini_connector.py` and `orchestrator.py`
- Each thread gets its own `TradingCrew` instance to avoid state conflicts
- Market scanner crew runs first, then distributes work to trading crews

**Implementation:** `src/crew/orchestrator.py`

### 3. Gemini LLM Integration (Two Implementations)

**Basic Connector** (`gemini_connector.py`):
- Key rotation with health tracking & exponential backoff
- Simple rate limiting (RPM/RPD)
- Model fallback (Flash → Pro)

**Enhanced Connector** (`gemini_connector_enhanced.py`):
- Dynamic model discovery via Google Gemini API
- Per-key, per-model quota tracking (Flash: 10 RPM/250 RPD, Pro: 2 RPM/50 RPD)
- Intelligent fallback: Flash (preferred) → Pro → Next key
- Thread-safe with locking for parallel execution

**Current Usage:** Enhanced connector is used in production for optimal quota management.

### 4. Lazy Initialization Pattern
Crews use proxy objects (`_TradingCrewProxy`, `_MarketScannerCrewProxy`) to avoid API calls during module import. Actual initialization happens on first `run()` call using thread-safe double-checked locking.

**Why:** Prevents LLM API calls when importing modules for testing or help commands.

### 5. Strategy Design Pattern
All strategies inherit from `TradingStrategy` abstract base class:
- `calculate_indicators(df)` → Returns dict of indicator Series
- `generate_signal(df)` → Returns signal dict with confidence
- `validate_signal(df, signal, data_feed)` → Applies confirmations (volume, ADX, etc.)

**Data-Feed Awareness:** Strategies weight volume confirmation differently for IEX (free, lower weight) vs SIP (paid, higher weight) data feeds.

## Build & Run Instructions

### Environment Setup
```bash
# 1. Clone repository (if not already done)
cd /home/planetazul3/autoanalyst

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies (choose one)
pip install -r requirements.txt
# OR
poetry install

# 4. Set up environment variables
cp .env.example .env  # If example exists, otherwise create new
# Edit .env with your API keys:
# - GEMINI_API_KEYS (comma-separated)
# - ALPACA_API_KEY
# - ALPACA_SECRET_KEY
```

### Configuration Validation
```bash
# Always run this first to verify setup
python scripts/run_crew.py validate

# Check system status
python scripts/run_crew.py status
python scripts/run_crew.py status --detailed  # Shows API key health
```

### Running the System

**Single Trading Crew:**
```bash
# Run for single symbol with default strategy (3ma)
python scripts/run_crew.py run --symbols SPY

# Run with specific strategy
python scripts/run_crew.py run --symbols AAPL --strategies rsi_breakout

# Multiple strategies on one symbol (sequential)
python scripts/run_crew.py run --symbols SPY --strategies 3ma,rsi_breakout,macd

# Multiple symbols and strategies (parallel)
python scripts/run_crew.py run --symbols SPY,QQQ --strategies 3ma,macd --parallel
```

**Market Scanner Mode:**
```bash
# Scan S&P 100 and auto-trade top 3 assets
python scripts/run_crew.py run --scan --top 3
```

**Backtesting:**
```bash
# Single strategy backtest
python scripts/run_crew.py backtest --symbol SPY --strategy 3ma --start 2024-01-01 --end 2024-06-30

# Compare multiple strategies
python scripts/run_crew.py compare --symbol SPY --strategies 3ma,rsi_breakout,macd --start 2024-01-01 --end 2024-06-30
```

**Autonomous 24/7 Trading:**
```bash
# Requires AUTONOMOUS_MODE_ENABLED=true in .env
python scripts/run_crew.py autonomous
```

**Interactive Dashboard:**
```bash
python scripts/run_crew.py interactive
```

### Testing
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_connectors/test_alpaca_connector.py

# Run with coverage
pytest --cov=src tests/
```

## Environment Variables (.env)

**Required:**
```bash
# Gemini API Keys (comma-separated)
GEMINI_API_KEYS=key1,key2,key3

# Alpaca API
ALPACA_API_KEY=PKxxxxxxxxxxxx
ALPACA_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
# ALPACA_BASE_URL=https://api.alpaca.markets      # Live trading (DANGER!)
ALPACA_DATA_FEED=iex  # 'iex' (free) or 'sip' (paid)
```

**Optional (with defaults):**
```bash
# Trading Parameters
TRADING_SYMBOL=SPY
MA_FAST_PERIOD=8
MA_MEDIUM_PERIOD=13
MA_SLOW_PERIOD=21
VOLUME_THRESHOLD=1.5
ADX_THRESHOLD=25.0

# Risk Management
MAX_RISK_PER_TRADE=0.02  # 2%
MAX_OPEN_POSITIONS=3
DAILY_LOSS_LIMIT=0.05    # 5%

# LLM Configuration
DEFAULT_LLM_MODEL=google/gemini-2.5-flash
PRIMARY_LLM_MODELS=gemini-2.5-flash
FALLBACK_LLM_MODELS=gemini-2.5-pro

# Rate Limiting (Free Tier)
RATE_LIMIT_RPM=9   # Flash: 10 RPM, Pro: 2 RPM
RATE_LIMIT_RPD=200 # Flash: 250 RPD, Pro: 50 RPD

# System
DRY_RUN=true  # ALWAYS TEST IN DRY_RUN FIRST!
LOG_LEVEL=INFO
AUTONOMOUS_MODE_ENABLED=false
MAX_DAILY_TRADES=10
```

## Common Issues & Solutions

### Issue: "All API keys exhausted their quotas"
**Solution:**
1. Check rate limits: Flash (10 RPM/250 RPD), Pro (2 RPM/50 RPD) per key
2. Add more API keys (comma-separated in GEMINI_API_KEYS)
3. Reduce parallel execution (max_workers in orchestrator)
4. Wait for quota reset (daily at midnight UTC)

### Issue: "Failed to get working Gemini client"
**Solutions:**
1. Verify API keys are valid: `python scripts/run_crew.py status --detailed`
2. Check internet connectivity
3. Ensure keys have proper format (no extra spaces/newlines)
4. Try basic health check: `gemini_manager.get_client(skip_health_check=True)`

### Issue: Alpaca "rate limit exceeded"
**Solution:**
- Increase timeframe for data fetching (e.g., 5Min instead of 1Min)
- Reduce scan frequency in autonomous mode
- Switch to SIP data feed (paid) for higher limits

### Issue: Market scanner takes too long (7+ minutes)
**Solution:** Already optimized with parallel fetching (ThreadPoolExecutor, max_workers=10). Fetching 100 symbols now takes ~1 minute instead of 7+.

### Issue: "Trading crew execution failed" during parallel runs
**Solution:**
- Check thread safety: Each crew should have its own instance
- Review logs in `logs/trading_crew_*.log` for detailed errors
- Ensure Gemini connector uses locks (already implemented)

## Code Style & Best Practices

### General Guidelines
1. **Thread Safety:** Always use locks when accessing shared resources in parallel execution contexts
2. **Error Handling:** Use try-except blocks with detailed logging; never fail silently
3. **Type Hints:** Always include type hints for function parameters and returns
4. **Docstrings:** Use Google-style docstrings for all public functions/classes
5. **Imports:** Group imports (stdlib, third-party, local) with blank line separation
6. **Logging:** Use module-level logger: `logger = logging.getLogger(__name__)`

### Strategy Development
When adding new strategies:
1. Inherit from `TradingStrategy` in `src/strategies/base_strategy.py`
2. Implement all abstract methods: `calculate_indicators`, `generate_signal`, `validate_signal`
3. Set class attributes: `name`, `description`, `min_bars_required`
4. Register in `src/strategies/registry.py`
5. Add data-feed-aware validation (weight volume differently for IEX vs SIP)

### Agent Development
When modifying agents:
1. Agents are defined in factory classes (`TradingAgents`, `ScannerAgents`)
2. Each agent gets an LLM instance passed in (for consistent model usage)
3. Use `@tool` decorator for tool definitions
4. Tools must return dict with consistent structure
5. Keep agents focused on single responsibilities

### Testing Requirements
- All new strategies must have backtesting validation
- Mock external API calls in tests (Alpaca, Gemini)
- Test both DRY_RUN and live modes (with paper account)
- Verify thread safety with parallel execution tests

## Important Security Notes

1. **API Keys:** Never commit `.env` file or log full API keys (only last 4 chars)
2. **Live Trading:** ALWAYS test in DRY_RUN mode first (set DRY_RUN=true)
3. **Paper Trading:** Use paper-api.alpaca.markets URL before going live
4. **Risk Limits:** Enforce daily loss limits and max position constraints
5. **Logging:** Sanitize sensitive data in logs (use `mask_api_key()` helper)

## Performance Considerations

1. **Parallel Execution:** Limited to 3 concurrent crews to avoid API rate limits
2. **Market Scanning:** Parallel fetching reduces scan time from 7+ min to ~1 min
3. **Rate Limiting:** Thread-safe implementation prevents quota exhaustion
4. **Caching:** Settings use cached key parsing (thread-safe with locks)
5. **Data Feed:** IEX (free) vs SIP (paid) affects volume data quality

## Deployment Notes

For production deployment:
1. Set `DRY_RUN=false` only after thorough testing
2. Use SIP data feed for better data quality (paid)
3. Monitor logs in `logs/` directory
4. Set up log rotation (not implemented yet)
5. Use `autonomous` mode for 24/7 operation with market calendar awareness
6. Implement alert system for critical errors (future enhancement)
7. Regular backups of state files in `data/` directory

## Related Documentation

- **CrewAI Reference:** `docs/CREWAI_REFERENCE.md` - **CRITICAL!** Architecture patterns, data sharing, anti-patterns (November 4, 2025)
- **Feature Roadmap:** `FEATURE_ROADMAP.md` - Development phases and priorities (includes Phase 4 architecture fix)
- **Phase 1 Summary:** `docs/PHASE1_CRITICAL_FIXES.md` - Critical fixes completed
- **Multi-Market Plan:** `docs/MULTIMARKET_IMPLEMENTATION.md` - 24/7 trading features
- **Crypto Verification:** `docs/ALPACA_CRYPTO_VERIFICATION.md` - Alpaca crypto support
- **Framework Usage:** `docs/FRAMEWORK_USAGE_GUIDE.md`
- **API Reference:** `docs/API_REFERENCE.md`
- **Testing Guide:** `docs/TESTING_GUIDE.md`
- **Agent Design:** `docs/AGENT_DESIGN.md`
- **Master SDK Docs:** `docs/MASTER_SDK_DOCUMENTATION.md`

## Quick Reference Commands

```bash
# Validate configuration
python scripts/run_crew.py validate

# Check status
python scripts/run_crew.py status --detailed

# Run single crew
python scripts/run_crew.py run --symbols SPY --strategies 3ma

# Scan market
python scripts/run_crew.py scan

# Backtest
python scripts/run_crew.py backtest --symbol SPY --strategy 3ma

# Interactive dashboard
python scripts/run_crew.py interactive

# Autonomous mode (24/7)
python scripts/run_crew.py autonomous
```

## Development Workflow

When working on this project:
1. Always activate virtual environment: `source venv/bin/activate`
2. Validate config before making changes: `python scripts/run_crew.py validate`
3. Test changes in DRY_RUN mode first
4. Run tests before committing: `pytest`
5. Check logs for detailed error information: `logs/trading_crew_*.log`
6. Use interactive dashboard for live monitoring
7. Keep API keys secure and never commit them

**User Preferences & Project Approach:**
- **Feature-based development**: Follow `FEATURE_ROADMAP.md` phases, not time-based schedules
- **Documentation management**: Delete redundant files permanently (don't archive unless explicitly requested)
- **Single source of truth**: Avoid creating duplicate documentation; consolidate information
- **AI-driven development**: Development velocity depends on feature complexity, not calendar deadlines
- **Trust the roadmap**: `FEATURE_ROADMAP.md` is the authoritative source for development priorities

**Development Status:**

- **Phase 1**: ✅ COMPLETE (Critical system fixes) - November 2, 2025
- **Documentation Cleanup**: ✅ COMPLETE - Removed 11 redundant files (4,094 lines)
- **Phase 2**: ✅ COMPLETE (Multi-market 24/7 trading) - November 3, 2025
- **Phase 3**: ✅ COMPLETE (100% - 4/4 features) - Comprehensive testing & validation
  - Feature 3.1: ✅ COMPLETE - 24-hour integration test (9 tests)
  - Feature 3.2: ✅ COMPLETE - Input validation framework (35 tests)
  - Feature 3.3: ✅ COMPLETE - Test coverage expansion (80% achieved, 109 tests)
  - Feature 3.4: ✅ COMPLETE - Performance testing (15 tests)
  - **Completion**: November 3, 2025
- **Phase 4**: ✅ COMPLETE - Architecture Revision & Production Hardening (November 4, 2025)
  - **Issue Discovered**: November 4, 2025 (autonomous testing)
  - **Root Cause**: CrewAI DataFrame serialization breaks market scanner
  - **Solution**: Independent Tool Fetching pattern (tools fetch own data)
  - **Status**: 4.1-4.4 features complete, validation partial (Gemini API 503 errors)
  - **Result**: 99 symbols processed successfully (0% error rate vs 100% before)

**Development Approach**: Feature-based implementation (AI-driven, not calendar-based)

**Recent Milestones:**
- November 3, 2025: **Feature 3.3 completion** - 80% test coverage achieved (297 tests passing)
- November 3, 2025: **Phase 2 completion** - Multi-market 24/7 trading (7/7 features, 3.7x uptime increase)
- November 2, 2025: Phase 1 completion, documentation restructure & cleanup
- Feature roadmap converted from time-based (weeks/days) to feature-based (phases)
- Consolidated 22 markdown files → 12 essential files (single source of truth)
- Repository ready for Phase 3.4 performance testing

**Phase 2 Achievements:**
- 7/7 features complete (100%): Asset classification, multi-asset data, dynamic universes, market-aware scanner, asset-class-aware strategies, intelligent market rotation, adaptive 24/7 scheduler
- 34/34 tests passing (100% pass rate)
- System uptime: 27% → 100% (3.7x improvement)
- Trading hours: 6.5h/day → 24h/day
- Markets supported: US_EQUITY + CRYPTO (24/7) + FOREX
- Adaptive scan intervals: 5-30 minutes based on market activity

**Phase 3 Achievements (Complete):**
- 4/4 features complete (100%): 24h integration, input validation, test coverage expansion, performance testing
- 312/312 tests passing (100% pass rate)
- Test coverage: 43% → 80% (+37pp improvement)
- 124 new comprehensive tests added (109 coverage + 15 performance)
- 7 modules at 90-100% coverage (backtester, logger, execution_tools, global_scheduler, market_calendar, orchestrator, state_manager)
- Performance validated: instantiation <2s, memory <100MB, thread-safe
- Zero flaky tests, all meaningful validations
- **Completion Date**: November 3, 2025

---

**Last Updated:** November 4, 2025
**Project Status:** Phase 4 complete - Market scanner refactored and functional (Independent Tool Fetching pattern)
**Current Version:** 0.4.0 (Phase 4 architecture fix validated)
