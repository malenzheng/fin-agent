from __future__ import annotations

from financial_agent.config.settings import Settings


class LongPortClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.longport_client_id and self.settings.longport_access_token)

    def require_configured(self) -> None:
        if not self.is_configured:
            raise RuntimeError("LongPort credentials are not configured. Use local .env or environment variables.")
