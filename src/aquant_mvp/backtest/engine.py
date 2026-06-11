from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from aquant_mvp.config import BacktestConfig


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    holdings: pd.DataFrame
    rebalances: pd.DataFrame
    metrics: dict[str, float]


def run_backtest(
    bars_by_symbol: dict[str, pd.DataFrame],
    target_weights: pd.DataFrame,
    config: BacktestConfig,
) -> BacktestResult:
    panels = _build_price_panels(bars_by_symbol)
    trading_dates = panels["close"].index
    execute_targets = _shift_targets_to_next_trade_date(target_weights, trading_dates)

    cash = float(config.initial_cash)
    lots: dict[str, list[dict[str, object]]] = {symbol: [] for symbol in panels["close"].columns}
    equity_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    holding_rows: list[dict[str, object]] = []
    rebalance_rows: list[dict[str, object]] = []

    for date in trading_dates:
        if date in execute_targets:
            target = execute_targets[date]
            cash, rebalance_row = _rebalance(date, target, panels, lots, cash, config, trade_rows)
            rebalance_rows.append(rebalance_row)

        close_prices = panels["close"].loc[date]
        market_value = _holdings_value(lots, close_prices)
        equity = cash + market_value
        equity_rows.append({"date": date, "cash": cash, "market_value": market_value, "equity": equity})

        for symbol, shares in _shares_by_symbol(lots).items():
            if shares <= 0:
                continue
            close = float(close_prices.get(symbol, np.nan))
            if math.isnan(close):
                continue
            holding_rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "shares": shares,
                    "close": close,
                    "market_value": shares * close,
                    "weight": shares * close / equity if equity > 0 else 0.0,
                }
            )

    equity_curve = _finalize_equity_curve(pd.DataFrame(equity_rows))
    trades = pd.DataFrame(trade_rows)
    holdings = pd.DataFrame(holding_rows)
    rebalances = pd.DataFrame(rebalance_rows)
    metrics = _compute_metrics(equity_curve, trades, rebalances, config.initial_cash)
    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades,
        holdings=holdings,
        rebalances=rebalances,
        metrics=metrics,
    )


def _rebalance(
    date: pd.Timestamp,
    target: pd.Series,
    panels: dict[str, pd.DataFrame],
    lots: dict[str, list[dict[str, object]]],
    cash: float,
    config: BacktestConfig,
    trade_rows: list[dict[str, object]],
) -> tuple[float, dict[str, object]]:
    open_prices = panels["open"].loc[date]
    close_prices = panels["close"].loc[date]
    equity_open = cash + _holdings_value(lots, open_prices)
    current_shares = _shares_by_symbol(lots)
    target = target.reindex(open_prices.index).fillna(0.0)

    desired_shares = {}
    for symbol, weight in target.items():
        price = float(open_prices.get(symbol, np.nan))
        if weight <= 0 or math.isnan(price) or price <= 0:
            desired_shares[symbol] = 0
            continue
        desired_value = equity_open * float(weight)
        desired_shares[symbol] = _floor_lot(desired_value / price, config.lot_size)

    sell_value = 0.0
    buy_value = 0.0
    sell_count = 0
    buy_count = 0

    for symbol, shares in current_shares.items():
        target_shares = desired_shares.get(symbol, 0)
        sell_shares = max(0, shares - target_shares)
        sell_shares = min(sell_shares, _available_shares(lots.get(symbol, []), date))
        sell_shares = _floor_lot(sell_shares, config.lot_size)
        if sell_shares <= 0:
            continue
        price = float(open_prices.get(symbol, np.nan))
        if math.isnan(price) or price <= 0:
            continue
        fill_price = price * (1 - config.slippage_rate)
        gross = fill_price * sell_shares
        fee = gross * config.fee_rate
        tax = gross * config.tax_rate
        cost_basis = _remove_lots_fifo(lots[symbol], sell_shares, date)
        realized_pnl = gross - fee - tax - cost_basis
        cash += gross - fee - tax
        sell_value += gross
        sell_count += 1
        trade_rows.append(
            _trade_row(
                date,
                symbol,
                "SELL",
                fill_price,
                sell_shares,
                gross,
                fee,
                tax,
                config,
                close_prices,
                cost_basis=cost_basis,
                realized_pnl=realized_pnl,
            )
        )

    for symbol, target_shares in desired_shares.items():
        shares = current_shares.get(symbol, 0)
        buy_shares = max(0, target_shares - shares)
        buy_shares = _floor_lot(buy_shares, config.lot_size)
        if buy_shares <= 0:
            continue
        price = float(open_prices.get(symbol, np.nan))
        if math.isnan(price) or price <= 0:
            continue
        fill_price = price * (1 + config.slippage_rate)
        max_affordable = _floor_lot(cash / (fill_price * (1 + config.fee_rate)), config.lot_size)
        buy_shares = min(buy_shares, max_affordable)
        gross = fill_price * buy_shares
        if buy_shares <= 0 or gross < config.min_trade_value:
            continue
        fee = gross * config.fee_rate
        cash -= gross + fee
        lots.setdefault(symbol, []).append({"shares": buy_shares, "buy_date": date, "cost_price": fill_price})
        buy_value += gross
        buy_count += 1
        trade_rows.append(
            _trade_row(
                date,
                symbol,
                "BUY",
                fill_price,
                buy_shares,
                gross,
                fee,
                0.0,
                config,
                close_prices,
                cost_basis=0.0,
                realized_pnl=0.0,
            )
        )

    traded_value = buy_value + sell_value
    return cash, {
        "date": date,
        "equity_open": equity_open,
        "buy_value": buy_value,
        "sell_value": sell_value,
        "traded_value": traded_value,
        "turnover": traded_value / equity_open if equity_open > 0 else 0.0,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "target_weight_sum": float(target.sum()),
    }


