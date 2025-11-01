# Quick Start Guide

This guide will help you get the AI-Driven Trading Crew up and running in under 5 minutes.

## Prerequisites

- Python 3.11+ (< 3.14)
- pip or Poetry package manager
- Alpaca Markets paper trading account (free)
- Google Gemini API key (free tier available)

## Installation (2 minutes)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd autoanalyst

# 2. Install dependencies
pip install -r requirements.txt
# or with Poetry:
poetry install

# 3. Set up environment
cp .env.template .env
```

## Configuration (2 minutes)

Edit `.env` with your API credentials:

```bash
# Get Gemini API keys from: https://aistudio.google.com/apikey
GEMINI_API_KEYS="your_key_1,your_key_2"

# Sign up for Alpaca at: https://app.alpaca.markets/signup
ALPACA_API_KEY="your_paper_api_key"
ALPACA_SECRET_KEY="your_paper_secret_key"
ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# Keep these defaults for safety
DRY_RUN=true
TRADING_SYMBOL="SPY"
```

## Validation (30 seconds)

Verify your configuration:

```bash
python scripts/run_crew.py validate
```

You should see all 4 checks pass ✓

## Your First Trade (1 minute)

Run a single trading crew in DRY_RUN mode:

```bash
python scripts/run_crew.py run --symbol SPY --strategy 3ma
```

This will:
1. Fetch market data for SPY
2. Apply the 3MA strategy
3. Generate a trading signal
4. Assess risk (in DRY_RUN, no real trades)
5. Show the result

## Check System Status

```bash
# Basic status
python scripts/run_crew.py status

# Detailed status with API health
python scripts/run_crew.py status --detailed
```

## Next Steps

### Try Different Strategies

```bash
# RSI Breakout strategy
python scripts/run_crew.py run --symbol AAPL --strategy rsi_breakout

# MACD Crossover
python scripts/run_crew.py run --symbol NVDA --strategy macd
```

Available strategies:
- `3ma` - Triple Moving Average crossover
- `rsi_breakout` - RSI-based breakout
- `macd` - MACD crossover
- `bollinger_bands_reversal` - Bollinger Bands mean reversion

### Backtest a Strategy

```bash
python scripts/run_crew.py backtest --symbol SPY --strategy 3ma --start 2024-01-01 --end 2024-06-30
```

### Compare Strategies

```bash
python scripts/run_crew.py compare --symbol SPY --strategies 3ma,rsi_breakout,macd
```

### Run Market Scanner

Find the best trading opportunities (takes 5-15 minutes):

```bash
python scripts/run_crew.py scan
```

### Launch Interactive Dashboard

```bash
python scripts/run_crew.py interactive
```

## Safety Checklist Before Live Trading

⚠️ **NEVER set `DRY_RUN=false` until you've:**

- [ ] Tested all commands in DRY_RUN mode
- [ ] Backtested your strategies with positive results
- [ ] Understand the risk management parameters
- [ ] Set appropriate `MAX_RISK_PER_TRADE` and `DAILY_LOSS_LIMIT`
- [ ] Verified your Alpaca account is in paper trading mode
- [ ] Read the full documentation
- [ ] Understand you can lose money with live trading

## Common Issues

### "Connection failed" errors
- **Cause:** Network connectivity or invalid API keys
- **Solution:** Check `.env` file and network connection

### "Rate limit exceeded"
- **Cause:** Too many API calls in short time
- **Solution:** Wait a few minutes, add more Gemini API keys

### "Module not found" errors
- **Cause:** Dependencies not installed
- **Solution:** Run `pip install -r requirements.txt`

## Get Help

```bash
# View all commands
python scripts/run_crew.py --help

# Get help for specific command
python scripts/run_crew.py run --help
```

## Resources

- [Full Documentation](README.md)
- [API Reference](docs/API_REFERENCE.md)
- [Testing Guide](docs/TESTING_GUIDE.md)
- [Agent Design](docs/AGENT_DESIGN.md)

## Support

- GitHub Issues: Report bugs and request features
- Alpaca Support: https://alpaca.markets/support
- Gemini Docs: https://ai.google.dev/docs

---

**Ready to trade?** Remember to always start in DRY_RUN mode and test thoroughly!
