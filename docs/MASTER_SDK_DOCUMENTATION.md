# Master SDK Documentation

**Last Updated:** November 1, 2024  
**Purpose:** Comprehensive, up-to-date reference for all SDKs used in the AutoAnalyst project  
**SDKs Covered:** CrewAI 1.3+, Google Gemini API, Alpaca Markets Python SDK

This document consolidates the latest API documentation to prevent regressions due to outdated AI context.

---

## Table of Contents

1. [Google Gemini API](#google-gemini-api)
2. [CrewAI Framework](#crewai-framework)
3. [Alpaca Markets Python SDK](#alpaca-markets-python-sdk)
4. [Integration Patterns](#integration-patterns)

---

## Google Gemini API

### Version: Google GenAI SDK 1.47+ (November 2024)

### Installation

```bash
pip install google-genai>=1.0.0
```

### Available Models (Free Tier)

| Model | RPM | RPD | TPM | Context | Best For |
|-------|-----|-----|-----|---------|----------|
| **gemini-2.5-flash** | 10 | 250 | 250K | 1M | High-volume, fast responses (PREFERRED) |
| **gemini-2.5-pro** | 2 | 50 | 125K | 1M | Complex reasoning (FALLBACK) |
| gemini-2.5-flash-lite | 10 | 250 | 250K | 1M | Cost-optimized throughput |
| gemini-2.0-flash | 10 | 250 | 250K | 1M | Previous generation |

**Key Points:**
- **Flash is preferred** for free tier due to higher quota (10 RPM vs 2 RPM)
- Use Pro as fallback when Flash quota exhausted
- Real-world Pro quota often ~10-15 requests before rate limiting
- Quotas are per API key

**Source:** https://ai.google.dev/gemini-api/docs/rate-limits

### Dynamic Model Discovery

Query available models programmatically:

```python
from google import genai

client = genai.Client(api_key="your_key")
models = list(client.models.list())

for model in models:
    print(f"{model.name}: {model.display_name}")
    print(f"  Supports: {model.supported_generation_methods}")
```

**API Endpoint:**  
`GET https://generativelanguage.googleapis.com/v1beta/models`

Response includes:
- Model name (e.g., `models/gemini-2.5-flash`)
- Supported methods (`generateContent`, `embedContent`)
- Context window size
- Version info (stable, preview, experimental)

**Source:** https://ai.google.dev/api/models

### Rate Limit Handling

Free tier limits are enforced:
- **429 RESOURCE_EXHAUSTED** error when limit hit
- Must wait for window to reset or switch keys
- Recommend tracking usage client-side to avoid hitting limits

```python
# Example error handling
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="hello"
    )
except Exception as e:
    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        # Switch to different key or model
        pass
```

### Text Generation

```python
from google import genai

client = genai.Client(api_key="your_key")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain AI in simple terms"
)

print(response.text)
```

**Configuration Options:**
- `temperature`: 0.0-2.0 (default: 1.0)
- `top_p`, `top_k`: Nucleus/top-k sampling
- `max_output_tokens`: Limit response length
- `stop_sequences`: Custom stop tokens

**Source:** https://ai.google.dev/gemini-api/docs/text-generation

### Structured Output

Force JSON schema compliance:

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Generate a person profile",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={"type": "object", "properties": {...}}
    )
)
```

**Source:** https://ai.google.dev/gemini-api/docs/structured-output

### Google Search Grounding

Enable web search grounding (500 requests/day free):

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Latest AI news",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
)
```

**Source:** https://ai.google.dev/gemini-api/docs/google-search

### Best Practices for Free Tier

1. **Prefer Flash over Pro**: 5x higher quota
2. **Use multiple API keys**: Rotate when quota exhausted
3. **Track usage client-side**: Avoid hitting rate limits
4. **Cache responses**: Reduce redundant API calls
5. **Implement exponential backoff**: On 429 errors
6. **Monitor quota daily**: Flash: 250/day, Pro: 50/day per key

---

## CrewAI Framework

### Version: 1.3.0+ (November 2024)

### Installation

```bash
pip install "crewai[tools,google-genai]>=1.3.0"
```

**Note:** The `[google-genai]` extra enables native Gemini support.

### Core Concepts

#### 1. LLM Configuration

**Correct Pattern (2024):**

```python
from crewai import LLM
import os

# Use CrewAI's LLM class with Gemini
llm = LLM(
    model="gemini/gemini-2.5-flash",  # Include "gemini/" prefix
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1
)
```

**Key Points:**
- Import `LLM` directly from `crewai` (NOT `crewai.llm`)
- Model string must include `"gemini/"` prefix
- Install with `[google-genai]` extra
- CrewAI handles underlying API integration

**Source:** https://docs.crewai.com/en/concepts/llms#google-gemini-api

#### 2. Agents

Agents are autonomous AI units with roles, goals, and tools.

```python
from crewai import Agent, LLM

llm = LLM(model="gemini/gemini-2.5-flash", api_key=api_key)

agent = Agent(
    role="Senior Data Analyst",
    goal="Extract insights from complex datasets",
    backstory="Expert in statistical analysis with 10+ years experience",
    llm=llm,
    tools=[data_analysis_tool, visualization_tool],
    verbose=True,
    allow_delegation=False,
    max_iter=15,
    max_execution_time=300  # seconds
)
```

**Agent Attributes:**
- `role`: Agent's function/expertise
- `goal`: What the agent aims to achieve
- `backstory`: Context and personality
- `tools`: List of callable functions
- `llm`: Language model instance
- `allow_delegation`: Can assign tasks to other agents
- `max_iter`: Maximum iterations per task
- `verbose`: Enable debug logging

**Source:** https://docs.crewai.com/en/concepts/agents

#### 3. Tasks

Tasks are specific assignments for agents.

```python
from crewai import Task

task = Task(
    description="""
    Analyze the trading data for {symbol}.
    
    Requirements:
    - Calculate key technical indicators
    - Identify trends
    - Generate trading signals
    
    Context: Market is volatile today.
    """,
    expected_output="A JSON object with analysis results and signals",
    agent=analyst_agent,
    context=[previous_task],  # Use outputs from these tasks
    output_json=AnalysisResult,  # Pydantic model
    human_input=False,
    async_execution=False
)
```

**Task Attributes:**
- `description`: Detailed instructions (supports templates with `{variable}`)
- `expected_output`: Format and content specification
- `agent`: Responsible agent
- `context`: List of tasks whose outputs are inputs to this task
- `output_json`: Enforce Pydantic model output
- `output_file`: Save output to file
- `callback`: Function to call after completion

**Source:** https://docs.crewai.com/en/concepts/tasks

#### 4. Tools

Tools extend agent capabilities.

```python
from crewai.tools import tool

@tool("Calculate RSI")
def calculate_rsi(prices: list, period: int = 14) -> float:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
        
    Returns:
        RSI value between 0 and 100
    """
    # Implementation
    return rsi_value
```

**Tool Requirements:**
- Use `@tool` decorator
- Clear, detailed docstring (agents read this)
- Type hints for parameters
- Descriptive function name
- Return structured data

**Built-in Tools:**
```bash
pip install 'crewai[tools]'
```

Available: `SerperDevTool` (web search), `FileReadTool`, `DirectoryReadTool`, `WebsiteSearchTool`, etc.

**Source:** https://docs.crewai.com/en/concepts/tools

#### 5. Crews

Crews orchestrate agents and tasks.

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # or Process.hierarchical
    verbose=True,
    max_rpm=10,  # Rate limit for API calls
    memory=True,  # Enable crew memory
    cache=True  # Cache LLM responses
)

# Execute with inputs
result = crew.kickoff(inputs={
    "symbol": "SPY",
    "timeframe": "1D"
})
```

**Process Types:**
- `Process.sequential`: Tasks execute in order
- `Process.hierarchical`: Manager agent delegates

**Crew Attributes:**
- `agents`: List of agent instances
- `tasks`: List of task instances
- `process`: Execution strategy
- `verbose`: Debug output
- `max_rpm`: API rate limiting
- `memory`: Enable persistent memory
- `cache`: Cache LLM calls

**Source:** https://docs.crewai.com/en/concepts/crews

### Best Practices

1. **80/20 Rule**: Spend 80% effort on clear task descriptions, 20% on agent config
2. **Specific Goals**: Clear, measurable objectives for each agent
3. **Tool Selection**: Give agents only tools they need
4. **Error Handling**: Always wrap `crew.kickoff()` in try/except
5. **Rate Limiting**: Set `max_rpm` to stay under API limits
6. **Testing**: Test individual agents before full crew

**Source:** https://docs.crewai.com/en/guides/agents/crafting-effective-agents

---

## Alpaca Markets Python SDK

### Version: alpaca-py 0.43+ (November 2024)

### Installation

```bash
pip install alpaca-py>=0.32.0
```

**Note:** `alpaca-py` is the current SDK. The old `alpaca-trade-api` is deprecated.

### Trading Client

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Initialize
client = TradingClient(
    api_key="your_key",
    secret_key="your_secret",
    paper=True  # Use paper trading (free forever)
)

# Get account
account = client.get_account()
print(f"Buying power: ${float(account.buying_power)}")

# Place order
order_req = MarketOrderRequest(
    symbol="SPY",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)

order = client.submit_order(order_req)
print(f"Order ID: {order.id}")

# Get positions
positions = client.get_all_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price}")
```

**Key Classes:**
- `TradingClient`: Main trading interface
- `MarketOrderRequest`: Market order
- `LimitOrderRequest`: Limit order
- `StopOrderRequest`: Stop order
- `OrderSide`: BUY or SELL
- `TimeInForce`: DAY, GTC, IOC, FOK

**Source:** https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html

### Market Data Client

```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta

# Initialize
data_client = StockHistoricalDataClient(
    api_key="your_key",
    secret_key="your_secret"
)

# Get latest quote
quote_req = StockLatestQuoteRequest(symbol_or_symbols=["SPY", "AAPL"])
quotes = data_client.get_stock_latest_quote(quote_req)
print(f"SPY Ask: ${quotes['SPY'].ask_price}")

# Get historical bars
bars_req = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(1, TimeFrameUnit.Minute),
    start=datetime.now() - timedelta(days=7),
    end=datetime.now(),
    feed="iex"  # Free IEX data
)

bars = data_client.get_stock_bars(bars_req)
df = bars.df  # Returns pandas DataFrame

print(df.head())
```

**TimeFrame Options:**
```python
TimeFrame(1, TimeFrameUnit.Minute)   # 1Min
TimeFrame(5, TimeFrameUnit.Minute)   # 5Min
TimeFrame(15, TimeFrameUnit.Minute)  # 15Min
TimeFrame(1, TimeFrameUnit.Hour)     # 1Hour
TimeFrame(1, TimeFrameUnit.Day)      # 1Day
TimeFrame(1, TimeFrameUnit.Week)     # 1Week
TimeFrame(1, TimeFrameUnit.Month)    # 1Month
```

**Data Feeds:**
- `"iex"`: Free IEX exchange data (default)
- `"sip"`: Paid consolidated data from all US exchanges

**Source:** https://alpaca.markets/sdks/python/market_data.html

### Crypto Data

```python
from alpaca.data.historical import CryptoHistoricalDataClient

# No API keys needed for public crypto data
crypto_client = CryptoHistoricalDataClient()

# Or with keys for higher limits
crypto_client = CryptoHistoricalDataClient(
    api_key="your_key",
    secret_key="your_secret"
)
```

**Source:** https://docs.alpaca.markets/docs/getting-started-with-alpaca-market-data

### Websocket Streaming

```python
from alpaca.data.live import StockDataStream

stream = StockDataStream(api_key, secret_key)

@stream.on_bar("SPY")
async def on_bar(bar):
    print(f"SPY: ${bar.close} at {bar.timestamp}")

stream.run()
```

**Source:** https://alpaca.markets/sdks/python/market_data_stream.html

---

## Integration Patterns

### Pattern 1: Dynamic Gemini Model Selection

```python
from google import genai

def get_best_model(api_keys: list) -> tuple:
    """Get best available Gemini model and key based on quota."""
    for api_key in api_keys:
        # Try Flash first (higher quota)
        if can_use_flash(api_key):
            return ("gemini-2.5-flash", api_key)
        
        # Fallback to Pro
        if can_use_pro(api_key):
            return ("gemini-2.5-pro", api_key)
    
    raise RuntimeError("All keys exhausted")
```

### Pattern 2: CrewAI with Dynamic Model

```python
from crewai import Agent, Crew, Task, LLM

# Get best model dynamically
model_name, api_key = get_best_model(api_keys)

# Create LLM
llm = LLM(
    model=f"gemini/{model_name}",
    api_key=api_key
)

# Use in agents
agent = Agent(role="Analyst", goal="Analyze data", llm=llm)
```

### Pattern 3: Multi-Key Rotation

```python
class KeyRotator:
    def __init__(self, keys: list):
        self.keys = keys
        self.current = 0
        self.quota_tracker = {}  # Track usage per key
    
    def get_next_key(self) -> str:
        """Get next available key with quota."""
        for _ in range(len(self.keys)):
            key = self.keys[self.current]
            self.current = (self.current + 1) % len(self.keys)
            
            if self.has_quota(key):
                return key
        
        raise RuntimeError("All keys exhausted")
```

### Pattern 4: Alpaca with Error Handling

```python
from alpaca.trading.client import TradingClient
from alpaca.common.exceptions import APIError

def place_order_safe(client, symbol, qty, side):
    """Place order with retry logic."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            order_req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            return client.submit_order(order_req)
        
        except APIError as e:
            if "insufficient" in str(e).lower():
                raise  # Don't retry insufficient funds
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## Quick Reference

### Gemini API

- **Models API:** https://ai.google.dev/api/models
- **Rate Limits:** https://ai.google.dev/gemini-api/docs/rate-limits
- **Text Generation:** https://ai.google.dev/gemini-api/docs/text-generation
- **Structured Output:** https://ai.google.dev/gemini-api/docs/structured-output
- **Google Search:** https://ai.google.dev/gemini-api/docs/google-search

### CrewAI

- **Main Docs:** https://docs.crewai.com/
- **Agents:** https://docs.crewai.com/en/concepts/agents
- **Tasks:** https://docs.crewai.com/en/concepts/tasks
- **Tools:** https://docs.crewai.com/en/concepts/tools
- **LLMs:** https://docs.crewai.com/en/concepts/llms
- **Changelog:** https://docs.crewai.com/en/changelog

### Alpaca Markets

- **SDK Home:** https://alpaca.markets/sdks/python/
- **Getting Started:** https://alpaca.markets/sdks/python/getting_started.html
- **Trading API:** https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html
- **Market Data:** https://alpaca.markets/sdks/python/market_data.html
- **API Reference:** https://docs.alpaca.markets/reference

---

## Maintenance Schedule

This document should be reviewed and updated:
- **Monthly:** Check for new Gemini models and quota changes
- **Quarterly:** Review CrewAI and Alpaca SDK updates
- **On Breaking Changes:** Immediate update when APIs change
- **Before Major Releases:** Full verification of all patterns

**Last Full Review:** November 1, 2024  
**Next Review Due:** December 1, 2024

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2024-11-01 | 1.0 | Initial comprehensive documentation |

---

**End of Master SDK Documentation**
