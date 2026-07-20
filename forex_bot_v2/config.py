import os
from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    db_path: str = "forex_events.db"
    forex_factory_month_url: str = "https://www.forexfactory.com/calendar"
    forex_factory_timezone: str = "America/New_York"
    target_timezone: str = "UTC"
    request_timeout: int = 30
    alert_before_minutes: int = 10
    prepare_before_minutes: int = 60
    target_currencies: Set[str] = field(default_factory=lambda: {"USD", "EUR", "GBP"})
    target_impacts: Set[str] = field(default_factory=lambda: {"Medium", "High"})
    telegram_offset_file: str = "telegram_offset.txt"
    user_agent: str = "Mozilla/5.0"

    @classmethod
    def from_env(cls, env: Dict[str, str] | None = None) -> "Settings":
        env = env or os.environ
        token = env.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = env.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

        def parse_csv(value: str, default: Set[str]) -> Set[str]:
            if not value:
                return default
            return {item.strip() for item in value.split(",") if item.strip()}

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            db_path=env.get("DB_PATH", "forex_events.db"),
            forex_factory_month_url=env.get("FOREX_FACTORY_MONTH_URL", "https://www.forexfactory.com/calendar"),
            forex_factory_timezone=env.get("FOREX_FACTORY_TIMEZONE", "America/New_York"),
            target_timezone=env.get("TARGET_TIMEZONE", "UTC"),
            request_timeout=int(env.get("REQUEST_TIMEOUT", "30")),
            alert_before_minutes=int(env.get("ALERT_BEFORE_MINUTES", "10")),
            prepare_before_minutes=int(env.get("PREPARE_BEFORE_MINUTES", "60")),
            target_currencies=parse_csv(env.get("TARGET_CURRENCIES", "USD,EUR,GBP"), {"USD", "EUR", "GBP"}),
            target_impacts=parse_csv(env.get("TARGET_IMPACTS", "Medium,High"), {"Medium", "High"}),
            telegram_offset_file=env.get("TELEGRAM_OFFSET_FILE", "telegram_offset.txt"),
            user_agent=env.get("USER_AGENT", "Mozilla/5.0"),
        )
