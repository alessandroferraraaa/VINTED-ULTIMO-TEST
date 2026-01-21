@echo off
echo.
echo ============================================================
echo  VINTED BOT - COMPLETE TEST SUITE
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.8+
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [2/4] Running comprehensive tests...
python test_bot.py
if errorlevel 1 (
    echo [ERROR] Tests failed
    pause
    exit /b 1
)
echo.

echo [3/4] Checking database...
if exist vinted_bot.db (
    echo [OK] Database created: vinted_bot.db
) else (
    echo [WARNING] Database not created yet
)
echo.

echo [4/4] Bot is ready!
echo.
echo ============================================================
echo  Next steps:
echo  1. Set Discord webhook: set DISCORD_WEBHOOK_URL=your_url
echo  2. Set Telegram bot: set TELEGRAM_BOT_TOKEN=your_token
echo  3. Set Telegram chat: set TELEGRAM_CHAT_ID=your_id
echo  4. Run: python vinted_bot.py
echo ============================================================
echo.

pause
