# API Reference Documentation

This document provides an overview of the key classes, modules, and external APIs used in the Talos Algo AI trading system.

---

## 1. Core Modules & Classes

### `src.crew.orchestrator.TradingOrchestrator`
⚠️ **Note**: Market scanner component requires Phase 4 refactoring (November 4, 2025)

The main entry point for running trading cycles. It's responsible for:
- Running the `MarketScannerCrew` (⚠️ currently non-functional due to DataFrame serialization issue)
- Dispatching `TradingCrew` instances in parallel for the top assets (or specified symbols)
- Managing the `GlobalRateLimiter`

**Current Workaround**: Use orchestrator with explicit symbol list instead of scanner results.

### `src.utils.global_scheduler.AutoTradingScheduler`
The engine for 24/7 autonomous operation. Its responsibilities include:
- Running an infinite loop to manage trading cycles.
- Using the `MarketCalendar` to check if target markets are open.
- Calling the `TradingOrchestrator` to execute a cycle.
- Persisting system state with the `StateManager`.

### `src.utils.backtester_v2.BacktesterV2`
A utility for running historical simulations of trading strategies.
- Used by the `backtest` and `compare` CLI commands.
- Implements an event-driven architecture to prevent lookahead bias.
- Models slippage and commissions for more realistic results.
- Fetches historical data and simulates trades to calculate advanced performance metrics like Sharpe Ratio, Sortino Ratio, Calmar Ratio, and Max Drawdown.

### `src.strategies` Module
This module contains the pluggable trading strategies. All strategies inherit from the `TradingStrategy` abstract base class and implement a consistent interface.

---

## 2. External APIs

### 2.1. Google Gemini API
- **Purpose:** Provides the core intelligence for all AI agents.
- **Integration:** The `src.connectors.gemini_connector.GeminiConnectionManager` provides a production-grade client with:
    - Multi-model fallback (e.g., Flash to Pro).
    - Automatic API key rotation and health tracking.
    - Exponential backoff and robust retry mechanisms.
- **Further Reading:** [Google AI for Developers](https://ai.google.dev/)

### 2.2. Alpaca Markets API
- **Purpose:** Provides market data and trade execution services.
- **Integration:** The `src.connectors.alpaca_connector.AlpacaConnectionManager` handles connections for both historical data and live trading.
- **Mode:** The system is configured for paper trading by default for safety.
- **Further Reading:** [Alpaca API Documentation](https://alpaca.markets/docs)

---

## 3. Frameworks

### 3.1. CrewAI
- **Purpose:** The core framework for orchestrating the multi-agent system.
- **Usage:** Used to define the agents, tasks, and crews for both market scanning and trading.
- **Architecture Note (🔴 November 4, 2025):** CrewAI uses LLM-first design with JSON serialization for all tool parameters. See [CrewAI Reference Guide](CREWAI_REFERENCE.md) for architecture patterns and data sharing limitations.
- **Further Reading:** [CrewAI Documentation](https://docs.crewai.com/)

### 3.2. Click
- **Purpose:** Used to build the command-line interface (`scripts/run_crew.py`).
- **Usage:** Powers all CLI commands, options, and help text.
- **Further Reading:** [Click Documentation](https://click.palletsprojects.com/)

### 3.3. Rich
- **Purpose:** Provides rich text and beautiful formatting in the terminal.
- **Usage:** Used throughout the CLI for tables, panels, and syntax highlighting to improve usability.
- **Further Reading:** [Rich Documentation](https://rich.readthedocs.io/)

---

*This document was last updated November 4, 2025 to reflect Phase 3 completion and Phase 4 architecture discovery.*
