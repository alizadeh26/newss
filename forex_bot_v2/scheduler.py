import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from forex_bot_v2.analysis import build_analysis, build_empty_events_message
from forex_bot_v2.config import Settings
from forex_bot_v2.notifications import TelegramNotifier
from forex_bot_v2.scraper import ForexFactoryScraper
from forex_bot_v2.storage import SQLiteEventStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("forex_bot_v2")


class ForexBotV2:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = SQLiteEventStore(settings.db_path)
        self.notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, settings.request_timeout)
        self.scraper = ForexFactoryScraper(settings)

    def _safe_send_message(self, text: str, title: str) -> None:
        try:
            self.notifier.send_message(text)
            logger.info("Dispatch message sent for %s", title)
        except Exception as exc:
            logger.exception("Failed to send Telegram alert for %s: %s", title, exc)

    def run_monthly_sync(self) -> None:
        self.store.init_db()
        try:
            html = self.scraper.fetch_calendar_html()
            events = self.scraper.parse_calendar_html(
                html,
                month_key=f"{datetime.now(timezone.utc).year}-{datetime.now(timezone.utc).month:02d}",
            )
            self.store.upsert_events(events)
            logger.info("Monthly sync stored %d events", len(events))
        except Exception as exc:
            logger.exception("Monthly sync failed: %s", exc)

    def run_dispatch(self) -> None:
        self.store.init_db()
        try:
            html = self.scraper.fetch_calendar_html()
            events = self.scraper.parse_calendar_html(
                html,
                month_key=f"{datetime.now(timezone.utc).year}-{datetime.now(timezone.utc).month:02d}",
            )
            self.store.upsert_events(events)
            logger.info("Dispatch refreshed %d events", len(events))
        except Exception as exc:
            logger.exception("Dispatch refresh failed: %s", exc)

        rows = self.store.get_upcoming_events(limit=5)
        if not rows:
            self._safe_send_message(build_empty_events_message(), "no-upcoming-events")
            return

        for row in rows:
            text = build_analysis(
                title=row["title"],
                currency=row["currency"],
                impact=row["impact"],
                event_time_utc=row["event_time_utc"],
                stage="prepare",
            )
            self._safe_send_message(text, row["title"])

    def export_json(self, output_path: str) -> None:
        self.store.init_db()
        rows = self.store.get_upcoming_events(limit=100)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump([dict(row) for row in rows], handle, ensure_ascii=False, indent=2)
        logger.info("Exported %d events to %s", len(rows), output_path)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Forex Bot v2")
    parser.add_argument("command", choices=["monthly-sync", "dispatch", "export-json"], nargs="?", default="dispatch")
    parser.add_argument("--output", default="events_export.json")
    return parser


def main() -> None:
    parser = build_cli()
    args = parser.parse_args()
    settings = Settings.from_env(os.environ)
    bot = ForexBotV2(settings)
    if args.command == "monthly-sync":
        bot.run_monthly_sync()
    elif args.command == "dispatch":
        bot.run_dispatch()
    elif args.command == "export-json":
        bot.export_json(args.output)


if __name__ == "__main__":
    main()
