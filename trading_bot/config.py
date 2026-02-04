from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Dict, List, Optional


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01
    max_daily_loss: float = 0.03
    max_open_positions: int = 2
    max_trades_per_day: int = 5
    min_rr: float = 1.5


@dataclass
class StrategyConfig:
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframe: str = "M15"
    higher_timeframe: str = "H1"
    ema_fast: int = 20
    ema_slow: int = 50
    liquidity_lookback: int = 8
    fvg_lookback: int = 5
    order_block_lookback: int = 12


@dataclass
class NewsConfig:
    enabled: bool = True
    calendar_provider: str = "tradingeconomics"
    impact_levels: List[str] = field(default_factory=lambda: ["high", "medium"])
    block_minutes_before: int = 30
    block_minutes_after: int = 30
    timezone: str = "UTC"


@dataclass
class ExecutionConfig:
    lot_size: float = 0.1
    max_slippage: int = 10
    allow_weekends: bool = False
    trading_start: time = time(6, 0)
    trading_end: time = time(20, 0)
    magic_number: int = 202409


@dataclass
class BrokerConfig:
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None
    path: Optional[str] = None


@dataclass
class BotConfig:
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    news: NewsConfig = field(default_factory=NewsConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    symbol_settings: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {"EURUSD": {"pip_value": 10.0, "pip_size": 0.0001}}
    )
