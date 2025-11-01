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

- **Multi-Agent System:** 4 specialized AI agents working in sequence
- **Multi-Strategy Framework:** Supports multiple, dynamically selectable trading strategies.
- **Risk Management:** Portfolio-level constraints and position sizing
- **Paper Trading:** Safe testing with Alpaca paper trading account
- **Backtesting:** Test strategies on historical data
- **CLI Interface:** User-friendly command-line tools
- **Monitoring:** Real-time interactive dashboard and status checks

---

## 🏗️ Architecture

The system is composed of a 4-agent crew that works sequentially to analyze market data, generate signals, manage risk, and execute trades.

```
Data Collection → Signal Generation → Risk Management → Execution
     Agent 1    →      Agent 2      →     Agent 3     →    Agent 4
```

### Agent Responsibilities

1. **DataCollectorAgent:** Fetches and validates OHLCV market data.
2. **SignalGeneratorAgent:** Applies a selected trading strategy to generate and validate a signal.
3. **RiskManagerAgent:** Enforces position sizing and portfolio constraints.
4. **ExecutionAgent:** Places approved trades via the Alpaca API.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (< 3.14)
- Poetry or pip
- WSL2 (if on Windows)
- Alpaca Markets account (paper trading is free)
- Google Gemini API key (free tier available)

### ⚠️ IMPORTANT: Framework Updates (November 2024)

This project has been updated to use the latest versions of all frameworks:
- **CrewAI 1.3.0+** with native LLM integration
- **Google Gemini API** with dynamic model discovery and intelligent quota management
- **Alpaca-py 0.32.0+** for trading and market data

**Enhanced Gemini Connector Features:**
- ✅ **Dynamic Model Discovery**: Automatically queries Gemini API for available models
- ✅ **Intelligent Fallback**: Flash (10 RPM, 250 RPD) → Pro (2 RPM, 50 RPD) → Next key
- ✅ **Per-Key Per-Model Quota Tracking**: Prevents over-use of any single key/model
- ✅ **Free Tier Optimized**: Uses official rate limits, prefers Flash for higher quota
- ✅ **Automatic Key Rotation**: Seamlessly switches keys when quota exhausted

**Key Changes:**
- Uses CrewAI's native `LLM` class (import from `crewai`, not `crewai.llm`)
- Model names include `"gemini/"` prefix for CrewAI
- Requires `crewai[google-genai]` extra for Gemini support

For detailed information on framework usage, see:
- [Master SDK Documentation](docs/MASTER_SDK_DOCUMENTATION.md) - **NEW!** Comprehensive reference
- [Framework Usage Guide](docs/FRAMEWORK_USAGE_GUIDE.md) - Patterns and best practices

### IMPORTANT: Configuring Your Alpaca Data Feed
Alpaca offers different data tiers. This system is designed to work with both the free and paid plans. By default, it uses the free **IEX** data feed.

#### Free Users (Default)
- **Data Feed:** IEX (Investors Exchange)
- **Cost:** Free
- **Details:** This feed provides real-time data but only represents a fraction of the total U.S. market volume.
- **Impact:**
    - Price-based strategies (like Moving Averages) will work perfectly.
    - Volume-based indicators or confirmations may be less reliable due to the limited data scope.

#### Paid Subscribers
- **Data Feed:** SIP (Securities Information Processor)
- **Cost:** Requires a paid Alpaca data subscription.
- **Details:** This is a professional-grade data feed that consolidates data from all U.S. exchanges, providing a complete view of market activity.
- **Configuration:** To use this feed, you must change the following setting in your `.env` file:
  ```
  ALPACA_DATA_FEED="sip"
  ```

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

### CLI Usage
The primary way to interact with the bot is through the CLI script `scripts/run_crew.py`.

**Quick Command Reference:**

| Command | Purpose | Time to Execute |
|---------|---------|-----------------|
| `validate` | Validate configuration | <5 seconds |
| `status` | Check system status | <5 seconds |
| `run` | Execute trading crew | 30-60 seconds |
| `backtest` | Historical strategy test | 1-5 minutes |
| `compare` | Compare strategies | 2-10 minutes |
| `scan` | Market scanner | 5-15 minutes |
| `autonomous` | 24/7 trading mode | Continuous |
| `interactive` | Live dashboard | Continuous |

---

**1. Validate Configuration**
Before first run, validate that all configuration is correct:
```bash
poetry run python scripts/run_crew.py validate
```

This checks:
- ✓ Gemini API keys (format and count)
- ✓ Alpaca API credentials (format)
- ✓ Trading strategy parameters
- ✓ Risk management settings

---

**2. Check System Status**
View current system status and API connectivity:
```bash
# Basic status
poetry run python scripts/run_crew.py status

# Detailed status with API key health tracking
poetry run python scripts/run_crew.py status --detailed

# Get AI-powered recommendations
poetry run python scripts/run_crew.py status --recommendations
```

Example output:
```
╭─────────────────────╮
│ System Status Check │
╰─────────────────────╯

Alpaca API Status:
  ✓ Account Status: AccountStatus.ACTIVE
  ✓ Equity: $99,431.01
  ✓ Mode: Paper Trading
  ✓ Data Feed: IEX

Gemini API Status:
  ✓ API keys found: 10
```

---

