from dataclasses import dataclass


@dataclass
class Event:
    source_id: str
    title: str
    currency: str
    impact: str
    event_time_utc: str
    month_key: str
    raw_text: str
