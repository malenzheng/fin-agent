from financial_agent.config.settings import Settings
from financial_agent.longport.client import LongPortClient
from financial_agent.universe.static import StaticUniverseProvider


def test_static_universe_has_proxy_members() -> None:
    members = StaticUniverseProvider().members()
    symbols = {member.symbol for member in members}
    assert {"AAPL.US", "MSFT.US", "IWM.US"}.issubset(symbols)


def test_longport_client_reports_unconfigured() -> None:
    client = LongPortClient(Settings(longport_client_id=None, longport_access_token=None))
    assert client.is_configured is False
