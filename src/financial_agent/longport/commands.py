from datetime import date
from pathlib import Path
from typing import Optional

import typer

from financial_agent.config.settings import Settings
from financial_agent.longport.client import LongPortClient, LongPortError
from financial_agent.longport.daily import sync_daily

auth_app = typer.Typer(help="长桥认证与只读连接验证")
market_app = typer.Typer(help="真实行情获取与本地缓存")


@auth_app.command("status")
def auth_status(env_file: Optional[Path] = typer.Option(None, help="本地配置文件，支持其他项目的 .env")) -> None:
    try:
        settings = Settings.from_env(env_file)
        client = LongPortClient(settings)
    except (ValueError, OSError) as exc:
        typer.echo(f"配置错误：{exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"auth_mode={settings.effective_auth_mode}; configured={client.is_configured}; 未调用 API")


def _verify(symbol: str, env_file: Optional[Path], login: bool) -> None:
    try:
        callback = (lambda url: typer.echo(f"请在浏览器授权：{url}")) if login else None
        client = LongPortClient(Settings.from_env(env_file), on_open_url=callback)
        result = client.verify(symbol)
    except (LongPortError, ValueError, OSError) as exc:
        typer.echo(f"验证失败：{exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"长桥 static_info 验证成功：{result['symbol']}，{result['records']} 条记录")


@auth_app.command("verify")
def auth_verify(symbol: str = typer.Option("AAPL.US"), env_file: Optional[Path] = typer.Option(None)) -> None:
    _verify(symbol, env_file, login=False)


@auth_app.command("oauth-login")
def oauth_login(symbol: str = typer.Option("AAPL.US"), env_file: Optional[Path] = typer.Option(None)) -> None:
    _verify(symbol, env_file, login=True)


@market_app.command("daily")
def market_daily(
    symbol: str = typer.Option(..., help="美股代码，如 AAPL.US"),
    start: str = typer.Option(..., help="开始日期 YYYY-MM-DD"),
    end: str = typer.Option(..., help="结束日期 YYYY-MM-DD，最多 366 个日历日"),
    env_file: Optional[Path] = typer.Option(None, help="本地配置路径"),
    data_dir: Optional[Path] = typer.Option(None, help="缓存目录，默认使用配置中的 data_dir"),
    refresh: bool = typer.Option(False, help="重新请求同一日期范围"),
) -> None:
    try:
        start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        typer.echo("日期格式错误，应为 YYYY-MM-DD", err=True)
        raise typer.Exit(2) from exc
    try:
        settings = Settings.from_env(env_file)
        result = sync_daily(LongPortClient(settings), data_dir or Path(settings.data_dir), symbol, start_date, end_date, refresh=refresh)
    except (LongPortError, ValueError, OSError) as exc:
        typer.echo(f"行情获取失败：{exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"来源={result.origin}; {symbol}; {result.rows} 条日 K；{result.path}")
