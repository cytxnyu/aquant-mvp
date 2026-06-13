from __future__ import annotations

from dataclasses import dataclass
import os
import time

import pandas as pd

from .base import DataVendorAdapter, VendorCapabilities, VendorFetchResult, VendorNotConfigured, VendorUnavailable


REQUIRED_DAILY_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "amount", "turnover"]


@dataclass(frozen=True)
class AkshareAdapter:
    name: str = "akshare"
    capabilities: VendorCapabilities = VendorCapabilities(daily_bar=True, moneyflow=True, industry=True)

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        try:
            import akshare as ak  # type: ignore
        except ImportError as exc:
            raise VendorNotConfigured("AKShare is not installed. Install `aquant-mvp[data]`.") from exc

        raw = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                raw = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=_compact_date(start_date),
                    end_date=_compact_date(end_date),
                    adjust=adjust,
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(0.8 * (attempt + 1))
        if raw is None:
            raise VendorUnavailable(f"AKShare daily bar request failed after retries: {last_error}")
        frame = _normalize_akshare_daily(raw, symbol)
        if frame.empty:
            raise VendorUnavailable("AKShare returned no daily bar rows")
        return VendorFetchResult(vendor=self.name, table="daily_bar", data=frame)


@dataclass(frozen=True)
class BaoStockAdapter:
    name: str = "baostock"
    capabilities: VendorCapabilities = VendorCapabilities(daily_bar=True, adj_factor=True, st_flag=True)
    _session: object | None = None
    _persistent: bool = False

    def __enter__(self) -> "BaoStockAdapter":
        object.__setattr__(self, "_persistent", True)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._session is not None:
            try:
                import baostock as bs  # type: ignore

                bs.logout()
            finally:
                object.__setattr__(self, "_session", None)
        object.__setattr__(self, "_persistent", False)

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        if self._session is None:
            object.__setattr__(self, "_session", self._login())
        owns_session = not self._persistent
        try:
            return self._query_daily_bars(symbol, start_date, end_date, adjust)
        finally:
            if owns_session:
                try:
                    import baostock as bs  # type: ignore

                    bs.logout()
                except Exception:  # noqa: BLE001
                    pass
                object.__setattr__(self, "_session", None)

    def _login(self) -> object:
        try:
            import baostock as bs  # type: ignore
        except ImportError as exc:
            raise VendorNotConfigured("BaoStock is not installed. Install `baostock` to enable this adapter.") from exc

        login = bs.login()
        if getattr(login, "error_code", "0") != "0":
            raise VendorUnavailable(f"BaoStock login failed: {getattr(login, 'error_msg', '')}")
        return login

    def _query_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        import baostock as bs  # type: ignore

        fields = "date,code,open,high,low,close,volume,amount,turn,tradestatus,pctChg,isST"
        query = bs.query_history_k_data_plus(
            _baostock_code(symbol),
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag=_baostock_adjust_flag(adjust),
        )
        if getattr(query, "error_code", "0") != "0":
            raise VendorUnavailable(f"BaoStock query failed: {getattr(query, 'error_msg', '')}")
        rows: list[list[str]] = []
        while query.next():
            rows.append(query.get_row_data())
        raw = pd.DataFrame(rows, columns=query.fields)

        frame = _normalize_baostock_daily(raw, symbol)
        if frame.empty:
            raise VendorUnavailable("BaoStock returned no daily bar rows")
        warnings = []
        if "tradestatus" in raw.columns and (raw["tradestatus"] == "0").any():
            warnings.append("BaoStock contains non-trading/suspended rows; normalized output keeps valid prices only.")
        return VendorFetchResult(vendor=self.name, table="daily_bar", data=frame, warnings=warnings)


@dataclass(frozen=True)
class TushareFreeAdapter:
    name: str = "tushare"
    capabilities: VendorCapabilities = VendorCapabilities(daily_bar=True, financial=True)

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        token = os.getenv("TUSHARE_TOKEN", "").strip()
        if not token:
            raise VendorNotConfigured("TUSHARE_TOKEN is not set; Tushare free adapter is disabled.")
        try:
            import tushare as ts  # type: ignore
        except ImportError as exc:
            raise VendorNotConfigured("Tushare is not installed. Install `tushare` to enable this adapter.") from exc

        pro = ts.pro_api(token)
        ts_code = _tushare_code(symbol)
        raw = pro.daily(ts_code=ts_code, start_date=_compact_date(start_date), end_date=_compact_date(end_date))
        if raw is None or raw.empty:
            raise VendorUnavailable("Tushare returned no daily bar rows")
        frame = _normalize_tushare_daily(raw, symbol)
        if frame.empty:
            raise VendorUnavailable("Tushare daily rows could not be normalized")
        warnings = ["Tushare free permissions vary by account; missing turnover is filled with NaN."]
        return VendorFetchResult(vendor=self.name, table="daily_bar", data=frame, warnings=warnings)


@dataclass(frozen=True)
class QMTReadOnlyAdapter:
    name: str = "qmt_readonly"
    capabilities: VendorCapabilities = VendorCapabilities(qmt_readonly=True)

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        try:
            import xtquant  # noqa: F401  # type: ignore
        except ImportError as exc:
            raise VendorNotConfigured("xtquant/QMT is not installed on this machine; QMT read-only is disabled.") from exc
        raise VendorUnavailable("QMT read-only adapter is reserved for account/position reconciliation, not bulk research sync.")


