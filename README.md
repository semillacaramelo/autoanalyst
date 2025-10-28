# Autonomous Analyst Trading Crew

## Project Description

This project implements an AI-driven trading crew using the CrewAI framework. The system is designed to be a modular, autonomous group of AI agents that perform financial market analysis, generate trading signals, execute trades, and analyze performance. The core reasoning engine for the agents is Google's Gemini LLM, and the system interacts with the market through the Alpaca Markets API.

## Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file will need to be generated from the project's dependencies.)*

3.  **Configure API Keys:**
    -   Copy the `.env.template` file to a new file named `.env`:
        ```bash
        cp .env.template .env
        ```
    -   Open the `.env` file and replace the placeholder values with your actual API keys:
        -   `GEMINI_API_KEYS`: A comma-separated list of your Google Gemini API keys.
        -   `ALPACA_API_KEY`: Your Alpaca API key.
        -   `ALPACA_SECRET_KEY`: Your Alpaca secret key.

## Application Architecture

The application is built on a modular, multi-agent architecture with a clear separation of concerns:

-   **Configuration (`config/`):**
    -   `config.py`: Loads all secrets and configuration settings from the `.env` file.
    -   `gemini_connector.py`: Contains the `GeminiConnectionManager`, which handles the connection to the Gemini API, including round-robin API key rotation for resilience and usage distribution.

-   **Tools (`tools/`):**
    -   This layer contains functions that provide the agents with their real-world capabilities.
    -   `alpaca_tools.py`: Includes all functions for interacting with the Alpaca Markets API, such as fetching historical data and placing market orders.

-   **Agents (`agents/`):**
    -   `trading_agents.py`: Defines each specialized AI agent using `crewai.Agent`. Each agent has a specific `role`, `goal`, `backstory`, and is assigned a set of `tools` to perform its tasks. Examples include the `AssetSelectionAgent`, `TrendAnalysisAgent`, and `TradeExecutionAgent`.

-   **Tasks (`tasks.py`):**
    -   This file defines the `crewai.Task` objects. Each task has a clear description, an expected output, and is assigned to a specific agent. Tasks can be chained together to form a logical workflow.

-   **Orchestration (`crew_setup.py`):**
    -   This is the central orchestrator that brings everything together.
    -   It imports the defined agents and tasks.
    -   It initializes the `GeminiConnectionManager` to get a configured LLM instance.
    -   It assigns the LLM to each agent, ensuring they all share the same reasoning engine.
    -   Finally, it defines the `crewai.Crew`, specifying the list of agents and tasks that will collaborate to achieve the overall goal. The crew is configured to run its tasks sequentially.
