from crewai import Agent
from tools.alpaca_tools import fetch_historical_data, place_market_order
from tools.analysis_tools import calculate_3ma_signal

def get_trading_agents():
    """
    Creates and returns all the trading agents.
    This function is designed for lazy initialization of agents.
    """
    asset_selector = Agent(
        role="Portfolio Strategy Analyst",
        goal="Select the optimal assets to trade based on volatility, liquidity, and user-defined criteria.",
        backstory="You are a sharp and discerning analyst with a keen eye for opportunity. You filter out the noise and identify the most promising assets that fit the current trading strategy.",
        verbose=True,
        allow_delegation=False,
    )

    trend_analyzer = Agent(
        role="Quantitative Strategy Specialist",
        goal="Implement a triple-moving-average (3 MA) strategy to generate buy or sell signals for one-minute trades.",
        backstory="You are a master of technical analysis. You live and breathe charts and indicators. Your sole purpose is to apply the 3 MA strategy flawlessly to generate high-probability trade signals.",
        verbose=True,
        allow_delegation=False,
        tools=[fetch_historical_data, calculate_3ma_signal]
    )

    signal_confirmer = Agent(
        role="Chief Risk Officer",
        goal="Validate the quality and risk profile of trade signals before execution to minimize false positives and protect capital.",
        backstory="You are the guardian of the crew's capital. Cautious and analytical, you scrutinize every signal, checking it against current market volatility and risk parameters before giving the green light.",
        verbose=True,
        allow_delegation=False,
    )

    trade_executor = Agent(
        role="Head of Trading Desk",
        goal="Execute confirmed trade signals precisely and efficiently by placing orders through the Alpaca API.",
        backstory="You are a cool-headed execution expert. Once a signal is confirmed, you act with speed and precision, translating the crew's decision into a live market order without hesitation.",
        verbose=True,
        allow_delegation=False,
        tools=[place_market_order]
    )

    performance_analyzer = Agent(
        role="Performance Review Analyst",
        goal="Track all trade outcomes, calculate key performance metrics (win rate, profit factor), and generate insightful reports and visualizations.",
        backstory="You are a data storyteller. After the trades are done, you meticulously gather the results and translate them into a clear narrative of what worked, what didn't, and why.",
        verbose=True,
        allow_delegation=False,
    )

    strategy_enhancer = Agent(
        role="AI Strategy Futurist",
        goal="Propose data-driven improvements to the trading strategy based on performance analysis and evolving market conditions.",
        backstory="You are a forward-thinking strategist, constantly learning from past performance. Your goal is to analyze the performance reports and suggest concrete ways to adapt and improve the trading logic.",
        verbose=True,
        allow_delegation=False,
    )

    return {
        "asset_selector": asset_selector,
        "trend_analyzer": trend_analyzer,
        "signal_confirmer": signal_confirmer,
        "trade_executor": trade_executor,
        "performance_analyzer": performance_analyzer,
        "strategy_enhancer": strategy_enhancer,
    }
