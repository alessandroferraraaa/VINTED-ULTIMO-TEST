# 🧪 VINTED BOT - TESTING GUIDE

## ✅ Quick Start (WINDOWS)

### Option 1: Automatic Test (Easiest)
```bash
RUN_TEST.bat
```
This will:
1. ✅ Install all dependencies
2. ✅ Run comprehensive tests
3. ✅ Verify database
4. ✅ Show next steps

**Expected output:**
```
[OK] Dependencies installed
🧪 TEST 1: VALIDATION FUNCTIONS
✅ 'Tuta calcio Nike Inter XL' -> Valid: True, Reason: Valid, Team: inter
✅ 'Football tracksuit Adidas Liverpool M' -> Valid: True, Reason: Valid, Team: liverpool
❌ 'Solo pantalone calcio' -> Valid: False, Reason: Not a complete tracksuit
...
[OK] Database created: vinted_bot.db
✅ ALL TESTS COMPLETED
```

---

### Option 2: Manual Testing (Step by Step)

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed requests-2.31.0 beautifulsoup4-4.12.2
```

**If error:** Make sure Python 3.8+ is installed
```bash
python --version  # Should show Python 3.8+
```

---

#### Step 2: Run Unit Tests
```bash
python test_bot.py
```

**Expected output:**
```
############################################################
# VINTED BOT - COMPREHENSIVE TEST SUITE
############################################################

============================================================
🧪 TEST 1: VALIDATION FUNCTIONS
============================================================
✅ 'Tuta calcio Nike Inter XL' -> Valid: True, Reason: Valid, Team: inter
✅ 'Football tracksuit Adidas Liverpool M' -> Valid: True, Reason: Valid, Team: liverpool
✅ 'Completo calcio Puma Barcelona S' -> Valid: True, Reason: Valid, Team: barcellona
❌ 'Solo pantalone calcio' -> Valid: False, Reason: Not a complete tracksuit
❌ 'Tuta bimbo' -> Valid: False, Reason: Forbidden keywords
❌ 'Tracksuit summer estivo' -> Valid: False, Reason: Forbidden keywords

🔍 Team Extraction:
✅ 'liverpool' -> Extracted: liverpool
✅ 'manchester city' -> Extracted: manchester city
✅ 'olympique marsiglia' -> Extracted: olympique marsiglia
✅ 'lione' -> Extracted: lione
✅ 'psg' -> Extracted: psg

🏷️ Brand Extraction:
✅ 'nike' -> Extracted: nike
✅ 'adidas' -> Extracted: adidas
✅ 'puma' -> Extracted: puma
✅ 'lotto' -> Extracted: lotto
✅ 'reebok' -> Extracted: reebok

🚫 Forbidden Keywords:
✅ Keyword 'kids' -> Detected: True
✅ Keyword 'bambino' -> Detected: True
✅ Keyword 'solo pantalone' -> Detected: True
✅ Keyword 'shorts' -> Detected: True
✅ Keyword 'training set' -> Detected: True

============================================================
🧪 TEST 2: DATABASE FUNCTIONS
============================================================
📝 Initializing database...
✅ Database initialized successfully
💾 Saving test item...
✅ Item saved
🔍 Checking if item exists...
✅ Item retrieved from database

============================================================
🧪 TEST 3: SESSION CREATION
============================================================
✅ Session created
✅ Headers: 7 headers configured

============================================================
🧪 TEST 4: WEB SCRAPING (PRODUCTION TEST)
============================================================
🔗 Fetching items from Vinted...
✅ Fetched 28 items

📋 Sample items:
1. ID: 1234567890
   Title: Tuta calcio Nike Inter M - ottime condizioni...
   Price: €25.50
   URL: https://www.vinted.it/items/1234567890
   Valid: True (Valid), Team: inter

2. ID: 1234567891
   Title: Completo Liverpool adidas XL nuovo...
   Price: €35.00
   URL: https://www.vinted.it/items/1234567891
   Valid: True (Valid), Team: liverpool

