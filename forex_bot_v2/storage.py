import sqlite3
from datetime import datetime, timezone
from typing import List

from forex_bot_v2.models import Event


class SQLiteEventStore:
    def __init__(self, db_path: str = "forex_events.db"):
        self.db_path = db_path

    def init_db(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                currency TEXT NOT NULL,
                impact TEXT NOT NULL,
                event_time_utc TEXT NOT NULL,
                month_key TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                analysis_sent_at TEXT,
                final_alert_sent_at TEXT,
                last_seen_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def upsert_events(self, events: List[Event]) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        count = 0
        for event in events:
            cur.execute(
                """
                INSERT INTO events (
                    source_id, title, currency, impact, event_time_utc, month_key, raw_text,
                    analysis_sent_at, final_alert_sent_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    title=excluded.title,
                    currency=excluded.currency,
                    impact=excluded.impact,
                    event_time_utc=excluded.event_time_utc,
                    month_key=excluded.month_key,
                    raw_text=excluded.raw_text,
                    last_seen_at=excluded.last_seen_at
                """,
                (
                    event.source_id,
                    event.title,
                    event.currency,
                    event.impact,
                    event.event_time_utc,
                    event.month_key,
                    event.raw_text,
                    now,
                ),
            )
            count += 1
        conn.commit()
        conn.close()
        return count

    def get_upcoming_events(self, limit: int = 5):
        self.init_db()
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT source_id, title, currency, impact, event_time_utc, analysis_sent_at, final_alert_sent_at
            FROM events
            WHERE event_time_utc >= ?
            ORDER BY event_time_utc ASC
            LIMIT ?
            """,
            (datetime.now(timezone.utc).isoformat(), limit),
        )
        rows = cur.fetchall()
        conn.close()
        return rows
