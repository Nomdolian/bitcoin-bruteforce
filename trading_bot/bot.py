from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict

import time as time_module
import yaml

from trading_bot.config import BotConfig
from trading_bot.mt5_broker import MT5Broker
from trading_bot.news import EconomicNewsClient, is_news_blocked
from trading_bot.risk import RiskManager
from trading_bot.strategy import SMCStrategy

TIMEFRAME_MAP = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


class TradingBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.broker = MT5Broker(config.broker, config.execution)
        self.strategy = SMCStrategy(config.strategy)
        self.risk = RiskManager(config.risk)
        self.news = EconomicNewsClient(config.news)

    def run(self, poll_interval: int = 60) -> None:
        if not self.broker.connect():
            raise RuntimeError("Unable to connect to MT5")
        try:
            while True:
                self._tick()
                time_module.sleep(poll_interval)
        finally:
            self.broker.shutdown()

    def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        events = self.news.fetch_events(now)
        if is_news_blocked(events, self.config.news, now):
            return
        for symbol in self.config.strategy.symbols:
            open_positions = self.broker.open_positions(symbol=symbol)
            if not self.risk.can_trade(len(open_positions), now.date()):
                continue
            candles = self.broker.get_candles(
                symbol,
                TIMEFRAME_MAP[self.config.strategy.timeframe],
                count=200,
            )
            signal = self.strategy.generate_signal(candles)
            if signal is None:
                continue
            if not self.risk.enforce_rr(signal.entry, signal.stop_loss, signal.take_profit):
                continue
            balance = self.broker.get_balance()
            symbol_settings = self.config.symbol_settings.get(symbol, {})
            volume = self.risk.position_size(
                balance,
                signal.entry,
                signal.stop_loss,
                pip_value=symbol_settings.get("pip_value", 10.0),
                pip_size=symbol_settings.get("pip_size", 0.0001),
            )
            if volume <= 0:
                continue
            if self.broker.place_order(symbol, signal, volume):
                self.risk.record_trade(0.0)


def load_config(path: str) -> BotConfig:
    with open(path, "r", encoding="utf-8") as handle:
        raw: Dict[str, Dict] = yaml.safe_load(handle) or {}
    config = BotConfig()
    for section, values in raw.items():
        if hasattr(config, section) and isinstance(values, dict):
            section_obj = getattr(config, section)
            for key, value in values.items():
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
    return config


def dump_config(config: BotConfig) -> str:
    return yaml.safe_dump(asdict(config), sort_keys=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the MT5 SMC trading bot")
    parser.add_argument("--config", default="trading_bot/config.example.yaml")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()

    cfg = load_config(args.config)
    bot = TradingBot(cfg)
    bot.run(poll_interval=args.interval)
