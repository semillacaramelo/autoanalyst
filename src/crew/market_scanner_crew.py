"""
Market Scanner Crew
This crew is responsible for scanning the market and identifying trading opportunities.
"""
import os
from crewai import Crew, Process, Task
from crewai.llm import LLM
from src.agents.scanner_agents import ScannerAgents
from src.config.settings import settings

class MarketScannerCrew:

    def __init__(self):
        os.environ["GEMINI_API_KEY"] = settings.get_gemini_keys_list()[0]
        llm = LLM(
            model=f"gemini/{settings.primary_llm_models[0]}"
        )
        agents_factory = ScannerAgents()

        # Define Agents
        self.volatility_analyzer = agents_factory.volatility_analyzer_agent(llm)
        self.technical_analyzer = agents_factory.technical_setup_agent(llm)
        self.liquidity_filter = agents_factory.liquidity_filter_agent(llm)
        self.chief_analyst = agents_factory.market_intelligence_chief(llm)

    def run(self):
        # Define Tasks
        fetch_and_analyze_volatility = Task(
            description="Fetch the S&P 100 symbols, get their daily data for the last 100 days, and analyze their volatility.",
            expected_output="A list of dictionaries, each containing a symbol and its volatility analysis.",
            agent=self.volatility_analyzer
        )

        analyze_technicals = Task(
            description="Based on the data from the volatility analysis, analyze the technical setup of each stock.",
            expected_output="A list of dictionaries, each containing a symbol and its technical score.",
            agent=self.technical_analyzer,
            context=[fetch_and_analyze_volatility]
        )

        filter_by_liquidity = Task(
            description="Filter the stocks by liquidity, ensuring they have an average daily volume of at least 1,000,000 shares.",
            expected_output="A list of dictionaries, each containing a symbol and its liquidity status.",
            agent=self.liquidity_filter,
            context=[fetch_and_analyze_volatility]
        )

        synthesize_results = Task(
            description="Synthesize the results from the volatility, technical, and liquidity analyses to create a prioritized list of the top 5 trading opportunities.",
            expected_output="A JSON object containing the top 5 assets to trade, with their scores and recommended strategies.",
            agent=self.chief_analyst,
            context=[analyze_technicals, filter_by_liquidity]
        )

        # Assemble the Crew
        scanner_crew = Crew(
            agents=[self.volatility_analyzer, self.technical_analyzer, self.liquidity_filter, self.chief_analyst],
            tasks=[fetch_and_analyze_volatility, analyze_technicals, filter_by_liquidity, synthesize_results],
            process=Process.sequential,
            verbose=True
        )

        result = scanner_crew.kickoff()
        return result

market_scanner_crew = MarketScannerCrew()
