class VolatilityAnalyzerAgent:
    def __init__(self, scan_func):
        self.scan_func = scan_func

    def scan(self):
        return self.scan_func()

class TechnicalSetupAgent:
    def __init__(self, scan_func):
        self.scan_func = scan_func

    def scan(self, candidates):
        return self.scan_func(candidates)

class LiquidityFilterAgent:
    def __init__(self, scan_func):
        self.scan_func = scan_func

    def scan(self, candidates):
        return self.scan_func(candidates)

class SectorRotationAgent:
    def __init__(self, scan_func):
        self.scan_func = scan_func

    def scan(self, candidates):
        return self.scan_func(candidates)
