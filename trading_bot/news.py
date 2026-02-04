from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional
import os

import requests

from trading_bot.config import NewsConfig


@dataclass(frozen=True)
class EconomicEvent:
    title: str
    country: str
    impact: str
    time: datetime
    source: str


def _normalize_impact(raw: str) -> str:
    value = raw.strip().lower()
    if "high" in value:
        return "high"
    if "medium" in value or "moderate" in value:
        return "medium"
    if "low" in value:
        return "low"
    return value


class EconomicNewsClient:
    def __init__(self, config: NewsConfig) -> None:
        self.config = config

    def fetch_events(self, now: Optional[datetime] = None) -> List[EconomicEvent]:
        if not self.config.enabled:
            return []
        provider = self.config.calendar_provider.lower()
        if provider == "tradingeconomics":
            return self._fetch_trading_economics(now)
        return []

    def _fetch_trading_economics(self, now: Optional[datetime]) -> List[EconomicEvent]:
        api_key = os.getenv("TRADING_ECONOMICS_API_KEY")
        if not api_key:
            return []
        if now is None:
            now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=3)).strftime("%Y-%m-%d")
        url = "https://api.tradingeconomics.com/calendar"
        response = requests.get(
            url,
            params={"c": api_key, "d1": start, "d2": end},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        events: List[EconomicEvent] = []
        for item in payload:
            impact = _normalize_impact(item.get("Importance", ""))
            events.append(
                EconomicEvent(
                    title=item.get("Event", ""),
                    country=item.get("Country", ""),
                    impact=impact,
                    time=datetime.fromisoformat(item.get("Date")).astimezone(
                        timezone.utc
                    ),
                    source="tradingeconomics",
                )
            )
        return events


def is_news_blocked(
    events: Iterable[EconomicEvent],
    config: NewsConfig,
    now: Optional[datetime] = None,
) -> bool:
    if not config.enabled:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    impacts = {impact.lower() for impact in config.impact_levels}
    window_before = timedelta(minutes=config.block_minutes_before)
    window_after = timedelta(minutes=config.block_minutes_after)
    for event in events:
        if event.impact.lower() not in impacts:
            continue
        if event.time - window_before <= now <= event.time + window_after:
            return True
    return False