3. ID: 1234567892
   Title: Tracksuit Barcelona Puma L...
   Price: €28.99
   URL: https://www.vinted.it/items/1234567892
   Valid: True (Valid), Team: barcellona

############################################################
# ✅ ALL TESTS COMPLETED
############################################################
```

---

## 🔧 Configure Notifications

### Discord (Optional)
1. Create a Discord webhook
2. In command prompt:
```bash
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

### Telegram (Optional)
1. Get bot token from @BotFather
2. Get chat ID
3. In command prompt:
```bash
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🚀 Run the Bot

### Test Run (Stop After 1 Cycle)
```bash
python vinted_bot.py
# Press Ctrl+C after first cycle to stop
```

**Expected output:**
```
2026-01-21 22:05:23,456 - INFO - 🚀 Starting Vinted Bot...
2026-01-21 22:05:23,457 - INFO - Discord: ❌
2026-01-21 22:05:23,458 - INFO - Telegram: ❌
2026-01-21 22:05:23,459 - INFO - ✅ Database initialized

2026-01-21 22:05:23,460 - INFO - 
📍 Cycle #1 - 2026-01-21 22:05:23
2026-01-21 22:05:24,123 - INFO - 🔍 Fetching from Vinted...
2026-01-21 22:05:25,456 - INFO - 📦 Found 28 item elements
2026-01-21 22:05:25,789 - INFO - ✅ Successfully extracted 28 items
2026-01-21 22:05:25,890 - INFO - ✅ Approved: 1234567890 - inter
2026-01-21 22:05:25,891 - INFO - ✅ Approved: 1234567891 - liverpool
2026-01-21 22:05:25,892 - INFO - ✅ Approved: 1234567892 - barcellona
2026-01-21 22:05:25,893 - INFO - ❌ Rejected: 1234567893 - Forbidden keywords
2026-01-21 22:05:25,894 - INFO - 📊 Cycle: 28 scanned, 15 approved
2026-01-21 22:05:25,895 - INFO - ⏳ Next in 60s...

(Press Ctrl+C to stop)
```

---

## 📊 Database File

After running tests, check database:
```bash
ls -la vinted_bot.db
```

This file stores:
- ✅ Approved items (tracksuit + team)
- ❌ Rejected items (reason)
- 🔄 Notification history

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'requests'
**Solution:**
```bash
pip install requests beautifulsoup4
```

### Issue: No items fetched
**Causes:**
1. Network issue - check internet
2. Vinted changed HTML - needs update
3. Rate limited - wait 1 minute

**Solution:**
```bash
# Test network
ping www.vinted.it

# Test with verbose output
python -c "import requests; print(requests.get('https://www.vinted.it').status_code)"
```

### Issue: Database locked
**Solution:**
```bash
# Delete and recreate
del vinted_bot.db
python test_bot.py  # Will recreate
```

---

## ✅ Testing Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tests pass (`python test_bot.py`)
- [ ] Database created (`vinted_bot.db` exists)
- [ ] Web scraping works (items fetched from Vinted)
- [ ] Validation logic works (correct items approved/rejected)
- [ ] No errors in logs (`vinted_bot.log`)
- [ ] Bot runs continuously without crashing
- [ ] (Optional) Discord/Telegram notifications configured

---

## 📝 Files

| File | Purpose |
|------|----------|
| `vinted_bot.py` | Main bot script |
| `test_bot.py` | Comprehensive test suite |
| `RUN_TEST.bat` | Windows batch file for quick testing |
| `requirements.txt` | Python dependencies |
| `vinted_bot.db` | SQLite database (created after first run) |
| `vinted_bot.log` | Log file (created after first run) |

---

## 🎯 Next Steps

1. ✅ Run tests: `RUN_TEST.bat`
2. ✅ Configure Discord/Telegram (optional)
3. ✅ Run bot: `python vinted_bot.py`
4. ✅ Check GitHub Actions workflow (auto-runs)

**Done!** 🎉
