# References

This project keeps its core implementation self-contained. External projects are used only for architecture and ecosystem reference.

## Referenced Projects

| Project | Source | Local Status | How It Was Used |
|---|---|---|---|
| Microsoft Qlib | `https://github.com/microsoft/qlib` | Read through GitHub MCP metadata and README. A local clone was attempted, but the network clone timed out and was not retained. | Research-platform structure, ML workflow direction, future Qlib integration planning. |
| AKShare | `https://github.com/akfamily/akshare` | Shallow-cloned to `external/akshare` for local reference. `external/` is ignored by git. | Public A-share data-source interface reference. |

## Boundary

- No external source code was copied into `src/aquant_mvp`.
- `external/` is ignored and should remain a local reference-only area.
- Before copying or vendoring any third-party code, review the upstream license and preserve attribution.

## Future References

- `microsoft/qlib`: AI-oriented quant research workflow and dataset provider design.
- `ricequant/rqalpha`: event-driven backtest ideas for China market workflows.
- `vnpy/vnpy`: practical execution gateway ideas for later live trading.
- `akfamily/akshare`: public financial data adapters.

