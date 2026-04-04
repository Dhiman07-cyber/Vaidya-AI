# VaidyaAI Telegram Bot

Interactive monitoring bot for VaidyaAI system.

## Features

- 📢 Receive real-time alerts from backend
- 📊 Query system status
- 📋 View recent logs
- ⚠️ Check recent errors
- 🔍 Interactive commands

## Setup

### 1. Get Your Telegram Chat ID

Send a message to your bot, then run:
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Look for `"chat":{"id":123456789}` in the response.

### 2. Install Dependencies

```bash
cd telegram_bot
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
BOT_WEBHOOK_PORT=8001
BACKEND_URL=http://localhost:8000
```

### 4. Run the Bot

```bash
python bot.py
```

The bot will:
- Start Telegram bot (listens for commands)
- Start webhook server on port 8001 (receives alerts from backend)

## Update Backend Configuration

Add to your `backend/.env`:
```env
# Telegram Bot Webhook (for sending alerts)
TELEGRAM_WEBHOOK_URL=http://localhost:8001/webhook
```

## Available Commands

- `/start` - Initialize bot
- `/help` - Show help message
- `/ping` - Check bot status
- `/status` - System health check
- `/logs [feature] [count]` - Get recent logs
  - Example: `/logs osce 10`
- `/errors [hours]` - Get recent errors
  - Example: `/errors 24`

## Architecture

```
VaidyaAI Backend (port 8000)
    ↓
    ├─→ Discord Webhook (instant alerts)
    └─→ Telegram Bot Webhook (port 8001)
            ↓
        Telegram Bot
            ↓
        Your Telegram App
```

## Next Steps

1. Implement database queries in bot.py (marked with TODO)
2. Add authentication for webhook endpoint
3. Add more commands as needed
4. Deploy bot to a server for 24/7 operation