class FreeDataRouter:
    """Try free A-share data vendors in deterministic order without silently fabricating data."""

    def __init__(self, vendors: list[str] | None = None) -> None:
        self.adapters = [_make_adapter(name) for name in (vendors or ["akshare", "baostock", "tushare"])]

    def __enter__(self) -> "FreeDataRouter":
        for adapter in self.adapters:
            enter = getattr(adapter, "__enter__", None)
            if callable(enter):
                enter()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        for adapter in reversed(self.adapters):
            exit_method = getattr(adapter, "__exit__", None)
            if callable(exit_method):
                exit_method(None, None, None)

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        warnings: list[str] = []
        for adapter in self.adapters:
            try:
                result = adapter.fetch_daily_bars(symbol, start_date, end_date, adjust)
                return VendorFetchResult(
                    vendor=result.vendor,
                    table=result.table,
                    data=result.data,
                    warnings=[*warnings, *result.warnings],
                    metadata=result.metadata,
                )
            except VendorUnavailable as exc:
                warnings.append(f"{adapter.name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{adapter.name}: unexpected error: {exc}")
        raise VendorUnavailable("; ".join(warnings) or "No free data vendor is available.")


def _make_adapter(name: str) -> DataVendorAdapter:
    normalized = name.lower()
    if normalized in {"akshare", "ak"}:
        return AkshareAdapter()
    if normalized in {"baostock", "bs"}:
        return BaoStockAdapter()
    if normalized in {"tushare", "ts"}:
        return TushareFreeAdapter()
    if normalized in {"qmt", "qmt_readonly"}:
        return QMTReadOnlyAdapter()
    raise ValueError(f"Unsupported free data vendor: {name}")


def _normalize_akshare_daily(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    frame = _normalize_akshare_columns(raw)
    frame["symbol"] = symbol
    return _finalize_daily_bars(frame)


def _normalize_akshare_columns(raw: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "date": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "amount": "amount",
        "turnover": "turnover",
        "\u65e5\u671f": "date",
        "\u5f00\u76d8": "open",
        "\u6700\u9ad8": "high",
        "\u6700\u4f4e": "low",
        "\u6536\u76d8": "close",
        "\u6210\u4ea4\u91cf": "volume",
        "\u6210\u4ea4\u989d": "amount",
        "\u6362\u624b\u7387": "turnover",
    }
    rename_map = {column: aliases.get(str(column).strip().lower(), aliases.get(str(column).strip(), str(column).strip())) for column in raw.columns}
    frame = raw.rename(columns=rename_map).copy()
    missing = [name for name in REQUIRED_DAILY_COLUMNS if name not in frame.columns and name != "symbol"]
    if missing and len(raw.columns) >= 12:
        columns = list(raw.columns)
        positional = {
            columns[0]: "date",
            columns[2]: "open",
            columns[3]: "close",
            columns[4]: "high",
            columns[5]: "low",
            columns[6]: "volume",
            columns[7]: "amount",
            columns[11]: "turnover",
        }
        frame = raw.rename(columns=positional).copy()
    return frame


def _normalize_baostock_daily(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    frame = raw.rename(columns={"turn": "turnover"}).copy()
    frame["symbol"] = symbol
    return _finalize_daily_bars(frame)


def _normalize_tushare_daily(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    frame = raw.rename(
        columns={
            "trade_date": "date",
            "vol": "volume",
        }
    ).copy()
    frame["symbol"] = symbol
    if "volume" in frame.columns:
        frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce") * 100.0
    if "amount" in frame.columns:
        frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce") * 1000.0
    if "turnover" not in frame.columns:
        frame["turnover"] = pd.NA
    return _finalize_daily_bars(frame)


def _finalize_daily_bars(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    missing = [name for name in REQUIRED_DAILY_COLUMNS if name not in out.columns]
    if missing:
        raise VendorUnavailable(f"Daily bar schema missing columns: {missing}")
    out = out[REQUIRED_DAILY_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["symbol"] = out["symbol"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    for column in ["open", "high", "low", "close", "volume", "amount", "turnover"]:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out = out[(out[["open", "high", "low", "close"]] > 0).all(axis=1)]
    out = out[out["amount"].fillna(0) > 0]
    out = out.sort_values("date").drop_duplicates(subset=["date", "symbol"], keep="last")
    return out.reset_index(drop=True)


def _compact_date(value: str) -> str:
    return value.replace("-", "")


def _baostock_code(symbol: str) -> str:
    return f"sh.{symbol}" if symbol.startswith(("5", "6", "9")) else f"sz.{symbol}"


def _baostock_adjust_flag(adjust: str) -> str:
    if adjust in {"qfq", "front", "forward"}:
        return "2"
    if adjust in {"hfq", "back", "backward"}:
        return "1"
    return "3"


def _tushare_code(symbol: str) -> str:
    if symbol.startswith(("4", "8")):
        suffix = "BJ"
    elif symbol.startswith(("5", "6", "9")):
        suffix = "SH"
    else:
        suffix = "SZ"
    return f"{symbol}.{suffix}"
