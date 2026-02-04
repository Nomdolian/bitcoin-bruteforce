from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from trading_bot.config import StrategyConfig


@dataclass(frozen=True)
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Signal:
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    reason: str


def ema(values: np.ndarray, period: int) -> np.ndarray:
    if len(values) < period:
        return np.array([])
    weights = np.exp(np.linspace(-1.0, 0.0, period))
    weights /= weights.sum()
    ema_values = np.convolve(values, weights, mode="full")[: len(values)]
    ema_values[: period] = ema_values[period]
    return ema_values


class SMCStrategy:
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def generate_signal(self, candles: List[Candle]) -> Optional[Signal]:
        if len(candles) < max(
            self.config.order_block_lookback,
            self.config.liquidity_lookback,
            self.config.ema_slow,
        ):
            return None
        closes = np.array([c.close for c in candles])
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        ema_fast = ema(closes, self.config.ema_fast)
        ema_slow = ema(closes, self.config.ema_slow)
        if ema_fast.size == 0 or ema_slow.size == 0:
            return None
        trend_up = ema_fast[-1] > ema_slow[-1]

        liquidity = self._liquidity_sweep(candles)
        order_block = self._order_block(candles, trend_up)
        fvg = self._fair_value_gap(candles, trend_up)

        if trend_up and liquidity == "buy" and order_block and fvg:
            entry = closes[-1]
            stop = min(order_block, lows[-1])
            take_profit = entry + (entry - stop) * 2
            return Signal(
                direction="buy",
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit,
                reason="trend_up + liquidity_sweep + order_block + fvg",
            )

        if (not trend_up) and liquidity == "sell" and order_block and fvg:
            entry = closes[-1]
            stop = max(order_block, highs[-1])
            take_profit = entry - (stop - entry) * 2
            return Signal(
                direction="sell",
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit,
                reason="trend_down + liquidity_sweep + order_block + fvg",
            )
        return None

    def _liquidity_sweep(self, candles: List[Candle]) -> Optional[str]:
        lookback = self.config.liquidity_lookback
        recent = candles[-lookback:]
        last = recent[-1]
        prev_high = max(c.high for c in recent[:-1])
        prev_low = min(c.low for c in recent[:-1])
        if last.high > prev_high and last.close < prev_high:
            return "sell"
        if last.low < prev_low and last.close > prev_low:
            return "buy"
        return None

    def _order_block(self, candles: List[Candle], trend_up: bool) -> Optional[float]:
        lookback = self.config.order_block_lookback
        recent = candles[-lookback:]
        if trend_up:
            bearish = [c for c in recent if c.close < c.open]
            if bearish:
                return min(b.low for b in bearish[-3:])
        else:
            bullish = [c for c in recent if c.close > c.open]
            if bullish:
                return max(b.high for b in bullish[-3:])
        return None

    def _fair_value_gap(self, candles: List[Candle], trend_up: bool) -> Optional[float]:
        lookback = self.config.fvg_lookback
        recent = candles[-lookback:]
        if len(recent) < 3:
            return None
        for i in range(2, len(recent)):
            c0 = recent[i - 2]
            c2 = recent[i]
            if trend_up and c2.low > c0.high:
                return c2.low
            if (not trend_up) and c2.high < c0.low:
                return c2.high
        return None
