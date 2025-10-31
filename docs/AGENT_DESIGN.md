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

### 2.2. Trading Crew (Simplified)
This crew executes a single trade for a given symbol and strategy. The `SignalValidatorAgent` has been removed, and its logic is now integrated into the `SignalGeneratorAgent` and the strategy classes themselves.

```
┌─────────────────────────────────────────┐
│   1. DataCollectorAgent                 │
│   Fetches OHLCV data                    │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   2. SignalGeneratorAgent               │
│   Applies a selected strategy to data   │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   3. RiskManagerAgent                   │
│   Portfolio-level risk checks           │
└──────────────┬──────────────────────────┘
			   │
			   ▼
┌─────────────────────────────────────────┐
│   4. ExecutionAgent                     │
│   Places orders via Alpaca             │
└─────────────────────────────────────────┘
```

### Agent Specifications (Trading Crew)

#### Agent 1: DataCollectorAgent
**Role:** Market Data Specialist  
**Goal:** Fetch accurate, complete OHLCV data for analysis.

#### Agent 2: SignalGeneratorAgent
**Role:** Quantitative Technical Analyst  
**Goal:** Dynamically apply a selected trading strategy to generate and validate a trading signal.
**Note:** This agent now uses the `generate_signal_tool(strategy_name)` to perform both signal generation and validation in one step, making the process more efficient.

#### Agent 3: RiskManagerAgent
**Role:** Portfolio Risk Officer  
**Goal:** Enforce position sizing and portfolio-level risk constraints.

#### Agent 4: ExecutionAgent
**Role:** Head of Trading Desk  
**Goal:** Execute approved trades with precision.

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
