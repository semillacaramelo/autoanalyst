# Testing & Validation Guide

This document outlines the testing strategy and operational commands for the Talos Algo AI trading system.

## 1. Unit Testing

**Framework:** Python's built-in `unittest` module.

**Location:** Unit tests are located in the `tests/` directory, which mirrors the `src/` directory structure.

**Execution:**
```bash
python -m unittest discover tests
```

**Principles:**
- **Isolation:** Tests should be independent.
- **Mocking:** External services (Alpaca, Gemini) should be mocked to ensure tests are fast and repeatable.
- **Coverage:** Aim for high test coverage on critical logic in the `strategies`, `tools`, and `utils` modules.

### Connector Testing
Connectors in `src/connectors` are critical for interacting with external services. When writing tests for connectors, ensure the following:
- **Mock External Libraries:** The actual client libraries (e.g., `alpaca-trade-api`, `langchain-google-genai`) should be mocked at the module level.
- **Simulate API Failures:** Tests should simulate various API failure modes, such as authentication errors, rate limit errors, and transient server errors.
- **Verify Resilience:** For connectors that implement resilience logic (e.g., retries, failover), tests must verify that this logic behaves as expected. The test suite for the `GeminiConnectionManager` in `tests/test_connectors/test_gemini_connector.py` is a good example of this.

## 2. End-to-End & Integration Testing (CLI)

The primary interface for testing and running the system is the Command-Line Interface (CLI) located at `scripts/run_crew.py`. All operational tasks are managed through this interface.

### Running a Single Trading Crew
To bypass the scanner and run a single, end-to-end execution of the trading crew for a specific symbol and strategy:
```bash
poetry run python scripts/run_crew.py run --symbol AAPL --strategy rsi_breakout
```

### Running the Market Scanner Only
To run the market scanner to see the top recommended assets without executing any trades:
```bash
poetry run python scripts/run_crew.py scan
```

### Checking System Status
To check the status of API connections and system health.
```bash
# Basic status check
poetry run python scripts/run_crew.py status

# Detailed status including API key health and rate limits
poetry run python scripts/run_crew.py status --detailed
```

### Launching the Interactive Dashboard
To launch a real-time, terminal-based dashboard for live system monitoring:
```bash
poetry run python scripts/run_crew.py interactive
```
**Note:** This command is intended for real-time monitoring and will not produce a static output file.

## 3. Backtesting

**Objective:** To evaluate the historical performance of trading strategies.

**Implementation:** The event-driven backtesting engine is located in `src/utils/backtester_v2.py`.

### Running a Single Backtest
To backtest a single strategy over a specified time period:
```bash
poetry run python scripts/run_crew.py backtest --symbol SPY --strategy 3ma --start 2024-01-01 --end 2024-06-30
```

### Comparing Multiple Strategies
To compare the backtested performance of several strategies on the same asset:
```bash
poetry run python scripts/run_crew.py compare --symbol NVDA --strategies 3ma,rsi_breakout,macd
```

**Key Metrics Calculated:**
- Total number of trades
- Net Profit/Loss (P&L)
- Win Rate (%)
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Maximum Drawdown

## 4. Autonomous Operation

To launch the system in its 24/7 autonomous mode, use the `autonomous` command. The system will run continuously, respecting market hours, until manually stopped.
```bash
poetry run python scripts/run_crew.py autonomous
```

---
*Last Updated: 2025-10-31*
