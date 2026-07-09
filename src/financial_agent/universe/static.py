from __future__ import annotations

from financial_agent.domain.models import UniverseMember


class StaticUniverseProvider:
    def members(self) -> list[UniverseMember]:
        return [
            UniverseMember("AAPL.US", "Apple", "Nasdaq 100 proxy"),
            UniverseMember("MSFT.US", "Microsoft", "Nasdaq 100 proxy"),
            UniverseMember("NVDA.US", "Nvidia", "S&P 500 proxy"),
            UniverseMember("SPY.US", "SPDR S&P 500 ETF", "S&P 500 proxy"),
            UniverseMember("QQQ.US", "Invesco QQQ ETF", "Nasdaq 100 proxy"),
            UniverseMember("IWM.US", "iShares Russell 2000 ETF", "Russell 2000 proxy"),
        ]
