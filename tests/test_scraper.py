import unittest

from forex_bot_v2.config import Settings
from forex_bot_v2.scraper import ForexFactoryScraper


class ScraperTests(unittest.TestCase):
    def test_parse_calendar_html_returns_expected_event(self):
        html = """
        <table class="calendar__table">
          <tr class="calendar__row">
            <td class="calendar__cell calendar__date">Mon Jul 21</td>
            <td class="calendar__cell calendar__time">10:00</td>
            <td class="calendar__cell calendar__currency">USD</td>
            <td class="calendar__cell calendar__event">CPI Inflation</td>
            <td class="calendar__cell calendar__impact"><span class="impact--high">High</span></td>
          </tr>
        </table>
        """
        settings = Settings.from_env({"TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "123"})
        scraper = ForexFactoryScraper(settings)
        events = scraper.parse_calendar_html(html, month_key="2026-07")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "CPI Inflation")
        self.assertEqual(events[0].impact, "High")
        self.assertEqual(events[0].currency, "USD")


if __name__ == "__main__":
    unittest.main()
