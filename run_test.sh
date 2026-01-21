#!/bin/bash

echo ""
echo "============================================================"
echo " VINTED BOT - COMPLETE TEST SUITE (Linux/Mac)"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found! Install Python 3.8+"
    exit 1
fi

echo "[1/4] Installing dependencies..."
pip3 install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"
echo ""

echo "[2/4] Running comprehensive tests..."
python3 test_bot.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Tests failed"
    exit 1
fi
echo ""

echo "[3/4] Checking database..."
if [ -f vinted_bot.db ]; then
    echo "[OK] Database created: vinted_bot.db"
else
    echo "[WARNING] Database not created yet"
fi
echo ""

echo "[4/4] Bot is ready!"
echo ""
echo "============================================================"
echo " Next steps:"
echo " 1. Export Discord webhook: export DISCORD_WEBHOOK_URL=your_url"
echo " 2. Export Telegram bot: export TELEGRAM_BOT_TOKEN=your_token"
echo " 3. Export Telegram chat: export TELEGRAM_CHAT_ID=your_id"
echo " 4. Run: python3 vinted_bot.py"
echo "============================================================"
echo ""
