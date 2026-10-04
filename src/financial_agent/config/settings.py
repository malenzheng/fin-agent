from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv.main import DotEnv


@dataclass(frozen=True)
class Settings:
    data_dir: str = "data"
    report_dir: str = "reports"
    longport_client_id: str | None = field(default=None, repr=False)
    longport_access_token: str | None = field(default=None, repr=False)
    longport_region: str = "cn"
    openai_api_key: str | None = field(default=None, repr=False)
    longport_auth_mode: str = "auto"
    longport_app_key: str | None = field(default=None, repr=False)
    longport_app_secret: str | None = field(default=None, repr=False)
    longport_oauth_callback_port: int | None = None

    def __post_init__(self) -> None:
        if self.longport_auth_mode not in {"auto", "oauth", "api_key"}:
            raise ValueError("LONGBRIDGE_AUTH_MODE must be auto, oauth or api_key")
        if self.longport_oauth_callback_port is not None and not 1 <= self.longport_oauth_callback_port <= 65535:
            raise ValueError("OAuth callback port must be between 1 and 65535")

    @property
    def effective_auth_mode(self) -> str:
        if self.longport_auth_mode != "auto":
            return self.longport_auth_mode
        return "api_key" if all((self.longport_app_key, self.longport_app_secret, self.longport_access_token)) else "oauth"

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        path = Path(env_file) if env_file is not None else Path(".env")
        if env_file is not None and not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        # Preserve load_dotenv's interpolation precedence without mutating os.environ.
        values = DotEnv(path, encoding="utf-8", override=False).dict() if path.is_file() else {}

        def read(name: str, legacy: str | None = None) -> str | None:
            for source in (os.environ, values):
                for key in (name, legacy):
                    if key is not None and key in source:
                        return (source[key] or "").strip() or None
            return None

        callback_port = read("LONGBRIDGE_OAUTH_CALLBACK_PORT", "LONGPORT_OAUTH_CALLBACK_PORT")
        return cls(
            data_dir=read("FINANCIAL_AGENT_DATA_DIR") or "data",
            report_dir=read("FINANCIAL_AGENT_REPORT_DIR") or "reports",
            longport_client_id=read("LONGBRIDGE_CLIENT_ID", "LONGPORT_CLIENT_ID"),
            longport_access_token=read("LONGBRIDGE_ACCESS_TOKEN", "LONGPORT_ACCESS_TOKEN"),
            longport_region=read("LONGPORT_REGION") or "cn",
            openai_api_key=read("OPENAI_API_KEY"),
            longport_auth_mode=read("LONGBRIDGE_AUTH_MODE", "LONGPORT_AUTH_MODE") or "auto",
            longport_app_key=read("LONGBRIDGE_APP_KEY", "LONGPORT_APP_KEY"),
            longport_app_secret=read("LONGBRIDGE_APP_SECRET", "LONGPORT_APP_SECRET"),
            longport_oauth_callback_port=int(callback_port) if callback_port else None,
        )
