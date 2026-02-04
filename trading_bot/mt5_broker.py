from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import MetaTrader5 as mt5

from trading_bot.config import BrokerConfig, ExecutionConfig
from trading_bot.strategy import Candle, Signal


@dataclass
class Position:
    ticket: int
    symbol: str
    volume: float
    direction: str


class MT5Broker:
    def __init__(self, config: BrokerConfig, execution: ExecutionConfig) -> None:
        self.config = config
        self.execution = execution

    def connect(self) -> bool:
        if self.config.path:
            connected = mt5.initialize(self.config.path)
        else:
            connected = mt5.initialize()
        if not connected:
            return False
        if self.config.login and self.config.password and self.config.server:
            return mt5.login(
                login=self.config.login,
                password=self.config.password,
                server=self.config.server,
            )
        return True

    def shutdown(self) -> None:
        mt5.shutdown()

    def get_candles(self, symbol: str, timeframe: int, count: int) -> List[Candle]:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            return []
        return [
            Candle(
                time=int(rate["time"]),
                open=rate["open"],
                high=rate["high"],
                low=rate["low"],
                close=rate["close"],
            )
            for rate in rates
        ]

    def get_balance(self) -> float:
        account = mt5.account_info()
        if account is None:
            return 0.0
        return float(account.balance)

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        results: List[Position] = []
        for pos in positions:
            direction = "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell"
            results.append(
                Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    volume=pos.volume,
                    direction=direction,
                )
            )
        return results

    def place_order(self, symbol: str, signal: Signal, volume: float) -> bool:
        if volume <= 0:
            return False
        order_type = mt5.ORDER_TYPE_BUY if signal.direction == "buy" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if signal.direction == "buy" else mt5.symbol_info_tick(symbol).bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": signal.stop_loss,
            "tp": signal.take_profit,
            "deviation": self.execution.max_slippage,
            "magic": self.execution.magic_number,
            "comment": "SMC-Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None:
            return False
        return result.retcode == mt5.TRADE_RETCODE_DONE
