"""
Shared context for the trading crew.
"""


class CrewContext:
    """
    Shared context object for the trading crew.
    """

    def __init__(self):
        self.market_data = None


# Global singleton instance
crew_context = CrewContext()
