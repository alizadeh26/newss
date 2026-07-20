import logging
import re
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from forex_bot_v2.config import Settings
from forex_bot_v2.models import Event

logger = logging.getLogger("forex_bot_v2.scraper")


class ForexFactoryScraper:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    def fetch_calendar_html(self) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                response = self.session.get(self.settings.forex_factory_month_url, timeout=self.settings.request_timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Scrape attempt %s failed: %s", attempt, exc)
        raise RuntimeError(f"Failed to fetch calendar after 3 attempts: {last_error}")

    def parse_calendar_html(self, html: str, month_key: str) -> List[Event]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.calendar__table")
        if not table:
            logger.warning("Calendar table not found")
            return []

        rows = table.select("tr.calendar__row, tr[class*='calendar__row']")
        if not rows:
            rows = table.find_all("tr")

        current_date_text = ""
        current_time_text = ""
        events: List[Event] = []

        for row in rows:
            row_classes = " ".join(row.get("class", []))
            if "calendar__row--grey" in row_classes:
                continue

            date_text = self._extract_text(row, ["td.calendar__cell.calendar__date", "td.calendar__date", "td[class*='date']"])
            time_text = self._extract_text(row, ["td.calendar__cell.calendar__time", "td.calendar__time", "td[class*='time']"])
            currency = self._extract_text(row, ["td.calendar__cell.calendar__currency", "td.calendar__currency", "td[class*='currency']"])
            title = self._extract_text(row, ["td.calendar__cell.calendar__event", "td.calendar__event", "td[class*='event']"])
            impact = self._infer_impact(row)

            if date_text:
                current_date_text = date_text
            if time_text:
                current_time_text = time_text

            if not currency or currency not in self.settings.target_currencies:
                continue
            if not title or impact not in self.settings.target_impacts:
                continue
            if not current_date_text or not current_time_text:
                continue

            event_dt = self._parse_datetime(current_date_text, current_time_text)
            if not event_dt:
                continue

            event = Event(
                source_id=f"{currency}|{impact}|{title}|{event_dt.isoformat()}",
                title=title,
                currency=currency,
                impact=impact,
                event_time_utc=event_dt.isoformat(),
                month_key=month_key,
                raw_text=" ".join(row.stripped_strings),
            )
            events.append(event)

        events.sort(key=lambda event: event.event_time_utc)
        return events

    def _extract_text(self, row, selectors: List[str]) -> str:
        for selector in selectors:
            cell = row.select_one(selector)
            if cell:
                text = " ".join(cell.stripped_strings).strip()
                if text:
                    return text
        return ""

    def _infer_impact(self, row) -> str:
        for selector in ["td.calendar__cell.calendar__impact", "td.calendar__impact", "td[class*='impact']"]:
            cell = row.select_one(selector)
            if not cell:
                continue
            html = str(cell).lower()
            classes = " ".join(cell.get("class", [])) if hasattr(cell, "get") else ""
            lowered = f"{html} {classes}".lower()
            if any(token in lowered for token in ["high", "icon--ff-impact-red", "impact--high", "calendar__impact--high"]):
                return "High"
            if any(token in lowered for token in ["medium", "med", "icon--ff-impact-ora", "impact--medium", "calendar__impact--medium"]):
                return "Medium"
        return "Low"

    def _parse_datetime(self, date_text: str, time_text: str) -> Optional[datetime]:
        if not date_text or not time_text:
            return None

        date_text = re.sub(r"\s+", " ", date_text.strip())
        time_text = re.sub(r"\s+", "", time_text.strip().lower())
        if any(token in time_text for token in ["all day", "tentative", "day"]):
            return None

        source_tz = ZoneInfo(self.settings.forex_factory_timezone)
        target_tz = ZoneInfo(self.settings.target_timezone)
        date_formats = ["%a %b %d %Y", "%b %d %Y", "%a%b %d %Y", "%a %b %d", "%b %d"]
        time_formats = ["%I:%M%p", "%H:%M"]

        candidates = []
        for date_format in date_formats:
            for time_format in time_formats:
                try:
                    if "%Y" in date_format:
                        raw = f"{date_text} {time_text}"
                        fmt = f"{date_format} {time_format}"
                    else:
                        raw = f"{date_text} {datetime.now(source_tz).year} {time_text}"
                        fmt = f"{date_format} %Y {time_format}"
                    parsed = datetime.strptime(raw, fmt).replace(tzinfo=source_tz)
                    candidates.append(parsed)
                except Exception:
                    continue

        if not candidates:
            return None

        now_source = datetime.now(source_tz)
        best = min(candidates, key=lambda value: abs((value - now_source).total_seconds()))
        if best.month == 12 and now_source.month == 1:
            best = best.replace(year=now_source.year - 1)
        elif best.month == 1 and now_source.month == 12:
            best = best.replace(year=now_source.year + 1)
        return best.astimezone(target_tz)
