# Agent Architecture & Trading Strategy

## 1. Multi-Strategy Framework

### Core Concept
The system has been refactored to support multiple, dynamically selectable trading strategies. The original Triple Moving Average (3MA) strategy is now one of several available options.

### Available Strategies

1.  **Triple Moving Average (3ma):**
    *   **Signal:** Crossover of 8, 13, and 21-period EMAs.
    *   **Confirmations:** Volume and ADX trend strength.

2.  **RSI Breakout (rsi_breakout):**
    *   **Signal:** RSI(14) crossing above 30 (BUY) or below 70 (SELL).
    *   **Confirmations:** Volume spike, ADX > 25, and price relative to 50 SMA.

3.  **MACD Crossover (macd):**
    *   **Signal:** MACD line crossing over the signal line.
    *   **Confirmations:** Volume and RSI momentum (RSI > 50 for BUY, < 50 for SELL).

4.  **Bollinger Bands Reversal (bollinger):**
    *   **Signal:** Price touching the lower/upper band with confirming RSI.
    *   **Confirmations:** Volatility expansion (Bollinger Band Squeeze release) and bullish/bearish candlestick patterns.

---

## 2. Agent Architecture

### 2.1. Market Scanner Crew
This crew runs first to identify a prioritized list of trading opportunities.

```
┌─────────────────────────────────────────┐
│   1. VolatilityAnalyzerAgent            │
│   Finds assets with ideal volatility    │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   2. TechnicalSetupAgent                │
│   Scores technical strength             │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   3. LiquidityFilterAgent               │
│   Removes illiquid assets               │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   4. MarketIntelligenceChief            │
│   Synthesizes results into a top-5 list │
└─────────────────────────────────────────┘
```

### 2.2. Trading Crew
The Trading Crew is a 4-agent system responsible for executing trades for a single financial instrument based on a selected strategy. The original 5-agent design has been streamlined by removing the `SignalValidatorAgent` and integrating its logic directly into the strategy classes.

The data processing and execution flow is as follows:
DataCollectorAgent → SignalGeneratorAgent → RiskManagerAgent → ExecutionAgent

### Agent Specifications (Trading Crew)

#### Agent 1: DataCollectorAgent
**Role:** Market Data Specialist
**Goal:** Fetch accurate, complete OHLCV data for analysis.
**Responsibilities:**
- Fetch historical bar data from Alpaca.
- Ensure data quality and completeness.
- Pass the data to the next agent.

#### Agent 2: SignalGeneratorAgent
**Role:** Quantitative Technical Analyst
**Goal:** Dynamically apply a selected trading strategy to generate a trading signal.
**Responsibilities:**
- Receive market data from the DataCollectorAgent.
- Use the `generate_signal_tool` to apply the chosen trading strategy (e.g., '3ma', 'rsi_breakout').
- **Note:** The validation logic (e.g., checking volume, ADX, or other confirmations) is now embedded within each `TradingStrategy` class itself, not in a separate agent. The tool uses strategy objects that contain both signal generation and validation logic internally.

#### Agent 3: RiskManagerAgent
**Role:** Portfolio Risk Officer
**Goal:** Enforce position sizing and portfolio-level risk constraints.
**Responsibilities:**
- Check for maximum open positions.
- Verify the trade does not exceed the daily loss limit.
- Calculate the appropriate position size based on risk parameters.

#### Agent 4: ExecutionAgent
**Role:** Head of Trading Desk
**Goal:** Execute approved trades with precision via the Alpaca API.
**Responsibilities:**
- Receive the final, validated trade signal and position size.
- Place the market order using the `place_order` tool.
- Confirm successful execution.

---

## 3. Total LLM Call Budget per Crew Run

The removal of the `SignalValidatorAgent` and the streamlining of the signal generation process have made the LLM call budget more efficient.

| Agent             | Calls per Run |
|-------------------|---------------|
| DataCollector     | 1-2           |
| SignalGenerator   | 2-3           |
| RiskManager       | 2-3           |
| Execution         | 1-2           |
| **Total (Trading)** | **~8 Calls**    |
| **Total (Scanner)** | **~10 Calls**   |

This efficient design allows for more frequent execution cycles within the daily API limits.
