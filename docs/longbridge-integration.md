# 长桥接入与已有项目复用

本次参考“美股选股”项目 `quant-hot-sector-breakout` 中的：

- `quant_signal/data_sources/longbridge_client.py`：OAuthBuilder、Config.from_oauth / from_apikey、QuoteContext、static_info 验证。
- `quant_signal/data_sources/longbridge_market.py`：日 K 接口、数值转换、复用 QuoteContext。
- `quant_signal/cache.py` 与 `quant_signal/sync/candles.py`：缓存优先、来源记录的设计。

当前移植为适合本仓库的小型适配层，没有复制旧项目的所有选股、回测和交易逻辑。旧项目代码、.env 和缓存保持只读。

## 配置

优先使用 `LONGBRIDGE_*` 名称，同时兼容原 `LONGPORT_*` 别名。环境变量优先于指定文件；相同来源中 LONGBRIDGE 名称优先。读取文件不向进程环境注入凭证。`--env-file` 明确指定的文件必须存在；未指定则读取当前目录 `.env`，不存在时只读环境变量。

| 模式 | 必需字段 |
| --- | --- |
| `oauth` | `LONGBRIDGE_CLIENT_ID`；可选 `LONGBRIDGE_OAUTH_CALLBACK_PORT` |
| `api_key` | `LONGBRIDGE_APP_KEY`、`LONGBRIDGE_APP_SECRET`、`LONGBRIDGE_ACCESS_TOKEN` |
| `auto` | 三个 API Key 字段齐全则用 API Key，否则选择 OAuth |

注意：OAuth 不要求在 `.env` 里额外保存 access token。由 SDK 管理本机授权和 token；新机器或失效授权仍可能需要用户重新登录。

当前可选依赖使用 `longbridge==4.5.0`。旧项目本机曾安装 4.4.1，但本次使用的包源已不提供该版本，不能直接照抄成不可安装的依赖锁定。API 对照 [官方 Python 参考](https://longbridge.github.io/openapi/python/reference_all/)。旧的 `LONGPORT_REGION` 字段为兼容保留，目前不改变 SDK 服务端点。

配置解析保留 `${VARIABLE}` 引用和环境变量优先级，通过只读解析实现，不把整个外部 `.env` 导入当前进程。

## 命令与边界

- `auth status`：显示模式和配置是否齐全，不输出凭证，不访问 API。
- `auth verify`：使用已有授权调用单标的 `static_info`；没有授权时提示登录。
- `auth oauth-login`：允许 SDK 输出浏览器授权 URL，授权完成后验证静态信息。
- `market daily`：使用 `history_candlesticks_by_date`、`Period.Day`、`AdjustType.NoAdjust` 拉取美股日 K。

当前只接受明确的 `.US` 标的，例如 `AAPL.US`、`BRK.B.US`。返回 timestamp 转换为纽约交易日期；OHLCV 非有限数值、不合理价格关系或负成交量会报错。SDK 错误会隐藏配置中已知的凭证文本。

非交互验证使用 SDK 的异步 OAuth 构建接口，同时检测“需要浏览器授权”事件，OAuth 初始化最多等待 30 秒。不能靠在同步 SDK 的授权回调中抛异常来退出：本次实测同步构建仍会继续等待。显式 `oauth-login` 允许等待用户完成浏览器授权。此 30 秒限制只适用于非交互 OAuth 初始化，不是所有行情请求的总超时。

缓存按来源、不复权标识、请求起止日期和标的隔离，并保存抓取时间和文件 SHA-256。命中时核验请求身份、文件哈希、记录数和返回日期范围。同一精确范围可在无认证情况下重读完整缓存；不同范围重新查询，不做区间合并。不因查询失败而返回合成行情。

返回 0 条 K 线可能代表非交易日或没有该范围的数据，不等同于拿到了有效历史样本；判断回测覆盖度需要进一步检查交易日历与返回记录。

目前真实日 K 是独立数据入口。研究简报仍使用合成资讯，尚未接入长桥新闻、公告、财报、基本面；原 `screen smoke` 也仍为合成演示。下一步再将真实数据接入候选池和证据研究流程。

## 本地核验

单元测试使用假的 SDK 边界，验证本项目的认证分支、参数映射、数据转换、缓存和错误处理，不代表真实网络或账户权限已验证。真实连通结果必须另行记录。

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

2026-10-04 核验记录：原美股项目的认证/行情/认证 CLI 测试 16 个通过；本项目 62 个测试通过。安装并导入 longbridge 4.5.0 后，读取既有项目本地 OAuth 配置，SDK 明确触发了需要浏览器授权事件；修复后的 `auth verify` 已能提示登录并退出。本次没有完成新的浏览器授权，没有获得真实 static_info 返回或日 K 数据，不能称为真实行情端到端验收通过。
