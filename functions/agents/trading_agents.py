from crewai import Agent
from tools.alpaca_tools import fetch_historical_data, place_market_order, fetch_1_minute_historical_data
from tools.analysis_tools import calculate_3ma_signal, get_trade_history, calculate_performance_metrics
from typing import Dict, Any

def get_trading_agents(llm_config: Dict[str, Any]):
    """
    Creates and returns all trading agents with the specified LLM configuration.
    """
    asset_selector = Agent(
        role="Portfolio Strategy Analyst",
        goal="Select optimal assets based on volatility, liquidity, and criteria.",
        backstory="A sharp analyst identifying promising assets.",
        verbose=True,
        allow_delegation=False,
        llm=llm_config
    )

    trend_analyzer = Agent(
        role="Quantitative Strategy Specialist",
        goal="Generate signals using a 3 MA strategy on 1-minute charts.",
        backstory="A master of technical analysis focused on the 3 MA strategy.",
        verbose=True,
        allow_delegation=False,
        tools=[fetch_1_minute_historical_data, calculate_3ma_signal],
        llm=llm_config
    )

    signal_confirmer = Agent(
        role="Chief Risk Officer",
        goal="Validate trade signals to minimize risk and protect capital.",
        backstory="The guardian of capital, scrutinizing every signal for risk.",
        verbose=True,
        allow_delegation=False,
        llm=llm_config
    )

    trade_executor = Agent(
        role="Head of Trading Desk",
        goal="Execute confirmed trade signals precisely via the Alpaca API.",
        backstory="A cool-headed expert in trade execution.",
        verbose=True,
        allow_delegation=False,
        tools=[place_market_order],
        llm=llm_config
    )

    performance_analyzer = Agent(
        role="Performance Review Analyst",
        goal="Track trade outcomes and calculate performance metrics.",
        backstory="A data storyteller analyzing what worked and what didn't.",
        verbose=True,
        allow_delegation=False,
        tools=[get_trade_history, calculate_performance_metrics],
        llm=llm_config
    )

    strategy_enhancer = Agent(
        role="AI Strategy Futurist",
        goal="Propose improvements to the trading strategy based on data.",
        backstory="A forward-thinking strategist learning from past performance.",
        verbose=True,
        allow_delegation=False,
        llm=llm_config
    )

    return {
        "asset_selector": asset_selector,
        "trend_analyzer": trend_analyzer,
        "signal_confirmer": signal_confirmer,
        "trade_executor": trade_executor,
        "performance_analyzer": performance_analyzer,
        "strategy_enhancer": strategy_enhancer,
    }
