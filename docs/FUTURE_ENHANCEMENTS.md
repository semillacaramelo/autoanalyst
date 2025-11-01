# Project Enhancements

## Implemented: Data-Feed-Aware Strategy Logic

- **Status:** ✅ Implemented
- **Description:** Strategies now dynamically adapt their confirmation logic based on the quality of the configured Alpaca data feed.
- **Implementation Details:**
    - The `validate_signal` method in the `TradingStrategy` base class now accepts a `data_feed` parameter ('iex' or 'sip').
    - Strategies that rely on volume confirmation (e.g., Triple MA, MACD Crossover) apply a smaller confidence boost when using the IEX feed. This is because IEX volume only represents a fraction of the total market and is less reliable.
- **Benefit:** This feature makes the system safer and more reliable for free-tier users by reducing the weight of potentially misleading volume data. Paid users with access to the full SIP data feed can leverage its higher accuracy for more confident signal validation.

## Future Proposals

### 1. Advanced Risk Management with Dynamic Position Sizing
- **Proposal:** Implement a more sophisticated position sizing algorithm that considers market volatility (e.g., using ATR) and portfolio-level risk allocation.
- **Benefit:** Improve capital efficiency and risk-adjusted returns.

### 2. Multi-Symbol, Multi-Strategy Orchestration
- **Proposal:** Enhance the `TradingOrchestrator` to manage a portfolio of multiple symbols and strategies concurrently, with intelligent capital allocation across all active crews.
- **Benefit:** Diversify trading activities and scale the system's operational capacity.

### 3. Machine Learning-Based Signal Filtering
- **Proposal:** Add an optional ML model (e.g., a simple classifier like XGBoost or Logistic Regression) as a final confirmation layer. The model would be trained on historical data to predict the probability of a signal's success.
- **Benefit:** Potentially increase the win rate by filtering out low-probability trades.
