# CrewAI Framework Reference Documentation

**Version:** 1.0  
**Date:** November 4, 2025  
**Purpose:** Authoritative reference for CrewAI architecture, patterns, and limitations discovered during AutoAnalyst development

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Concept: LLM-First Design](#core-concept-llm-first-design)
3. [Tool Communication Architecture](#tool-communication-architecture)
4. [Data Sharing Patterns](#data-sharing-patterns)
5. [Memory System](#memory-system)
6. [Knowledge System](#knowledge-system)
7. [Task Context and Dependencies](#task-context-and-dependencies)
8. [Common Pitfalls and Anti-Patterns](#common-pitfalls-and-anti-patterns)
9. [Correct Implementation Examples](#correct-implementation-examples)
10. [Migration Strategies](#migration-strategies)

---

## Architecture Overview

### What is CrewAI?

CrewAI is a **multi-agent orchestration framework** designed around **LLM-first principles**. Unlike traditional Python applications where functions pass objects directly, CrewAI coordinates agents through **natural language** and **JSON-serializable data**.

**Key Characteristics:**
- **Agent-based**: Each agent has a role, goal, backstory, and set of tools
- **Task-driven**: Work is decomposed into discrete tasks with clear descriptions and expected outputs
- **LLM-mediated**: All inter-agent communication goes through the LLM's understanding
- **JSON-serializable**: Tool parameters and outputs must be serializable to JSON

---

## Core Concept: LLM-First Design

### Traditional Python Application vs CrewAI

#### Traditional Python (Direct Object Passing)
```python
# Traditional approach - direct object passing
def fetch_data() -> pd.DataFrame:
    return pd.DataFrame({...})

def analyze_data(df: pd.DataFrame) -> dict:
    return {"mean": df.mean(), "std": df.std()}

# Direct passing works fine
data = fetch_data()
results = analyze_data(data)  # DataFrame passed directly
```

#### CrewAI Approach (LLM-Mediated Communication)
```python
# CrewAI approach - LLM-mediated communication
@tool
def fetch_data() -> dict:
    df = pd.DataFrame({...})
    return df.to_dict()  # MUST serialize to JSON

@tool
def analyze_data(data: dict) -> dict:
    df = pd.DataFrame(data)  # Reconstruct from JSON
    return {"mean": float(df.mean()), "std": float(df.std())}

# CrewAI flow:
# 1. Agent calls fetch_data() → Returns dict to agent context
# 2. LLM processes context → Decides to call analyze_data()
# 3. LLM serializes parameters → JSON string
# 4. analyze_data receives JSON-compatible dict
```

### Why This Matters

**The Fundamental Rule:** All data passed between agents and tools MUST be JSON-serializable.

**What Works:**
- ✅ `str`, `int`, `float`, `bool`
- ✅ `list`, `dict` (with JSON-compatible values)
- ✅ Pydantic models (with `model_dump()`)
- ✅ Simple data structures

**What DOES NOT Work:**
- ❌ `pd.DataFrame` objects
- ❌ `np.ndarray` objects
- ❌ File handles
- ❌ Database connections
- ❌ Any complex Python object that can't be JSON-serialized

---

## Tool Communication Architecture

### How Tools Are Actually Called

#### The Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Tool Returns Data                                            │
│    @tool                                                         │
│    def fetch_data() -> Dict[str, pd.DataFrame]:                 │
│        return {"BTC": DataFrame(...)}                           │
│                                                                  │
│    ↓ Returns to Agent Context                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. LLM Processes Context                                        │
│    - Agent receives: {"BTC": <DataFrame object>}                │
│    - LLM sees: String representation of DataFrame               │
│    - Example: "BTC: open high low close..."                     │
│                                                                  │
│    ↓ LLM decides next action                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. CrewAI Serializes Parameters (THE CRITICAL STEP)             │
│    - LLM wants to call: analyze_volatility(data)                │
│    - CrewAI serializes all parameters to JSON                   │
│    - DataFrame → String representation (UNPARSEABLE!)           │
│    - Result: "open high low close\ntimestamp ..."               │
│                                                                  │
│    ↓ Serialized parameters sent to tool                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 4. Tool Receives Serialized Data                                │
│    @tool                                                         │
│    def analyze_volatility(data: Dict[str, pd.DataFrame]):       │
│        # data = {"BTC": "open high low close..."}  (STRING!)    │
│        df = data["BTC"]  # This is a STRING, not DataFrame!     │
│        high = df['high']  # ERROR: string indices must be int   │
│                                                                  │
│    ↓ TypeError: cannot process string as DataFrame              │
└─────────────────────────────────────────────────────────────────┘
```

### Why DataFrame Passing Fails

**The Problem:** DataFrames serialize to unparseable string representations:
```python
# What the LLM sees:
"BTC/USD": "open        high        low       close     volume  trade_count       vwap
timestamp                                                                    
2025-10-31 03:00:00+00:00  184.7100  185.960000  184.5000  185.240  1160.315         21.0  185.050965
2025-10-31 04:00:00+00:00  185.2400  187.020000  185.1500  186.973   785.402         17.0  186.374529"

# This is NOT JSON
# This is NOT parseable back to DataFrame
# This is NOT what your tool expects
```

**Attempted Solutions That Don't Work:**
1. ❌ String detection and parsing → Format varies, unreliable
2. ❌ Dict-to-DataFrame conversion → LLM sends strings, not dicts
3. ❌ Custom serialization → LLM controls serialization, not your code
4. ❌ Bypassing LLM → Goes against CrewAI architecture

---

## Data Sharing Patterns

### Pattern 1: Knowledge Sources (Recommended for Static Data)

**Use Case:** Preload reference data that agents query during task execution

**How It Works:**
- Data is loaded into ChromaDB vector store during crew initialization
- Agents query knowledge sources by symbol/identifier (strings only)
- CrewAI handles retrieval and injects context into agent prompts

**Example:**
```python
from crewai import Crew, Agent, Task
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

class MarketDataKnowledgeSource(BaseKnowledgeSource):
    """Store OHLCV data in knowledge base."""
    
    def load_content(self) -> Dict[str, str]:
        """Fetch and format market data as text."""
        data = fetch_market_data()  # Returns DataFrames
        
        # Convert DataFrames to searchable text format
        formatted = {}
        for symbol, df in data.items():
            # Store as markdown table or CSV format
            formatted[symbol] = df.to_markdown()
        
        return formatted
    
    def add(self) -> None:
        """Process and store in knowledge base."""
        content = self.load_content()
        for symbol, text in content.items():
            chunks = self._chunk_text(text)
            self.chunks.extend(chunks)
        self._save_documents()

# Create knowledge source
market_knowledge = MarketDataKnowledgeSource()

# Agents query by symbol name (string)
analyst = Agent(
    role="Market Analyst",
    goal="Analyze volatility",
    backstory="Expert in market analysis",
    knowledge_sources=[market_knowledge]
)

# Tasks receive text context, not DataFrames
task = Task(
    description="Analyze volatility for BTC/USD",  # Agent queries knowledge by symbol
    expected_output="Volatility analysis report",
    agent=analyst
)

crew = Crew(
    agents=[analyst],
    tasks=[task],
    knowledge_sources=[market_knowledge]
)
```

**Pros:**
- ✅ RAG-based retrieval (semantic search)
- ✅ Works with large datasets
- ✅ Persistent across runs
- ✅ No serialization issues

**Cons:**
- ⚠️ Text-based only (loses DataFrame structure)
- ⚠️ Requires text formatting/parsing
- ⚠️ Query latency (database lookup)

---

### Pattern 2: Shared Memory (For Session State)

**Use Case:** Share execution context and results across agents in single run

**How It Works:**
- Crew-level memory stores task outputs
- Agents access memory during execution
- Memory persists across tasks but not across crew runs (by default)

**Example:**
```python
from crewai import Crew, Agent, Task

# Enable crew-level memory
crew = Crew(
    agents=[data_collector, analyst],
    tasks=[fetch_task, analysis_task],
    memory=True,  # Enables short-term, long-term, entity memory
    verbose=True
)

# Task 1: Store data identifiers in memory
fetch_task = Task(
    description="Fetch BTC, ETH, SOL data and store symbol list",
    expected_output="List of symbols fetched",
    agent=data_collector
)

# Task 2: Agent retrieves symbol list from memory context
analysis_task = Task(
    description="Analyze volatility for symbols from previous task",
    expected_output="Volatility report",
    agent=analyst,
    context=[fetch_task]  # Receives task output as text context
)
```

**Pros:**
- ✅ Built-in with CrewAI
- ✅ Automatic context passing between tasks
- ✅ No setup required

**Cons:**
- ⚠️ Text-based context (no structured data)
- ⚠️ Limited to task outputs (strings)
- ⚠️ No direct DataFrame access

---

### Pattern 3: Independent Tool Fetching (Simplest)

**Use Case:** Each tool fetches its own data independently

**How It Works:**
- Tools accept simple parameters (symbol names, dates)
- Tools fetch and process DataFrames internally
- Tools return JSON-serializable results

**Example:**
```python
from crewai_tools import tool
import pandas as pd

@tool("Analyze Volatility")
def analyze_volatility(symbols: list[str], timeframe: str = "1Hour") -> dict:
    """
    Analyze volatility for given symbols.
    
    Args:
        symbols: List of symbol names (e.g., ["BTC/USD", "ETH/USD"])
        timeframe: Timeframe for analysis (e.g., "1Hour", "1Day")
    
    Returns:
        dict: Volatility metrics for each symbol
    """
    results = {}
    
    for symbol in symbols:
        # Fetch data internally (not passed from another tool)
        df = fetch_market_data(symbol, timeframe)  # Returns DataFrame
        
        # Calculate metrics from DataFrame
        atr = calculate_atr(df)
        volatility_score = (atr / df['close'].mean()) * 100
        
        # Return JSON-serializable result
        results[symbol] = {
            "atr": float(atr),
            "volatility_score": float(volatility_score),
            "timestamp": df.index[-1].isoformat()
        }
    
    return results  # Dict of dicts - fully JSON-serializable

# Agent calls tool with simple string parameters
analyst = Agent(
    role="Volatility Analyst",
    goal="Find high-volatility assets",
    backstory="Expert in volatility analysis",
    tools=[analyze_volatility]  # Tool handles data fetching internally
)

task = Task(
    description="Analyze volatility for BTC/USD and ETH/USD",
    expected_output="Volatility comparison",
    agent=analyst
)
```

**Pros:**
- ✅ Simplest implementation
- ✅ No serialization issues
- ✅ Self-contained tools
- ✅ Easy to test

**Cons:**
- ⚠️ Duplicate data fetching (less efficient)
- ⚠️ No data reuse between tools
- ⚠️ Higher API call volume

---

### Pattern 4: CrewAI Flows (For Complex Pipelines)

**Use Case:** Data-intensive workflows with Python-level control

**How It Works:**
- Flows handle data pipeline in pure Python
- Crews handle analysis/decision-making
- DataFrames live in Flow code, not passed through tools

**Example:**
```python
from crewai.flow.flow import Flow, listen, start
import pandas as pd

class MarketAnalysisFlow(Flow):
    """Flow handles data fetching, crews handle analysis."""
    
    @start()
    def fetch_market_data(self) -> dict:
        """Fetch data in Python (DataFrames OK here)."""
        symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]
        data = {}
        
        for symbol in symbols:
            df = fetch_ohlcv(symbol, timeframe="1Hour", limit=100)
            data[symbol] = df  # DataFrames live in Flow state
        
        return data
    
    @listen(fetch_market_data)
    def calculate_metrics(self, data: dict) -> dict:
        """Calculate metrics in Python (DataFrames OK here)."""
        metrics = {}
        
        for symbol, df in data.items():
            atr = calculate_atr(df)
            rsi = calculate_rsi(df)
            
            metrics[symbol] = {
                "atr": float(atr),
                "rsi": float(rsi),
                "price": float(df['close'].iloc[-1])
            }
        
        return metrics  # JSON-serializable dict
    
    @listen(calculate_metrics)
    def analyze_with_crew(self, metrics: dict) -> str:
        """Use crew for analysis (no DataFrames passed)."""
        # Create crew with metrics as input
        analyst = Agent(
            role="Market Analyst",
            goal="Identify trading opportunities",
            backstory="Expert trader"
        )
        
        task = Task(
            description=f"Analyze these metrics and recommend trades: {metrics}",
            expected_output="Trading recommendations",
            agent=analyst
        )
        
        crew = Crew(agents=[analyst], tasks=[task])
        result = crew.kickoff(inputs={"metrics": metrics})
        
        return result.raw

# Run flow
flow = MarketAnalysisFlow()
result = flow.kickoff()
```

**Pros:**
- ✅ Best of both worlds (Python + AI)
- ✅ Full DataFrame support in Flow code
- ✅ Crews handle analysis, not data processing
- ✅ Efficient data pipelines

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Requires Flow framework knowledge
- ⚠️ Less agent autonomy

---

## Memory System

### How Memory Works in CrewAI

**Memory Components:**
1. **Short-Term Memory**: RAG-based, current execution context
2. **Long-Term Memory**: SQLite storage, persists across runs
3. **Entity Memory**: Tracks people, places, concepts
4. **Contextual Memory**: Combines all memory types

**Storage Locations (Linux):**
```
~/.local/share/CrewAI/{project_name}/
├── short_term_memory/   # ChromaDB for current session
├── long_term_memory/    # ChromaDB for historical data
├── entities/            # ChromaDB for entity tracking
└── long_term_memory_storage.db  # SQLite database
```

### Memory Configuration

**Basic Setup:**
```python
from crewai import Crew

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    memory=True,  # Enables all memory types
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
)
```

**Agent-Level Memory:**
```python
agent = Agent(
    role="Analyst",
    goal="Analyze data",
    backstory="Expert analyst",
    memory=True,  # Agent has its own memory
    knowledge_sources=[...]  # Optional agent-specific knowledge
)
```

### Memory Events

**Available Events:**
- `MemoryQueryStartedEvent`
- `MemoryQueryCompletedEvent`
- `MemorySaveStartedEvent`
- `MemorySaveCompletedEvent`
- `MemoryRetrievalCompletedEvent`

**Example Monitoring:**
```python
from crewai.events import BaseEventListener, MemoryQueryCompletedEvent

class MemoryMonitor(BaseEventListener):
    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(MemoryQueryCompletedEvent)
        def on_query(source, event):
            print(f"Query: {event.query}")
            print(f"Results: {len(event.results)}")
            print(f"Time: {event.query_time_ms}ms")

monitor = MemoryMonitor()
```

---

## Knowledge System

### How Knowledge Works in CrewAI

**Knowledge vs Memory:**
- **Knowledge**: Static reference data (documents, manuals, datasets)
- **Memory**: Dynamic execution state (task outputs, agent interactions)

**Knowledge Storage:**
- ChromaDB vector database
- Same location as memory
- Separate collections per agent/crew

**Data Flow:**
```
┌─────────────────────────────────────────────────────────┐
│ 1. Load Knowledge Source                                │
│    - Reads files/data                                   │
│    - Converts to text chunks                            │
│    - Stores in ChromaDB                                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Agent Executes Task                                  │
│    - Task description mentions "BTC/USD"                │
│    - CrewAI rewrites query: "Bitcoin price data"        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Query Knowledge Base                                 │
│    - Semantic search in ChromaDB                        │
│    - Retrieves relevant text chunks                     │
│    - Injects into agent prompt as context              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Agent Processes Context                              │
│    - LLM reads knowledge context                        │
│    - Generates response based on knowledge              │
│    - Returns text output                                │
└─────────────────────────────────────────────────────────┘
```

### Creating Custom Knowledge Sources

**Example: Market Data Knowledge Source**
```python
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from pydantic import BaseModel, Field
import pandas as pd

class MarketDataKnowledgeSource(BaseKnowledgeSource):
    """Store market data as searchable text."""
    
    symbols: list[str] = Field(description="List of symbols to load")
    timeframe: str = Field(default="1Hour", description="Data timeframe")
    
    def load_content(self) -> dict[str, str]:
        """Fetch and format market data."""
        content = {}
        
        for symbol in self.symbols:
            df = fetch_ohlcv(symbol, self.timeframe, limit=100)
            
            # Format as markdown table for better LLM understanding
            content[symbol] = f"""
# {symbol} Market Data ({self.timeframe})

## Recent Prices
{df[['open', 'high', 'low', 'close', 'volume']].tail(10).to_markdown()}

## Statistics
- Current Price: ${df['close'].iloc[-1]:.2f}
- 24h High: ${df['high'].tail(24).max():.2f}
- 24h Low: ${df['low'].tail(24).min():.2f}
- 24h Volume: {df['volume'].tail(24).sum():.0f}
"""
        
        return content
    
    def add(self) -> None:
        """Process and store in knowledge base."""
        content = self.load_content()
        for symbol, text in content.items():
            chunks = self._chunk_text(text)
            self.chunks.extend(chunks)
        self._save_documents()

# Usage
market_knowledge = MarketDataKnowledgeSource(
    symbols=["BTC/USD", "ETH/USD", "SOL/USD"],
    timeframe="1Hour"
)

crew = Crew(
    agents=[analyst],
    tasks=[analysis_task],
    knowledge_sources=[market_knowledge]
)
```

### Query Rewriting

**Automatic Query Optimization:**
```python
# Original task prompt:
"Analyze BTC/USD and format the output as JSON with headers"

# CrewAI rewrites to:
"Bitcoin USD analysis data"

# Benefits:
# - Removes formatting instructions
# - Focuses on core information need
# - Better semantic search results
```

---

## Task Context and Dependencies

### How Task Context Works

**Context Passing:**
```python
# Task 1: Fetches data and returns text
research_task = Task(
    description="Fetch BTC/USD data for last 100 hours",
    expected_output="Data summary with key metrics",
    agent=data_agent
)

# Task 2: Receives Task 1 output as TEXT CONTEXT
analysis_task = Task(
    description="Analyze the data from previous task",
    expected_output="Analysis report",
    agent=analyst_agent,
    context=[research_task]  # TEXT output, not DataFrame!
)
```

**What Gets Passed:**
- ✅ Task output as string (from `task.output.raw`)
- ✅ Task description
- ✅ Task metadata
- ❌ NOT the original DataFrame
- ❌ NOT Python objects

**Best Practice:**
```python
# Task 1: Return structured text that Task 2 can parse
research_task = Task(
    description="Fetch BTC/USD data",
    expected_output="""
    JSON format with structure:
    {
        "symbol": "BTC/USD",
        "current_price": 45000.00,
        "24h_volume": 1000000,
        "metrics": {"atr": 500, "rsi": 65}
    }
    """,
    agent=data_agent,
    output_json=MarketData  # Use Pydantic model
)

# Task 2: Parse JSON from context
analysis_task = Task(
    description="Parse the JSON data and create analysis",
    expected_output="Analysis report",
    agent=analyst_agent,
    context=[research_task]
)
```

---

## Common Pitfalls and Anti-Patterns

### ❌ Anti-Pattern 1: Passing DataFrames Between Tools

**Wrong:**
```python
@tool("Fetch Data")
def fetch_data() -> Dict[str, pd.DataFrame]:
    return {"BTC": pd.DataFrame({...})}  # DON'T DO THIS

@tool("Analyze Data")
def analyze(data: Dict[str, pd.DataFrame]) -> dict:
    df = data["BTC"]  # Will receive STRING, not DataFrame!
    return {"mean": df.mean()}  # ERROR: string has no mean()
```

**Why It Fails:**
- CrewAI serializes DataFrame to unparseable string
- Tool receives `"BTC": "open high low close..."` (string)
- Cannot reconstruct DataFrame from this format

**Fix:** Use independent fetching pattern (Pattern 3)

---

### ❌ Anti-Pattern 2: Storing Complex Objects in Agent State

**Wrong:**
```python
class DataCollectorAgent:
    def __init__(self):
        self.dataframes = {}  # Storing DataFrames in agent
    
    def fetch_data(self, symbol: str):
        self.dataframes[symbol] = fetch_ohlcv(symbol)
        return f"Fetched {symbol}"
```

**Why It Fails:**
- Agents don't maintain stateful object stores
- Tools are called by LLM, not agent class
- No way to access agent.dataframes from tools

**Fix:** Use knowledge sources or flows

---

### ❌ Anti-Pattern 3: Relying on Tool Call Order

**Wrong:**
```python
# Assuming Tool B will be called after Tool A
@tool("Tool A")
def tool_a() -> str:
    global cached_data  # Bad: global state
    cached_data = fetch_data()
    return "Data cached"

@tool("Tool B")
def tool_b() -> dict:
    return analyze(cached_data)  # Fragile: depends on call order
```

**Why It Fails:**
- LLM controls tool call order
- No guarantee Tool A runs before Tool B
- Global state is unreliable in async execution

**Fix:** Make tools self-contained (Pattern 3)

---

### ❌ Anti-Pattern 4: Assuming Task Context is Structured Data

**Wrong:**
```python
fetch_task = Task(
    description="Fetch BTC data",
    expected_output="DataFrame with OHLCV data",
    agent=data_agent
)

analysis_task = Task(
    description="Calculate mean from previous task",
    expected_output="Mean price",
    agent=analyst,
    context=[fetch_task]
)

# Agent tries to parse context as DataFrame
# But context is TEXT, not DataFrame object!
```

**Why It Fails:**
- Task context is always TEXT (string)
- Even if Task 1 worked with DataFrames internally
- Task 2 receives only the text output

**Fix:** Use JSON output format with Pydantic models

---

### ❌ Anti-Pattern 5: Over-Complex Tool Chains

**Wrong:**
```python
# Tool 1: Fetch raw data
# Tool 2: Clean data
# Tool 3: Calculate indicators
# Tool 4: Filter by indicators
# Tool 5: Rank by score
# Tool 6: Format output

# 6 separate tools = 6 LLM calls = slow + error-prone
```

**Why It's Bad:**
- Too many tool calls = high latency
- Each call risks serialization issues
- Hard to debug failures
- LLM may skip steps or reorder them

**Fix:** Combine related operations in single tool

**Better:**
```python
@tool("Analyze Market Data")
def analyze_market(symbols: list[str]) -> dict:
    # Do all processing internally
    results = {}
    for symbol in symbols:
        df = fetch_and_clean(symbol)
        indicators = calculate_all_indicators(df)
        score = rank_by_criteria(indicators)
        results[symbol] = format_output(score, indicators)
    return results
```

---

## Correct Implementation Examples

### Example 1: Market Scanner with Knowledge Sources

**Scenario:** Scan 100 symbols, analyze top 10 by volatility

**Solution:**
```python
from crewai import Crew, Agent, Task
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

# Step 1: Create knowledge source for market data
class MarketKnowledge(BaseKnowledgeSource):
    def load_content(self) -> dict:
        symbols = get_sp100_symbols()  # 100 symbols
        content = {}
        
        for symbol in symbols:
            df = fetch_ohlcv(symbol, "1Hour", 100)
            
            # Store as markdown (LLM-friendly format)
            content[symbol] = f"""
Symbol: {symbol}
Price: ${df['close'].iloc[-1]:.2f}
Volume: {df['volume'].tail(24).sum():.0f}
High: ${df['high'].tail(24).max():.2f}
Low: ${df['low'].tail(24).min():.2f}
ATR: {calculate_atr(df):.2f}
"""
        
        return content

# Step 2: Create agent with knowledge
scanner = Agent(
    role="Market Scanner",
    goal="Find high-volatility assets",
    backstory="Expert scanner",
    knowledge_sources=[MarketKnowledge()]
)

# Step 3: Create task (agent queries knowledge by symbol)
scan_task = Task(
    description="Find top 10 symbols by volatility from S&P 100",
    expected_output="List of 10 symbols with volatility metrics",
    agent=scanner
)

crew = Crew(agents=[scanner], tasks=[scan_task])
result = crew.kickoff()
```

**Why This Works:**
- ✅ Data preloaded into knowledge base (no serialization)
- ✅ Agent queries by symbol name (strings)
- ✅ LLM reads text context, no DataFrame passing
- ✅ Scales to 100+ symbols

---

### Example 2: Trading Workflow with Flows

**Scenario:** Fetch data → Calculate indicators → Generate signals → Place trades

**Solution:**
```python
from crewai.flow.flow import Flow, listen, start
from crewai import Crew, Agent, Task

class TradingFlow(Flow):
    """Data pipeline in Flow, analysis in Crew."""
    
    @start()
    def fetch_data(self) -> dict:
        """Fetch data (DataFrames OK in Flow)."""
        symbols = ["BTC/USD", "ETH/USD"]
        data = {s: fetch_ohlcv(s, "1Hour", 100) for s in symbols}
        return data
    
    @listen(fetch_data)
    def calculate_indicators(self, data: dict) -> dict:
        """Calculate indicators (DataFrames OK in Flow)."""
        indicators = {}
        for symbol, df in data.items():
            indicators[symbol] = {
                "rsi": float(calculate_rsi(df)),
                "macd": float(calculate_macd(df)),
                "price": float(df['close'].iloc[-1])
            }
        return indicators
    
    @listen(calculate_indicators)
    def generate_signals(self, indicators: dict) -> dict:
        """Use Crew for signal generation."""
        analyst = Agent(
            role="Signal Generator",
            goal="Generate trading signals",
            backstory="Expert trader"
        )
        
        task = Task(
            description=f"Generate signals for: {indicators}",
            expected_output="Trading signals (BUY/SELL/HOLD)",
            agent=analyst
        )
        
        crew = Crew(agents=[analyst], tasks=[task])
        result = crew.kickoff(inputs={"indicators": indicators})
        
        # Parse result back to structured format
        return {"signals": result.raw}

# Run flow
flow = TradingFlow()
result = flow.kickoff()
```

**Why This Works:**
- ✅ DataFrames stay in Flow code (Python level)
- ✅ Crew only receives JSON-serializable indicators
- ✅ Clear separation: data processing vs analysis
- ✅ Efficient: no redundant fetching

---

### Example 3: Independent Tools Pattern

**Scenario:** Simple analysis workflow, no shared state

**Solution:**
```python
from crewai_tools import tool

@tool("Fetch Market Summary")
def fetch_market_summary(symbols: list[str]) -> dict:
    """Fetch and summarize market data."""
    summary = {}
    
    for symbol in symbols:
        df = fetch_ohlcv(symbol, "1Hour", 24)  # Fetch internally
        
        summary[symbol] = {
            "price": float(df['close'].iloc[-1]),
            "volume_24h": float(df['volume'].sum()),
            "change_24h": float((df['close'].iloc[-1] / df['open'].iloc[0] - 1) * 100)
        }
    
    return summary

@tool("Analyze Volatility")
def analyze_volatility(symbols: list[str]) -> dict:
    """Analyze volatility independently."""
    results = {}
    
    for symbol in symbols:
        df = fetch_ohlcv(symbol, "1Hour", 100)  # Fetch internally (duplicate)
        
        atr = calculate_atr(df)
        results[symbol] = {
            "atr": float(atr),
            "volatility_pct": float((atr / df['close'].mean()) * 100)
        }
    
    return results

# Agents call tools with simple parameters
analyst = Agent(
    role="Market Analyst",
    goal="Analyze markets",
    backstory="Expert analyst",
    tools=[fetch_market_summary, analyze_volatility]
)

task = Task(
    description="Analyze BTC/USD and ETH/USD",
    expected_output="Market analysis report",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

**Why This Works:**
- ✅ Tools are self-contained
- ✅ Only strings (symbol names) passed between tools
- ✅ Easy to test individually
- ✅ No serialization issues

**Trade-off:**
- ⚠️ Duplicate data fetching (fetch_ohlcv called twice)
- ⚠️ Less efficient than shared data approach
- ✅ But simpler and more reliable

---

## Migration Strategies

### Migrating from DataFrame-Passing to Knowledge Sources

**Current (Broken) Architecture:**
```python
# Tool 1: Fetch
@tool("Fetch Universe Data")
def fetch_data(symbols: list) -> Dict[str, pd.DataFrame]:
    return {s: fetch_ohlcv(s) for s in symbols}

# Tool 2: Analyze (FAILS - receives strings)
@tool("Analyze Volatility")
def analyze(data: Dict[str, pd.DataFrame]) -> dict:
    results = {}
    for symbol, df in data.items():  # df is STRING!
        results[symbol] = calculate_atr(df)  # ERROR
    return results
```

**Migration Steps:**

**Step 1: Create Knowledge Source**
```python
class MarketDataKnowledge(BaseKnowledgeSource):
    """Store fetched data in knowledge base."""
    
    def __init__(self, symbols: list[str], **kwargs):
        super().__init__(**kwargs)
        self.symbols = symbols
    
    def load_content(self) -> dict:
        content = {}
        for symbol in self.symbols:
            df = fetch_ohlcv(symbol, "1Hour", 100)
            # Store as CSV or markdown
            content[symbol] = df.to_csv()
        return content
    
    def add(self):
        content = self.load_content()
        for symbol, csv_data in content.items():
            chunks = self._chunk_text(csv_data)
            self.chunks.extend(chunks)
        self._save_documents()
```

**Step 2: Refactor Tools to Query Knowledge**
```python
# NEW: Tool queries knowledge by symbol name
@tool("Analyze Volatility from Knowledge")
def analyze_from_knowledge(symbols: list[str]) -> dict:
    """Analyze volatility using data from knowledge base."""
    results = {}
    
    for symbol in symbols:
        # Fetch internally (not from tool parameter)
        df = fetch_ohlcv(symbol, "1Hour", 100)
        
        # Calculate metrics
        atr = calculate_atr(df)
        results[symbol] = {
            "atr": float(atr),
            "volatility": float((atr / df['close'].mean()) * 100)
        }
    
    return results
```

**Step 3: Update Crew Configuration**
```python
# OLD
crew = Crew(
    agents=[data_agent, analyst_agent],
    tasks=[fetch_task, analyze_task],
    process=Process.sequential
)

# NEW
knowledge = MarketDataKnowledge(symbols=["BTC/USD", "ETH/USD"])

crew = Crew(
    agents=[analyst_agent],  # Only one agent needed
    tasks=[analyze_task],     # Single task
    knowledge_sources=[knowledge],
    process=Process.sequential
)
```

**Step 4: Update Task Definitions**
```python
# OLD: Two separate tasks
fetch_task = Task(
    description="Fetch data for symbols",
    expected_output="DataFrames",  # Doesn't work!
    agent=data_agent
)

analyze_task = Task(
    description="Analyze data from previous task",
    expected_output="Analysis",
    agent=analyst_agent,
    context=[fetch_task]  # Broken: receives strings
)

# NEW: Single task with knowledge access
analyze_task = Task(
    description="Analyze volatility for BTC/USD and ETH/USD using available market data",
    expected_output="Volatility analysis report",
    agent=analyst_agent
)
```

---

### Estimated Migration Effort

**For AutoAnalyst (current state):**

1. **Create Market Data Knowledge Source** (~2-3 hours)
   - Implement `MarketDataKnowledgeSource`
   - Test data loading and chunking
   - Verify ChromaDB storage

2. **Refactor Scanner Tools** (~3-4 hours)
   - `fetch_universe_data`: Remove (data in knowledge)
   - `analyze_volatility`: Refactor to query knowledge or fetch independently
   - `analyze_technical_setup`: Same refactoring
   - `filter_by_liquidity`: Same refactoring

3. **Update Market Scanner Crew** (~1-2 hours)
   - Add knowledge source to crew config
   - Simplify agent workflow (single agent instead of pipeline)
   - Update task descriptions

4. **Testing & Validation** (~2-3 hours)
   - Test knowledge base loading
   - Verify scanner finds opportunities
   - Compare results with current system
   - Test autonomous mode end-to-end

**Total Estimated Time: 8-12 hours**

---

## Summary: Key Takeaways

### The Golden Rules

1. **Everything Must Be JSON-Serializable**
   - No DataFrames, no NumPy arrays, no complex objects
   - Use dicts, lists, strings, numbers, booleans

2. **Tools Should Be Self-Contained**
   - Don't rely on data from other tools
   - Fetch what you need inside the tool
   - Return JSON-serializable results

3. **Use Knowledge Sources for Reference Data**
   - Preload static/reference data
   - Agents query by identifier (strings)
   - Let CrewAI handle retrieval

4. **Use Flows for Data Pipelines**
   - Keep DataFrames in Flow code
   - Pass only JSON-serializable summaries to Crews
   - Crews handle analysis, not data processing

5. **Task Context is Always Text**
   - Even if Task 1 returns structured data
   - Task 2 receives it as string
   - Use Pydantic models for structured outputs

### When to Use Each Pattern

| Pattern | Use When | Pros | Cons |
|---------|----------|------|------|
| **Knowledge Sources** | Static reference data, large datasets | RAG-based, persistent, semantic search | Text-only, setup overhead |
| **Shared Memory** | Session state, task context | Built-in, automatic | Text-only, limited structure |
| **Independent Tools** | Simple workflows, no shared data | Simple, reliable | Duplicate fetching |
| **Flows** | Complex pipelines, data processing | Python control, efficient | More complex architecture |

### Common Mistakes to Avoid

- ❌ Passing DataFrames between tools
- ❌ Storing complex objects in agent state
- ❌ Assuming task context is structured data
- ❌ Creating over-complex tool chains
- ❌ Relying on tool call order

### Quick Decision Tree

```
Need to share data between agents?
│
├─ YES
│  │
│  ├─ Static/reference data?
│  │  └─ Use Knowledge Sources
│  │
│  ├─ Dynamic execution state?
│  │  └─ Use Shared Memory
│  │
│  └─ Complex data pipeline?
│     └─ Use Flows
│
└─ NO
   └─ Use Independent Tools
```

---

## Additional Resources

### Official Documentation
- [CrewAI Core Concepts](https://docs.crewai.com/concepts)
- [Tools Documentation](https://docs.crewai.com/concepts/tools)
- [Knowledge System](https://docs.crewai.com/concepts/knowledge)
- [Memory System](https://docs.crewai.com/concepts/memory)
- [Tasks Guide](https://docs.crewai.com/concepts/tasks)
- [Flows Documentation](https://docs.crewai.com/concepts/flows)

### AutoAnalyst-Specific Docs
- `docs/FRAMEWORK_USAGE_GUIDE.md` - How we use CrewAI in AutoAnalyst
- `docs/AGENT_DESIGN.md` - Agent architecture and responsibilities
- `docs/FEATURE_ROADMAP.md` - Development phases and priorities

---

**Document Version:** 1.0  
**Last Updated:** November 4, 2025  
**Maintainer:** AutoAnalyst Development Team  
**Status:** Living Document - Update as new patterns are discovered
