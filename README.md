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

**1. Check System Status**
Before running any trading operations, check that all API connections are working.
```bash
poetry run python scripts/run_crew.py status
```

**2. Run an Orchestrated Cycle (Scan-Then-Trade)**
This is the standard operational mode. The system will scan the market for opportunities and then execute trades on the top candidates.
```bash
poetry run python scripts/run_crew.py run --scan
```

**3. Run a Specific Trade**
To bypass the scanner and execute a trade for a single symbol with a specific strategy:
```bash
poetry run python scripts/run_crew.py run --symbol NVDA --strategy macd
```

**4. View All Commands**
To see the full list of available commands and options:
```bash
poetry run python scripts/run_crew.py --help
```

### Running the Bot in Autonomous Mode
For 24/7 operation, the bot can be launched in autonomous mode. It will continuously scan the market, execute trades, and manage its state according to the global market calendar.
```bash
poetry run python scripts/run_crew.py autonomous
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