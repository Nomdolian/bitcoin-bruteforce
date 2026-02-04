from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict

from trading_bot.config import RiskConfig


@dataclass
class RiskState:
    daily_loss: float = 0.0
    trades_taken: int = 0
    last_trade_day: date = date.min


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self.state = RiskState()

    def reset_if_new_day(self, today: date) -> None:
        if self.state.last_trade_day != today:
            self.state.daily_loss = 0.0
            self.state.trades_taken = 0
            self.state.last_trade_day = today

    def can_trade(self, open_positions: int, today: date) -> bool:
        self.reset_if_new_day(today)
        if self.state.daily_loss <= -abs(self.config.max_daily_loss):
            return False
        if self.state.trades_taken >= self.config.max_trades_per_day:
            return False
        if open_positions >= self.config.max_open_positions:
            return False
        return True

    def record_trade(self, pnl: float) -> None:
        self.state.trades_taken += 1
        self.state.daily_loss += pnl

    def position_size(
        self,
        balance: float,
        entry: float,
        stop_loss: float,
        pip_value: float,
        pip_size: float,
    ) -> float:
        risk_amount = balance * self.config.risk_per_trade
        stop_distance = abs(entry - stop_loss)
        if stop_distance <= 0:
            return 0.0
        pips = stop_distance / pip_size
        if pips <= 0:
            return 0.0
        lot_size = risk_amount / (pips * pip_value)
        return max(lot_size, 0.0)

    def enforce_rr(self, entry: float, stop_loss: float, take_profit: float) -> bool:
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        if risk <= 0:
            return False
        return reward / risk >= self.config.min_rr
