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

## 2. End-to-End & Integration Testing (CLI)

The primary interface for testing and running the system is the Command-Line Interface (CLI) in `scripts/run_crew.py`.

### Running a Single Trading Crew
To run a single, end-to-end execution of the trading crew for a specific symbol and strategy:
```bash
poetry run python scripts/run_crew.py run --symbol AAPL --strategy rsi_breakout
```

### Running the Market Scanner
To run the market scanner and see the top recommended assets:
```bash
poetry run python scripts/run_crew.py scan
```

### Running the Orchestrator with Scanner Input
To run the full, orchestrated cycle (scan followed by parallel trading crews):
```bash
poetry run python scripts/run_crew.py run --scan
```

### Checking System Status
To check the status of API connections and, optionally, get detailed health info and AI recommendations:
```bash
# Basic status
poetry run python scripts/run_crew.py status

# Detailed status with API key health
poetry run python scripts/run_crew.py status --detailed

# Detailed status with AI recommendations
poetry run python scripts/run_crew.py status --detailed --recommendations
```

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

To launch the system in its 20/7 autonomous mode, use the `autonomous` command. The system will run continuously, respecting market hours, until manually stopped.
```bash
poetry run python scripts/run_crew.py autonomous
```

---
*Last Updated: 2025-10-31*
