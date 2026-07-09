from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    data_dir: str = "data"
    report_dir: str = "reports"
    longport_client_id: str | None = None
    longport_access_token: str | None = None
    longport_region: str = "cn"
    openai_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            data_dir=os.getenv("FINANCIAL_AGENT_DATA_DIR", "data"),
            report_dir=os.getenv("FINANCIAL_AGENT_REPORT_DIR", "reports"),
            longport_client_id=os.getenv("LONGPORT_CLIENT_ID") or None,
            longport_access_token=os.getenv("LONGPORT_ACCESS_TOKEN") or None,
            longport_region=os.getenv("LONGPORT_REGION", "cn"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        )