def _trade_row(
    date: pd.Timestamp,
    symbol: str,
    side: str,
    fill_price: float,
    shares: int,
    gross: float,
    fee: float,
    tax: float,
    config: BacktestConfig,
    close_prices: pd.Series,
    cost_basis: float,
    realized_pnl: float,
) -> dict[str, object]:
    close_price = float(close_prices.get(symbol, np.nan))
    return {
        "date": date,
        "symbol": symbol,
        "side": side,
        "price": fill_price,
        "shares": shares,
        "gross_value": gross,
        "fee": fee,
        "tax": tax,
        "cost_basis": cost_basis,
        "realized_pnl": realized_pnl,
        "slippage_rate": config.slippage_rate,
        "close": close_price,
    }


def _build_price_panels(bars_by_symbol: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    panels: dict[str, pd.DataFrame] = {}
    for field in ["open", "close"]:
        frame = pd.concat(
            [
                bars.assign(date=pd.to_datetime(bars["date"])).set_index("date")[[field]].rename(columns={field: symbol})
                for symbol, bars in bars_by_symbol.items()
            ],
            axis=1,
        ).sort_index()
        panels[field] = frame.ffill()
    return panels


def _shift_targets_to_next_trade_date(
    target_weights: pd.DataFrame,
    trading_dates: pd.DatetimeIndex,
) -> dict[pd.Timestamp, pd.Series]:
    execute: dict[pd.Timestamp, pd.Series] = {}
    for signal_date, row in target_weights.iterrows():
        pos = trading_dates.searchsorted(pd.Timestamp(signal_date), side="right")
        if pos >= len(trading_dates):
            continue
        execute[trading_dates[pos]] = row
    return execute


def _holdings_value(lots: dict[str, list[dict[str, object]]], prices: pd.Series) -> float:
    total = 0.0
    for symbol, symbol_lots in lots.items():
        shares = sum(int(lot["shares"]) for lot in symbol_lots)
        price = float(prices.get(symbol, np.nan))
        if shares > 0 and not math.isnan(price):
            total += shares * price
    return total


def _shares_by_symbol(lots: dict[str, list[dict[str, object]]]) -> dict[str, int]:
    return {symbol: sum(int(lot["shares"]) for lot in symbol_lots) for symbol, symbol_lots in lots.items()}


def _available_shares(symbol_lots: list[dict[str, object]], date: pd.Timestamp) -> int:
    return sum(int(lot["shares"]) for lot in symbol_lots if pd.Timestamp(lot["buy_date"]) < date)


def _remove_lots_fifo(symbol_lots: list[dict[str, object]], shares: int, date: pd.Timestamp) -> float:
    remaining = shares
    cost_basis = 0.0
    for lot in symbol_lots:
        if remaining <= 0:
            break
        if pd.Timestamp(lot["buy_date"]) >= date:
            continue
        lot_shares = int(lot["shares"])
        used = min(lot_shares, remaining)
        cost_basis += used * float(lot.get("cost_price", 0.0))
        lot["shares"] = lot_shares - used
        remaining -= used
    symbol_lots[:] = [lot for lot in symbol_lots if int(lot["shares"]) > 0]
    return cost_basis


def _floor_lot(shares: float | int, lot_size: int) -> int:
    if lot_size <= 1:
        return max(0, int(shares))
    return max(0, int(float(shares) // lot_size * lot_size))


def _finalize_equity_curve(equity_curve: pd.DataFrame) -> pd.DataFrame:
    if equity_curve.empty:
        return equity_curve
    out = equity_curve.copy()
    out["daily_return"] = out["equity"].pct_change().fillna(0.0)
    out["running_max"] = out["equity"].cummax()
    out["drawdown"] = out["equity"] / out["running_max"] - 1
    return out


def _compute_metrics(
    equity_curve: pd.DataFrame,
    trades: pd.DataFrame,
    rebalances: pd.DataFrame,
    initial_cash: float,
) -> dict[str, float]:
    equity = equity_curve["equity"].astype(float)
    returns = equity_curve["daily_return"].astype(float).dropna()
    total_return = equity.iloc[-1] / initial_cash - 1
    days = max(1, len(equity_curve))
    annual_return = (1 + total_return) ** (252 / days) - 1
    max_drawdown = float(equity_curve["drawdown"].min())
    annual_volatility = float(returns.std(ddof=0) * np.sqrt(252)) if len(returns) > 1 else 0.0
    sharpe = float(returns.mean() / returns.std(ddof=0) * np.sqrt(252)) if returns.std(ddof=0) > 0 else 0.0
    calmar = float(annual_return / abs(max_drawdown)) if max_drawdown < 0 else 0.0
    sell_trades = trades[trades["side"] == "SELL"] if not trades.empty else pd.DataFrame()
    win_rate = float((sell_trades["realized_pnl"] > 0).mean()) if not sell_trades.empty else 0.0
    avg_turnover = float(rebalances["turnover"].mean()) if not rebalances.empty else 0.0
    total_turnover = float(rebalances["turnover"].sum()) if not rebalances.empty else 0.0
    return {
        "initial_cash": float(initial_cash),
        "final_equity": float(equity.iloc[-1]),
        "total_return": float(total_return),
        "annual_return": float(annual_return),
        "annual_volatility": annual_volatility,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "calmar": calmar,
        "win_rate": win_rate,
        "avg_turnover": avg_turnover,
        "total_turnover": total_turnover,
        "trade_count": float(len(trades)),
        "rebalance_count": float(len(rebalances)),
    }
