#!/usr/bin/env python3
"""
VINTED FOOTBALL TRACKSUIT BOT 🔍⚽
Monitor real-time adult complete football tracksuits (jacket + long pants)
Browser-like requests to bypass anti-scraping
"""

import sys
import subprocess

try:
    import requests
except ImportError:
    print("[INSTALLING] requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

import json
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "DISCORD_WEBHOOK_URL": "",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "CHECK_INTERVAL": 60,
    "DB_NAME": "vinted_bot.db",
    "LOG_LEVEL": logging.INFO,
    "RETRY_ATTEMPTS": 3,
    "RETRY_DELAY": 2,
}

# ============================================================================
# LOGGER SETUP
# ============================================================================

logging.basicConfig(
    level=CONFIG["LOG_LEVEL"],
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("vinted_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA VALIDATION
# ============================================================================

APPROVED_TEAMS = {
    "liverpool", "manchester city", "olympique marsiglia", "lione", "psg",
    "borussia dortmund", "bayern monaco", "inter", "manchester united",
    "argentina", "francia", "spagna", "arsenal", "tottenham",
    "real madrid", "barcellona", "atletico madrid", "chelsea",
    "napoli", "roma", "juventus", "ac milan"
}

APPROVED_BRANDS = {
    "nike", "adidas", "puma", "lotto", "reebok", "umbro", "kappa"
}

ALLOWED_SIZES = {"XS", "S", "M", "L", "XL"}

FORBIDDEN_KEYWORDS = {
    "solo pantalone", "solo felpa", "joggers", "bottom", "piece 1",
    "short", "shorts", "maillot", "kids", "junior", "academy",
    "enfant", "garçon", "bambino", "child", "children", "youth",
    "training set", "kit gara", "summer", "estivo", "tees",
    "polo", "shirt", "maglietta", "canotta", "singlet"
}

FORBIDDEN_AGE_KEYWORDS = {
    "anni", "years", "age", "mesi", "months", "cm", "taglia bimbo",
    "kids size", "child size", "ragazzo", "ragazza", "16 anni"
}

APPROVED_COMBINATIONS = {
    "tuta calcio", "tuta da calcio", "tracksuit", "football tracksuit",
    "survêtement", "ensemble", "completo", "set completo"
}

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize SQLite database for tracking items"""
    conn = sqlite3.connect(CONFIG["DB_NAME"])
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            price TEXT,
            team TEXT,
            brand TEXT,
            status TEXT,
            vinted_url TEXT,
            reason_rejected TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def check_forbidden_keywords(text: str) -> bool:
    """Return True if text contains forbidden keywords"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in text_lower:
            return True
    
    for keyword in FORBIDDEN_AGE_KEYWORDS:
        if keyword in text_lower:
            return True
    
    return False

def check_team(title: str) -> Optional[str]:
    """Extract and validate team name"""
    text = title.lower()
    
    for team in APPROVED_TEAMS:
        if team in text:
            return team
    
    return None

def check_brand(title: str) -> Optional[str]:
    """Extract and validate brand name"""
    text = title.lower()
    
    for brand in APPROVED_BRANDS:
        if brand in text:
            return brand
    
    return None

def is_valid_tracksuit(title: str) -> tuple:
    """Validate if title matches tracksuit criteria"""
    title_lower = title.lower()
    
    if check_forbidden_keywords(title_lower):
        return False, "Forbidden keywords"
    
    has_approved_combo = any(combo in title_lower for combo in APPROVED_COMBINATIONS)
    
    if not has_approved_combo:
        has_jacket = any(word in title_lower for word in ["felpa", "giacca", "jacket", "hoodie", "tuta"])
        has_pants = any(word in title_lower for word in ["pantalone", "pants", "trousers", "tuta"])
        if not (has_jacket and has_pants):
            return False, "Not a complete tracksuit"
    
    team = check_team(title)
    if not team:
        return False, "Team not approved"
    
    return True, "Valid"

# ============================================================================
# WEB SCRAPING
# ============================================================================

def get_browser_headers():
    """Get realistic browser headers"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Referer": "https://www.vinted.it/",
    }

def create_session():
    """Create requests session with realistic settings"""
    session = requests.Session()
    session.headers.update(get_browser_headers())
    session.timeout = 15
    return session

def fetch_items_with_retry(session, url, params, max_retries=3):
    """Fetch items from Vinted with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Attempt {attempt + 1}/{max_retries} - Fetching {url}...")
            
            response = session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                logger.warning(f"⏸️ Rate limited! Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if response.status_code == 403:
                logger.warning(f"🚫 Forbidden (403) - Vinted blocking requests. Waiting 120s...")
                time.sleep(120)
                continue
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(CONFIG["RETRY_DELAY"] * (attempt + 1))
                continue
            
            try:
                data = response.json()
                items = data.get("items", [])
                if items:
                    logger.info(f"✅ Successfully fetched {len(items)} items")
                    return items
                else:
                    logger.debug("No items in response")
                    return []
            except json.JSONDecodeError:
                logger.warning("❌ Invalid JSON response")
                if attempt < max_retries - 1:
                    time.sleep(CONFIG["RETRY_DELAY"])
                continue
        
        except requests.exceptions.ConnectTimeout:
            logger.warning("⏱️ Connection timeout")
            if attempt < max_retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
        except requests.exceptions.ReadTimeout:
            logger.warning("⏱️ Read timeout")
            if attempt < max_retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
        except Exception as e:
            logger.warning(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
    
    logger.error("❌ All retry attempts failed")
    return []

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def item_exists(item_id: str) -> bool:
    """Check if item already recorded"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM items WHERE item_id = ?", (item_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except:
        return False

def save_item(item_id: str, title: str, price: str, status: str, team: Optional[str] = None, reason: Optional[str] = None):
    """Save item to database"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO items (item_id, title, price, team, brand, status, reason_rejected)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            title,
            price,
            team,
            check_brand(title),
            status,
            reason,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB save error: {e}")

# ============================================================================
# NOTIFICATIONS
# ============================================================================

def send_discord(item_id: str, title: str, price: str, team: str):
    """Send Discord notification"""
    if not CONFIG["DISCORD_WEBHOOK_URL"]:
        return
    
    try:
        data = {
            "embeds": [{"title": title[:256], "description": f"👥 **{team}** | 💰 **{price}**", "color": 65280}]
        }
        requests.post(CONFIG["DISCORD_WEBHOOK_URL"], json=data, timeout=5)
        logger.info("✅ Discord sent")
    except:
        pass

def send_telegram(item_id: str, title: str, price: str, team: str):
    """Send Telegram notification"""
    if not CONFIG["TELEGRAM_BOT_TOKEN"] or not CONFIG["TELEGRAM_CHAT_ID"]:
        return
    
    try:
        text = f"🎯 *{title}*\n👥 {team}\n💰 {price}"
        url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
        requests.post(url, json={"chat_id": CONFIG["TELEGRAM_CHAT_ID"], "text": text, "parse_mode": "Markdown"}, timeout=5)
        logger.info("✅ Telegram sent")
    except:
        pass

# ============================================================================
# MAIN LOOP
# ============================================================================

def monitor_vinted():
    """Main monitoring loop"""
    logger.info("🚀 Starting Vinted Bot...")
    logger.info(f"Discord: {'✅' if CONFIG['DISCORD_WEBHOOK_URL'] else '❌'}")
    logger.info(f"Telegram: {'✅' if CONFIG['TELEGRAM_BOT_TOKEN'] else '❌'}")
    
    init_database()
    session = create_session()
    cycle = 0
    
    while True:
        try:
            cycle += 1
            logger.info(f"\n📍 Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Try multiple search endpoints
            endpoints = [
                ("https://www.vinted.it/api/v2/items", {"search_text": "tuta calcio", "order": "newest_first", "per_page": 30}),
                ("https://www.vinted.com/api/v2/items", {"search_text": "tuta calcio", "order": "newest_first", "per_page": 30}),
            ]
            
            total_found = 0
            total_approved = 0
            
            for endpoint, params in endpoints:
                items = fetch_items_with_retry(session, endpoint, params)
                
                if not items:
                    continue
                
                total_found += len(items)
                
                for item in items:
                    item_id = str(item.get("id", ""))
                    title = item.get("title", "")
                    price = item.get("price", "N/A")
                    
                    if not item_id or not title:
                        continue
                    
                    if item_exists(item_id):
                        logger.debug(f"Already processed: {item_id}")
                        continue
                    
                    is_valid, reason = is_valid_tracksuit(title)
                    
                    if is_valid:
                        team = check_team(title)
                        total_approved += 1
                        save_item(item_id, title, price, "approved", team)
                        logger.info(f"✅ {item_id} | {title} | {team}")
                        send_discord(item_id, title, price, team)
                        send_telegram(item_id, title, price, team)
                    else:
                        save_item(item_id, title, price, "rejected", reason=reason)
                        logger.debug(f"❌ {item_id} | {reason}")
            
            logger.info(f"📊 Found: {total_found} | Approved: {total_approved}")
            logger.info(f"⏳ Next check in {CONFIG['CHECK_INTERVAL']}s\n")
            
            time.sleep(CONFIG["CHECK_INTERVAL"])
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Bot stopped")
            break
        except Exception as e:
            logger.error(f"💥 Error: {e}")
            time.sleep(CONFIG["CHECK_INTERVAL"])

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    monitor_vinted()
