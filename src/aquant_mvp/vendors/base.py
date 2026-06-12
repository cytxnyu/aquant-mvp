from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd


class VendorUnavailable(RuntimeError):
    """Raised when a vendor cannot serve the requested data."""


class VendorNotConfigured(VendorUnavailable):
    """Raised when a vendor needs credentials or a local client."""


@dataclass(frozen=True)
class VendorCapabilities:
    daily_bar: bool = False
    adj_factor: bool = False
    limit_price: bool = False
    suspension: bool = False
    st_flag: bool = False
    industry: bool = False
    financial: bool = False
    announcement: bool = False
    moneyflow: bool = False
    qmt_readonly: bool = False


@dataclass(frozen=True)
class VendorFetchResult:
    vendor: str
    table: str
    data: pd.DataFrame
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class DataVendorAdapter(Protocol):
    name: str
    capabilities: VendorCapabilities

    def fetch_daily_bars(self, symbol: str, start_date: str, end_date: str, adjust: str) -> VendorFetchResult:
        """Fetch point-in-time daily bars for one A-share symbol."""
