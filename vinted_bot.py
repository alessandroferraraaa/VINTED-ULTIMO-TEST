#!/usr/bin/env python3
"""
VINTED FOOTBALL TRACKSUIT BOT 🔍⚽
Monitor real-time adult complete football tracksuits (jacket + long pants)
Standalone version: Handles dependencies automatically
"""

import sys
import subprocess

# Auto-install dependencies
try:
    import requests
except ImportError:
    print("[INSTALLING] requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[INSTALLING] beautifulsoup4...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

import json
import time
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    "VINTED_URL": "https://www.vinted.it/items?search_text=tuta%20calcio&order=newest_first",
    "CHECK_INTERVAL": 60,
    "DB_NAME": "vinted_bot.db",
    "LOG_LEVEL": logging.INFO,
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
        has_jacket = any(word in title_lower for word in ["felpa", "giacca", "jacket", "hoodie"])
        has_pants = any(word in title_lower for word in ["pantalone", "pants", "trousers"])
        if not (has_jacket and has_pants):
            return False, "Not a complete tracksuit"
    
    team = check_team(title)
    if not team:
        return False, "Team not approved"
    
    return True, "Valid"

# ============================================================================
# WEB SCRAPING
# ============================================================================

def create_session():
    """Create requests session with proper headers"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    return session

def fetch_items(session) -> List[Dict]:
    """Fetch items from Vinted using requests + BeautifulSoup"""
    items = []
    try:
        logger.info(f"🔍 Fetching from Vinted...")
        response = session.get(CONFIG["VINTED_URL"], timeout=15)
        
        if response.status_code != 200:
            logger.error(f"HTTP Error {response.status_code}")
            return items
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        item_elements = soup.find_all('div', {'class': re.compile('.*item.*')})
        logger.info(f"📦 Found {len(item_elements)} item elements")
        
        for elem in item_elements[:30]:
            try:
                title_elem = elem.find('span', {'class': re.compile('.*title.*')})
                if not title_elem:
                    title_elem = elem.find('h2')
                
                title = title_elem.text.strip() if title_elem else None
                
                link_elem = elem.find('a', href=True)
                url = link_elem.get('href') if link_elem else None
                
                price_elem = elem.find('span', {'class': re.compile('.*price.*')})
                price = price_elem.text.strip() if price_elem else "N/A"
                
                if not title or not url:
                    continue
                
                item_id = url.split('/')[-1] if '/' in url else None
                
                if not item_id:
                    continue
                
                item = {
                    "id": item_id,
                    "title": title,
                    "price": price,
                    "url": url if url.startswith('http') else f"https://www.vinted.it{url}"
                }
                
                items.append(item)
                logger.debug(f"Found item: {item_id} - {title[:50]}")
            
            except Exception as e:
                logger.debug(f"Error parsing item: {e}")
                continue
        
        logger.info(f"✅ Successfully extracted {len(items)} items")
    
    except Exception as e:
        logger.error(f"Error fetching: {e}")
    
    return items

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

def save_item(item: Dict, status: str, team: Optional[str] = None, reason: Optional[str] = None):
    """Save item to database"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO items (item_id, title, price, team, brand, status, vinted_url, reason_rejected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"),
            item.get("title"),
            item.get("price"),
            team,
            check_brand(item.get("title", "")),
            status,
            item.get("url"),
            reason,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB save error: {e}")

# ============================================================================
# NOTIFICATIONS
# ============================================================================

def send_discord(item: Dict, team: str):
    """Send Discord notification"""
    if not CONFIG["DISCORD_WEBHOOK_URL"]:
        return
    
    try:
        data = {
            "embeds": [{
                "title": item.get("title", "N/A")[:256],
                "description": f"**Team:** {team.upper()}\n**Price:** {item.get('price', 'N/A')}",
                "color": 65280,
                "url": item.get("url", ""),
                "fields": [
                    {"name": "Brand", "value": check_brand(item.get("title", "")) or "N/A", "inline": True},
                    {"name": "Item ID", "value": item.get("id", "N/A"), "inline": True},
                ],
            }]
        }
        response = requests.post(CONFIG["DISCORD_WEBHOOK_URL"], json=data, timeout=5)
        if response.status_code == 204:
            logger.info("✅ Discord sent")
    except Exception as e:
        logger.warning(f"Discord error: {e}")

def send_telegram(item: Dict, team: str):
    """Send Telegram notification"""
    if not CONFIG["TELEGRAM_BOT_TOKEN"] or not CONFIG["TELEGRAM_CHAT_ID"]:
        return
    
    try:
        text = f"🎯 *TRACKSUIT*\n*{item.get('title', 'N/A')}*\n👥 {team.upper()}\n💰 {item.get('price', 'N/A')}\n🔗 [View]({item.get('url', '')})"
        url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
        requests.post(url, json={
            "chat_id": CONFIG["TELEGRAM_CHAT_ID"],
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=5)
        logger.info("✅ Telegram sent")
    except Exception as e:
        logger.warning(f"Telegram error: {e}")

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
            
            items = fetch_items(session)
            
            if not items:
                logger.warning("No items found")
                time.sleep(CONFIG["CHECK_INTERVAL"])
                continue
            
            approved = 0
            for item in items:
                item_id = item.get("id")
                
                if item_exists(item_id):
                    logger.debug(f"Already processed: {item_id}")
                    continue
                
                is_valid, reason = is_valid_tracksuit(item.get("title", ""))
                
                if is_valid:
                    team = check_team(item.get("title", ""))
                    approved += 1
                    save_item(item, "approved", team)
                    logger.info(f"✅ Approved: {item_id} - {team}")
                    send_discord(item, team)
                    send_telegram(item, team)
                else:
                    save_item(item, "rejected", reason=reason)
                    logger.info(f"❌ Rejected: {item_id} - {reason}")
            
            logger.info(f"📊 Cycle: {len(items)} scanned, {approved} approved")
            logger.info(f"⏳ Next in {CONFIG['CHECK_INTERVAL']}s...\n")
            
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