**3. Run Trading Crew**
Execute the 4-agent trading workflow for specific assets and strategies:

```bash
# Single symbol, default strategy (3ma)
poetry run python scripts/run_crew.py run --symbol SPY

# Specific strategy
poetry run python scripts/run_crew.py run --symbol AAPL --strategy rsi_breakout

# Multiple strategies on one symbol (sequential)
poetry run python scripts/run_crew.py run --symbol SPY --strategies 3ma,rsi_breakout,macd

# Multiple symbols with parallel execution
poetry run python scripts/run_crew.py run --symbols SPY,QQQ,IWM --strategy 3ma --parallel

# Custom timeframe and data limit
poetry run python scripts/run_crew.py run --symbol NVDA --strategy 3ma --timeframe 5Min --limit 200

# Use market scanner to find opportunities
poetry run python scripts/run_crew.py run --scan --top 5
```

**Available Strategies:**
- `3ma` - Triple Moving Average crossover
- `rsi_breakout` - RSI-based breakout strategy
- `macd` - MACD crossover strategy
- `bollinger_bands_reversal` - Bollinger Bands mean reversion

**Available Timeframes:**
- `1Min`, `5Min`, `15Min`, `30Min`, `1Hour`, `1Day`

---

**4. Backtest a Strategy**
Test strategy performance on historical data:

```bash
# Default: 3ma on SPY for Jan-Jun 2024
poetry run python scripts/run_crew.py backtest

# Custom strategy and symbol
poetry run python scripts/run_crew.py backtest --symbol AAPL --strategy rsi_breakout

# Custom date range
poetry run python scripts/run_crew.py backtest \
    --symbol NVDA \
    --strategy 3ma \
    --start 2024-01-01 \
    --end 2024-12-31
```

Output includes:
- Total trades executed
- Total P&L (profit/loss)
- Win rate (% of profitable trades)
- Sharpe ratio (risk-adjusted returns)
- Sortino ratio (downside risk-adjusted returns)
- Calmar ratio (return vs max drawdown)
- Maximum drawdown

---

**5. Compare Strategies**
Compare multiple strategies side-by-side on the same asset:

```bash
# Compare 3ma vs rsi_breakout on SPY
poetry run python scripts/run_crew.py compare --symbol SPY --strategies 3ma,rsi_breakout

# Compare all strategies on NVDA
poetry run python scripts/run_crew.py compare \
    --symbol NVDA \
    --strategies 3ma,rsi_breakout,macd,bollinger_bands_reversal

# Custom date range
poetry run python scripts/run_crew.py compare \
    --symbol QQQ \
    --strategies 3ma,macd \
    --start 2024-01-01 \
    --end 2024-12-31
```

---

**6. Run Market Scanner**
Scan S&P 100 to find top trading opportunities:

```bash
poetry run python scripts/run_crew.py scan
```

The scanner:
- Analyzes volatility patterns
- Evaluates technical setups
- Filters by liquidity (>1M daily volume)
- Recommends top 5 assets with strategies

**Note:** This command can take 5-15 minutes as it analyzes 100+ stocks.

---

**7. Launch Autonomous Mode**
Run 24/7 autonomous trading:

```bash
poetry run python scripts/run_crew.py autonomous
```

**Before using autonomous mode:**
1. Test thoroughly in DRY_RUN mode
2. Set `AUTONOMOUS_MODE_ENABLED=true` in `.env`
3. Configure `MAX_DAILY_TRADES` and loss limits
4. Only set `DRY_RUN=false` when ready for live trading

**Safety features:**
- Follows market calendar (9:30 AM - 4:00 PM ET)
- Respects daily trade and loss limits
- Automatic error recovery
- Circuit breakers on failures

Press `Ctrl+C` to stop.

---

**8. Interactive Dashboard**
Launch real-time monitoring dashboard:

```bash
poetry run python scripts/run_crew.py interactive
```

Dashboard shows:
- System status (Alpaca & Gemini APIs)
- Current account equity
- Open positions with real-time P&L
- Recent log messages

Auto-refreshes every 5 seconds. Press `Ctrl+C` to exit.

---

**9. View Command Help**
Get detailed help for any command:

```bash
# Main help
poetry run python scripts/run_crew.py --help

# Command-specific help
poetry run python scripts/run_crew.py run --help
poetry run python scripts/run_crew.py backtest --help
poetry run python scripts/run_crew.py status --help
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
python -m unittest discover tests
```

### Backtesting

To backtest a single strategy over a specified time period:
```bash
poetry run python scripts/run_crew.py backtest --symbol SPY --strategy 3ma --start 2024-01-01 --end 2024-06-30
```
```json
{
  "trades": 0,
  "pnl": 0,
  "win_rate": 0,
  "sharpe_ratio": 0,
  "sortino_ratio": 0,
  "calmar_ratio": 0,
  "max_drawdown": 0
}
```

To compare the backtested performance of several strategies on the same asset:
```bash
poetry run python scripts/run_crew.py compare --symbol NVDA --strategies 3ma,rsi_breakout,macd
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

- [Framework Usage Guide](docs/FRAMEWORK_USAGE_GUIDE.md) - **NEW!** Comprehensive guide for CrewAI, Gemini, and Alpaca APIs
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Agent Design](docs/AGENT_DESIGN.md) - Strategy and architecture details
- [Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing procedures

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
