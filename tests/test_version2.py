import os
import tempfile
import unittest

from forex_bot_v2.analysis import build_analysis, confidence_score, event_weight
from forex_bot_v2.config import Settings
from forex_bot_v2.models import Event
from forex_bot_v2.storage import SQLiteEventStore


class SettingsTests(unittest.TestCase):
    def test_requires_telegram_credentials(self):
        with self.assertRaises(ValueError):
            Settings.from_env({"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""})

    def test_parses_target_lists(self):
        settings = Settings.from_env(
            {
                "TELEGRAM_BOT_TOKEN": "token",
                "TELEGRAM_CHAT_ID": "123",
                "TARGET_CURRENCIES": "USD,EUR",
                "TARGET_IMPACTS": "High,Medium",
            }
        )
        self.assertEqual(settings.target_currencies, {"USD", "EUR"})
        self.assertEqual(settings.target_impacts, {"High", "Medium"})


class AnalysisTests(unittest.TestCase):
    def test_confidence_and_weight_are_reasonable(self):
        score = event_weight("NFP Non-Farm Payrolls", "High")
        confidence = confidence_score("NFP Non-Farm Payrolls", "High", "final")
        self.assertGreater(score, 20)
        self.assertGreater(confidence, 70)

    def test_build_analysis_contains_stage_labels(self):
        text = build_analysis(
            title="CPI Inflation",
            currency="USD",
            impact="High",
            event_time_utc="2026-07-20T15:30:00+00:00",
            stage="prepare",
        )
        self.assertIn("Preparation alert", text)
        self.assertIn("CPI Inflation", text)


class StorageTests(unittest.TestCase):
    def test_upsert_and_read_back_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteEventStore(db_path=os.path.join(tmpdir, "events.db"))
            store.init_db()
            event = Event(
                source_id="USD|High|CPI|2030-07-20T15:30:00+00:00",
                title="CPI Inflation",
                currency="USD",
                impact="High",
                event_time_utc="2030-07-20T15:30:00+00:00",
                month_key="2026-07",
                raw_text="CPI Inflation",
            )
            store.upsert_events([event])
            rows = store.get_upcoming_events(limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "CPI Inflation")


if __name__ == "__main__":
    unittest.main()
