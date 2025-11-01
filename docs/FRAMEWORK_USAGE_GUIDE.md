# Framework Usage Guide

**Last Updated:** November 2024  
**Project:** AI-Driven Trading Crew  
**Stack:** CrewAI 1.3+, Google Gemini API, Alpaca Markets Python SDK

This comprehensive guide documents the correct usage patterns for all frameworks in this project, based on the latest official documentation as of November 2024.

---

## Table of Contents

1. [CrewAI Framework](#crewai-framework)
2. [Google Gemini API Integration](#google-gemini-api-integration)
3. [Alpaca Markets Python SDK](#alpaca-markets-python-sdk)
4. [Best Practices](#best-practices)
5. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## CrewAI Framework

### Version: 1.3.0+

CrewAI is a multi-agent orchestration framework that enables AI agents to work together on complex tasks.

### Key Concepts

#### 1. Agents

Agents are autonomous AI entities with specific roles, goals, and backstories.

**Correct Pattern (2024):**

```python
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Get LangChain LLM instance
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key="your_api_key",
    temperature=0.1
)

# Create agent with LangChain LLM directly
agent = Agent(
    role="Market Data Specialist",
    goal="Fetch accurate market data",
    backstory="Expert in financial data collection",
    llm=llm,  # Pass LangChain LLM directly
    verbose=True,
    allow_delegation=False
)
```

**❌ Deprecated Pattern (DO NOT USE):**

```python
# WRONG - Do not use crewai.llm.LLM wrapper
from crewai.llm import LLM

llm = LLM(llm=llm_client, model="gemini/model-name")  # ❌ Outdated
```

#### 2. Tools

Tools are functions that agents can use to perform specific actions.

**Correct Pattern (2024):**

```python
from crewai.tools import tool

@tool("Fetch Market Data")
def fetch_data_tool(symbol: str) -> dict:
    """
    Fetch historical market data for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with market data
    """
    # Implementation here
    return {"symbol": symbol, "data": [...]}
```

**Key Points:**
- Use `@tool` decorator from `crewai.tools`
- Provide clear docstring (agents use this to understand the tool)
- Type hints are important for parameter validation
- Return structured data (dict, list, or Pydantic models)

#### 3. Tasks

Tasks define what needs to be accomplished.

**Correct Pattern (2024):**

```python
from crewai import Task

task = Task(
    description="""
    Fetch historical OHLCV data for {symbol}.
    
    Requirements:
    - Timeframe: {timeframe}
    - Number of bars: {limit}
    """,
    expected_output="A DataFrame with OHLCV data and validation status",
    agent=data_collector_agent,
    context=[previous_task]  # Optional: tasks this one depends on
)
```

**Key Points:**
- Use template variables like `{symbol}` for dynamic inputs
- Clearly specify expected output format
- Use `context` parameter to chain tasks sequentially

#### 4. Crews

Crews orchestrate multiple agents and tasks.

**Correct Pattern (2024):**

```python
from crewai import Crew, Process

crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential,  # Or Process.hierarchical
    verbose=True
)

# Execute crew with inputs
result = crew.kickoff(inputs={
    "symbol": "SPY",
    "timeframe": "1Min",
    "limit": 100
})
```

**Process Types:**
- `Process.sequential`: Tasks execute one after another
- `Process.hierarchical`: Manager agent coordinates other agents

#### 5. LLM Configuration

CrewAI 1.3+ accepts LangChain LLM instances directly.

**Correct Pattern:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Create LangChain LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # No "gemini/" prefix
    google_api_key=api_key,
    temperature=0.1
)

# Pass directly to Agent
agent = Agent(
    role="Analyst",
    goal="Analyze data",
    llm=llm,  # LangChain LLM directly
    verbose=True
)
```

**Important Notes:**
- CrewAI wraps the LangChain LLM internally using LiteLLM
- Ensure `litellm` package is installed: `pip install litellm`
- Model names should NOT include provider prefix (use `gemini-2.0-flash-exp`, not `gemini/gemini-2.0-flash-exp`)

---

## Google Gemini API Integration

### Version: Google GenAI SDK 2024 + LangChain Integration

### Installation

```bash
pip install langchain-google-genai>=3.0.0
```

### Basic Usage

**Correct Pattern (2024):**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Set API key
os.environ["GOOGLE_API_KEY"] = "your_api_key"

# Create client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # Latest models: gemini-2.0-flash-exp, gemini-1.5-pro
    temperature=0.1,
    max_output_tokens=8192,
    timeout=30,
    max_retries=3
)

# Use the client
response = llm.invoke("Explain AI in simple terms")
print(response.content)
```

### Available Models (2024)

| Model Name | Context Window | Best For |
|------------|----------------|----------|
| `gemini-2.0-flash-exp` | 1M tokens | Fast responses, most use cases |
| `gemini-1.5-pro` | 2M tokens | Complex reasoning, large context |
| `gemini-1.5-flash` | 1M tokens | Balanced speed and capability |

### API Key Management

**Best Practice - Multiple Keys with Rotation:**

```python
from typing import List
import random

class GeminiKeyManager:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
    
    def get_next_key(self) -> str:
        """Rotate through keys."""
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        return key
    
    def get_client(self) -> ChatGoogleGenerativeAI:
        """Get client with rotated key."""
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.get_next_key(),
            temperature=0.1
        )
```

### Rate Limits (Free Tier)

- **RPM (Requests Per Minute):** 15
- **RPD (Requests Per Day):** 1500
- **TPM (Tokens Per Minute):** 1M tokens

**Rate Limiting Implementation:**

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, rpm: int = 15):
        self.rpm = rpm
        self.requests = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove requests older than 60 seconds
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()
        
        # Wait if at limit
        if len(self.requests) >= self.rpm:
            sleep_time = 60 - (now - self.requests[0]) + 0.5
            time.sleep(sleep_time)
        
        self.requests.append(now)
```

---

## Alpaca Markets Python SDK

### Version: alpaca-py 0.32.0+

### Installation

```bash
pip install alpaca-py>=0.32.0
```

### Trading Client

**Correct Pattern (2024):**

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Initialize client
client = TradingClient(
    api_key="your_api_key",
    secret_key="your_secret_key",
    paper=True  # Set to False for live trading
)

# Get account info
account = client.get_account()
print(f"Equity: ${float(account.equity)}")

# Place market order
order_request = MarketOrderRequest(
    symbol="SPY",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)

order = client.submit_order(order_request)
print(f"Order ID: {order.id}")
```

### Market Data Client

**Correct Pattern (2024):**

```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta

# Initialize data client
data_client = StockHistoricalDataClient(
    api_key="your_api_key",
    secret_key="your_secret_key"
)

# Request parameters
request_params = StockBarsRequest(
    symbol_or_symbols=["SPY", "AAPL"],
    timeframe=TimeFrame(1, TimeFrameUnit.Minute),
    start=datetime.now() - timedelta(days=7),
    end=datetime.now(),
    feed="iex"  # "iex" for free, "sip" for paid
)

# Fetch bars
bars = data_client.get_stock_bars(request_params)
df = bars.df  # Returns pandas DataFrame

print(df.head())
```

### TimeFrame Usage

**Available TimeFrames:**

```python
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

# Minute bars
TimeFrame(1, TimeFrameUnit.Minute)   # 1Min
TimeFrame(5, TimeFrameUnit.Minute)   # 5Min
TimeFrame(15, TimeFrameUnit.Minute)  # 15Min

# Hour bars
TimeFrame(1, TimeFrameUnit.Hour)     # 1Hour
TimeFrame(4, TimeFrameUnit.Hour)     # 4Hour

# Day bars
TimeFrame(1, TimeFrameUnit.Day)      # 1Day
```

### Data Feeds

| Feed Type | Cost | Description |
|-----------|------|-------------|
| `iex` | Free | IEX exchange data (fraction of market volume) |
| `sip` | Paid | Consolidated data from all US exchanges |

**Recommendation:** Use `iex` for development and most use cases. Switch to `sip` only if you need complete market data.

---

## Best Practices

### 1. LLM Configuration

✅ **DO:**
- Pass LangChain LLM instances directly to CrewAI agents
- Use model names without provider prefixes
- Implement key rotation for rate limit management
- Install `litellm` for CrewAI LLM support

❌ **DON'T:**
- Use deprecated `crewai.llm.LLM` wrapper
- Include provider prefixes in model names when using LangChain
- Hardcode API keys in source code

### 2. Agent Design

✅ **DO:**
- Give agents clear, specific roles and goals
- Provide detailed backstories for context
- Use focused tools (one clear purpose per tool)
- Implement proper error handling in tools

❌ **DON'T:**
- Create agents with vague or overlapping roles
- Give agents too many unrelated tools
- Allow agents to delegate unless necessary

### 3. Task Definition

✅ **DO:**
- Write clear, specific task descriptions
- Define expected output format explicitly
- Use template variables for dynamic inputs
- Chain tasks using `context` parameter

❌ **DON'T:**
- Write vague task descriptions
- Expect agents to guess output format
- Create circular task dependencies

### 4. Error Handling

✅ **DO:**
```python
try:
    result = crew.kickoff(inputs=inputs)
    return {"success": True, "result": result}
except Exception as e:
    logger.error(f"Crew execution failed: {e}", exc_info=True)
    return {"success": False, "error": str(e)}
```

❌ **DON'T:**
```python
# No error handling
result = crew.kickoff(inputs=inputs)
return result
```

### 5. API Rate Limiting

✅ **DO:**
- Implement rate limiting for all external APIs
- Use multiple API keys with rotation
- Add exponential backoff on failures
- Monitor API usage and health

❌ **DON'T:**
- Make unlimited API requests
- Ignore rate limit errors
- Use a single API key for production

---

## Common Pitfalls and Solutions

### Pitfall 1: ImportError for Google GenAI Provider

**Error:**
```
ImportError: Google Gen AI native provider not available, to install: uv add "crewai[google-genai]"
```

**Solution:**
This error occurs when using the deprecated LLM wrapper pattern. Update to use LangChain models directly:

```python
# ❌ WRONG
from crewai.llm import LLM
llm = LLM(llm=llm_client, model="gemini/model")

# ✅ CORRECT
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=key)
```

### Pitfall 2: LiteLLM Not Available

**Error:**
```
ImportError: Fallback to LiteLLM is not available
```

**Solution:**
Install litellm package:

```bash
pip install litellm>=1.0.0
```

### Pitfall 3: Invalid Model Name

**Error:**
```
Error: Model 'gemini/gemini-2.0-flash-exp' not found
```

**Solution:**
Remove the provider prefix when using LangChain:

```python
# ❌ WRONG
model="gemini/gemini-2.0-flash-exp"

# ✅ CORRECT
model="gemini-2.0-flash-exp"
```

### Pitfall 4: Alpaca TimeFrame Parsing

**Error:**
```
ValueError: Invalid timeframe format: 1Min
```

**Solution:**
Use the proper TimeFrame objects:

```python
# ❌ WRONG (string)
timeframe="1Min"

# ✅ CORRECT (TimeFrame object)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
timeframe = TimeFrame(1, TimeFrameUnit.Minute)
```

### Pitfall 5: Rate Limit Exceeded

**Error:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Solution:**
Implement proper rate limiting:

```python
class RateLimiter:
    def __init__(self, rpm: int = 15):
        self.rpm = rpm
        self.window = deque()
    
    def wait_if_needed(self):
        now = time.time()
        # Remove old requests
        while self.window and now - self.window[0] > 60:
            self.window.popleft()
        
        # Wait if at limit
        if len(self.window) >= self.rpm:
            sleep_time = 60 - (now - self.window[0]) + 1
            time.sleep(sleep_time)
        
        self.window.append(now)

# Use before each API call
rate_limiter.wait_if_needed()
```

---

## Migration Checklist

If you're updating an existing project to use the latest frameworks:

- [ ] Update `crewai` to version 1.3.0 or later
- [ ] Install `litellm` package
- [ ] Update `langchain-google-genai` to version 3.0.0 or later
- [ ] Remove all `from crewai.llm import LLM` imports
- [ ] Update agent initialization to use LangChain LLMs directly
- [ ] Remove "gemini/" prefix from model names in LangChain calls
- [ ] Update Alpaca TimeFrame usage to use proper objects
- [ ] Test all crew instantiations
- [ ] Verify rate limiting is working correctly
- [ ] Update documentation and examples

---

## Testing Your Setup

### Quick Validation Script

```python
#!/usr/bin/env python3
"""
Quick validation script for framework setup.
Run this to verify all frameworks are correctly installed and configured.
"""

def test_crewai():
    """Test CrewAI import and basic functionality."""
    from crewai import Agent, Crew, Task, Process
    print("✓ CrewAI imported successfully")

def test_gemini():
    """Test Gemini/LangChain integration."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✓ LangChain Google GenAI imported successfully")

def test_alpaca():
    """Test Alpaca SDK import."""
    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import StockHistoricalDataClient
    print("✓ Alpaca SDK imported successfully")

def test_litellm():
    """Test LiteLLM availability."""
    import litellm
    print("✓ LiteLLM available")

if __name__ == "__main__":
    print("Testing framework setup...\n")
    
    try:
        test_crewai()
        test_gemini()
        test_alpaca()
        test_litellm()
        print("\n✓ All frameworks are properly configured!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Please check your installation.")
```

---

## Additional Resources

### Official Documentation

- **CrewAI:** https://docs.crewai.com/
- **Google Gemini API:** https://ai.google.dev/gemini-api/docs
- **LangChain Google GenAI:** https://python.langchain.com/docs/integrations/chat/google_generative_ai/
- **Alpaca Python SDK:** https://alpaca.markets/sdks/python/
- **Alpaca API Docs:** https://docs.alpaca.markets/

### Community Resources

- CrewAI GitHub: https://github.com/joaomdmoura/crewAI
- Alpaca Community: https://alpaca.markets/community
- LangChain Discord: https://discord.gg/langchain

---

## Maintenance

This guide should be reviewed and updated:
- When any framework releases a major version update
- When API changes are announced
- When deprecation warnings appear
- At least once per quarter

**Last Review:** November 2024  
**Next Review Due:** February 2025

---

## Contributing

If you find outdated information or have suggestions for improvements:

1. Check the official documentation for the latest changes
2. Test your proposed changes thoroughly
3. Update this guide with clear examples
4. Document the reason for the change

---

**End of Framework Usage Guide**
