# Testing Protocols & Guide

This document outlines the testing strategy for the AI-Driven Trading Crew project, ensuring reliability, correctness, and robustness.

## 1. Unit Testing

**Framework:** Python's built-in `unittest` module.

**Location:** Unit tests are located in the `tests/` directory, which mirrors the `src/` directory structure. For example, tests for `src/connectors/alpaca_connector.py` are in `tests/test_connectors/test_alpaca_connector.py`.

**Execution:** To run all unit tests, execute the following command from the project root:
```bash
python -m unittest discover tests
```

**Principles:**
- **Isolation:** Each test should be independent and not rely on the state of other tests.
- **Mocking:** External services (like the Alpaca API or the Gemini LLM) should be mocked using `unittest.mock` to ensure tests are fast, repeatable, and don't incur costs.
- **Coverage:** Aim for high test coverage on critical business logic, especially in the `tools` and `connectors` modules.

## 2. Integration Testing

**Objective:** To verify the end-to-end functionality of the trading crew, from data fetching to order execution.

**Environment:** Integration tests should be run against the Alpaca paper trading environment to simulate real-world conditions without risking capital.

**Execution:** Integration tests are typically run manually or as part of a CI/CD pipeline. The main entry point for an end-to-end run is:
```bash
poetry run python scripts/run_crew.py run --symbol SPY --limit 10
```

**Validation:**
- Verify that the crew completes a full run without errors.
- Check the logs in the `logs/` directory for any warnings or unexpected behavior.
- Confirm that simulated orders appear in the Alpaca paper trading dashboard.

## 3. Backtesting

**Objective:** To evaluate the historical performance of the trading strategy.

**Status:** Backtesting is a planned feature and is not yet implemented. When it is, it will involve running the trading strategy against historical market data to calculate key performance metrics.

**Key Metrics (to be implemented):**
- **Win Rate:** Percentage of profitable trades.
- **Profit Factor:** Gross profit / gross loss.
- **Max Drawdown:** The largest peak-to-trough decline in portfolio value.

## 4. Coverage & Reporting

**Tool:** `coverage.py` is the recommended tool for measuring test coverage.

**Execution:** To run tests with coverage reporting:
```bash
coverage run -m unittest discover tests
coverage report -m
```

**Goal:** Strive for a minimum of 80% test coverage on all new code.

_Last Updated: 2025-10-30_
