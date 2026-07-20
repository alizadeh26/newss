import requests


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, request_timeout: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.request_timeout = request_timeout

    def send_message(self, text: str) -> dict:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=self.request_timeout)
        response.raise_for_status()
        return response.json()
