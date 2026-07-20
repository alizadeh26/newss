# Forex Bot Pro

This repository contains a modular forex news bot that scrapes the Forex Factory calendar, stores relevant events, and sends Telegram alerts.

## Features
- Scrapes calendar data with retry handling
- Stores events in SQLite
- Sends Telegram alerts
- Supports monthly sync and dispatch jobs
- Includes basic tests for core behavior

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create environment variables:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
3. Run:
   ```bash
   python forex_bot_v2/scheduler.py monthly-sync
   python forex_bot_v2/scheduler.py dispatch
   ```
