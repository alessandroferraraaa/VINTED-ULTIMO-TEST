"""
VINTED FOOTBALL TRACKSUIT BOT 🔍⚽
Monitor real-time adult complete football tracksuits (jacket + long pants)
Strict filters: sizes S/M/L/XL only, approved teams/brands only
Author: Advanced Bot Builder
GitHub: https://github.com/alessandroferraraaa/VINTED-ULTIMO-TEST
"""

import requests
import json
import time
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
from pathlib import Path
import threading

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # DISCORD WEBHOOK (read from environment or config)
    "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
    
    # TELEGRAM (read from environment or config)
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    
    # VINTED PARAMETERS
    "VINTED_URLS": [
        "https://www.vinted.it/api/v2/catalog/items",
        "https://www.vinted.de/api/v2/catalog/items",
        "https://www.vinted.fr/api/v2/catalog/items",
        "https://www.vinted.es/api/v2/catalog/items",
        "https://www.vinted.nl/api/v2/catalog/items",
        "https://www.vinted.be/api/v2/catalog/items",
    ],
    
    # MONITOR FREQUENCY (seconds)
    "CHECK_INTERVAL": 60,
    
    # DATABASE
    "DB_NAME": "vinted_bot.db",
    
    # LOGLEVEL
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

# FORBIDDEN KEYWORDS
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

ACCEPTABLE_CONDITIONS = {
    "Ottime condizioni",
    "Nuovo senza cartellino",
    "Nuovo con cartellino"
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
            item_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price REAL,
            team TEXT,
            brand TEXT,
            size TEXT,
            condition TEXT,
            image_url TEXT,
            vinted_url TEXT,
            status TEXT,
            reason_rejected TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_at DATETIME
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notified (
            item_id INTEGER PRIMARY KEY,
            notification_type TEXT,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def check_size(size: str) -> bool:
    """Validate size: only S, M, L, XL allowed"""
    if not size:
        return False
    
    normalized = size.strip().upper()
    
    # Reject if contains age/kid keywords
    if any(keyword in normalized.lower() for keyword in FORBIDDEN_AGE_KEYWORDS):
        return False
    
    return normalized in ALLOWED_SIZES

def check_forbidden_keywords(text: str) -> bool:
    """Return True if text contains forbidden keywords"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in text_lower:
            logger.debug(f"🚫 Forbidden keyword found: '{keyword}'")
            return True
    
    for keyword in FORBIDDEN_AGE_KEYWORDS:
        if keyword in text_lower:
            logger.debug(f"🚫 Age keyword found: '{keyword}'")
            return True
    
    return False

def check_team(title: str, description: str = "") -> Optional[str]:
    """Extract and validate team name"""
    text = (title + " " + description).lower()
    
    for team in APPROVED_TEAMS:
        if team in text:
            return team
    
    return None

def check_brand(title: str, description: str = "") -> Optional[str]:
    """Extract and validate brand name"""
    text = (title + " " + description).lower()
    
    for brand in APPROVED_BRANDS:
        if brand in text:
            return brand
    
    return None

def is_complete_tracksuit(item: Dict) -> tuple[bool, str]:
    """
    Strictly validate if item is a complete tracksuit (jacket + long pants)
    Returns (is_valid, reason)
    """
    title = item.get("title", "").lower()
    description = item.get("description", "").lower()
    
    # Check forbidden keywords first
    if check_forbidden_keywords(title) or check_forbidden_keywords(description):
        return False, "Contains forbidden keywords"
    
    # Check for approved combination keywords
    has_approved_combo = any(combo in title or combo in description 
                            for combo in APPROVED_COMBINATIONS)
    
    if not has_approved_combo:
        # Check minimal requirements
        has_jacket = any(word in title for word in ["felpa", "giacca", "jacket", "hoodie"])
        has_pants = any(word in title for word in ["pantalone", "pants", "trousers"])
        
        if not (has_jacket and has_pants):
            return False, "Not a complete tracksuit (missing jacket or pants)"
    
    # Size validation
    size = item.get("size_title", "").strip()
    if not check_size(size):
        return False, f"Size '{size}' not allowed (only S/M/L/XL for adults)"
    
    # Team validation
    team = check_team(title, description)
    if not team:
        return False, "Team not in approved list"
    
    # Condition validation
    condition = item.get("status", "")
    if condition not in ACCEPTABLE_CONDITIONS:
        return False, f"Condition '{condition}' not acceptable"
    
    return True, "Valid tracksuit"

def validate_item(item: Dict) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Full item validation
    Returns (is_valid, team, reason_if_rejected)
    """
    is_valid, reason = is_complete_tracksuit(item)
    
    if not is_valid:
        logger.info(f"❌ Item rejected: {item.get('id')} - {reason}")
        return False, None, reason
    
    team = check_team(item.get("title", ""), item.get("description", ""))
    logger.info(f"✅ Item approved: {item.get('id')} - Team: {team}")
    
    return True, team, None

# ============================================================================
# VINTED API
# ============================================================================

def create_session() -> requests.Session:
    """Create a requests session with proper headers to avoid 401 errors"""
    session = requests.Session()
    
    # Realistic browser headers to avoid bot detection
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    
    return session

def fetch_vinted_items(session: requests.Session, 
                       url: str, 
                       search_params: Dict) -> Optional[List[Dict]]:
    """Fetch items from Vinted API with retry logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = session.get(url, params=search_params, timeout=10)
            
            if response.status_code == 429:
                logger.warning("⚠️ Rate limit hit! Waiting 60 seconds...")
                time.sleep(60)
                retry_count += 1
                continue
            
            if response.status_code == 401:
                logger.warning("⚠️ 401 Unauthorized - Vinted may have changed API protection. Retrying...")
                time.sleep(5)
                retry_count += 1
                continue
            
            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text[:200]}")
                return None
            
            data = response.json()
            return data.get("items", [])
        
        except requests.exceptions.Timeout:
            logger.error("⏱️ Request timeout")
            retry_count += 1
            time.sleep(3)
            continue
        except Exception as e:
            logger.error(f"❌ Error fetching Vinted: {e}")
            return None
    
    logger.error("💯 Max retries exceeded for Vinted API")
    return None

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def item_exists(item_id: int) -> bool:
    """Check if item already recorded"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM items WHERE item_id = ?", (item_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False

def save_item(item: Dict, status: str, team: Optional[str] = None, reason: Optional[str] = None):
    """Save item to database"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO items (
                item_id, title, price, team, brand, size, condition,
                image_url, vinted_url, status, reason_rejected, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"),
            item.get("title"),
            item.get("price"),
            team,
            check_brand(item.get("title", "")),
            item.get("size_title"),
            item.get("status"),
            item.get("photo", {}).get("full_size_url"),
            f"https://www.vinted.it/items/{item.get('id')}",
            status,
            reason,
            datetime.fromtimestamp(item.get("created_at_ts", 0))
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB save error: {e}")

def mark_notified(item_id: int, notification_type: str):
    """Mark item as notified"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notified (item_id, notification_type) VALUES (?, ?)",
            (item_id, notification_type)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB notify error: {e}")

# ============================================================================
# NOTIFICATIONS
# ============================================================================

def send_discord_notification(item: Dict, team: str):
    """Send Discord webhook notification"""
    if not CONFIG["DISCORD_WEBHOOK_URL"]:
        return
    
    try:
        embed = {
            "title": item.get("title", "N/A")[:256],
            "description": f"**Team:** {team.upper()}\n**Price:** €{item.get('price', 'N/A')}\n**Size:** {item.get('size_title', 'N/A')}",
            "color": 0x00FF00,
            "thumbnail": {
                "url": item.get("photo", {}).get("full_size_url", "")
            },
            "fields": [
                {"name": "Brand", "value": check_brand(item.get("title", "")) or "N/A", "inline": True},
                {"name": "Condition", "value": item.get("status", "N/A"), "inline": True},
                {"name": "Item ID", "value": str(item.get("id", "N/A")), "inline": True},
                {"name": "Published", "value": datetime.fromtimestamp(item.get("created_at_ts", 0)).strftime("%H:%M:%S"), "inline": True},
            ],
            "url": f"https://www.vinted.it/items/{item.get('id')}",
            "timestamp": datetime.now().isoformat()
        }
        
        data = {"embeds": [embed]}
        response = requests.post(CONFIG["DISCORD_WEBHOOK_URL"], json=data, timeout=5)
        
        if response.status_code == 204:
            logger.info("✅ Discord notification sent")
            mark_notified(item.get("id"), "discord")
        else:
            logger.warning(f"Discord error: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Discord notification error: {e}")

def send_telegram_notification(item: Dict, team: str):
    """Send Telegram notification"""
    if not CONFIG["TELEGRAM_BOT_TOKEN"] or not CONFIG["TELEGRAM_CHAT_ID"]:
        return
    
    try:
        text = (
            f"🎯 *TRACKSUIT FOUND*\n\n"
            f"*{item.get('title', 'N/A')}*\n"
            f"👥 Team: {team.upper()}\n"
            f"💰 Price: €{item.get('price', 'N/A')}\n"
            f"👕 Size: {item.get('size_title', 'N/A')}\n"
            f"📦 Condition: {item.get('status', 'N/A')}\n"
            f"🏷️ ID: {item.get('id', 'N/A')}\n"
            f"⏰ Published: {datetime.fromtimestamp(item.get('created_at_ts', 0)).strftime('%H:%M:%S')}\n"
            f"🔗 [View on Vinted](https://www.vinted.it/items/{item.get('id')})"
        )
        
        url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
        data = {
            "chat_id": CONFIG["TELEGRAM_CHAT_ID"],
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent")
            mark_notified(item.get("id"), "telegram")
        else:
            logger.warning(f"Telegram error: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Telegram notification error: {e}")

# ============================================================================
# MAIN MONITORING LOOP
# ============================================================================

def monitor_vinted():
    """Main monitoring loop"""
    logger.info("🚀 Starting Vinted Football Tracksuit Bot...")
    logger.info(f"📧 Discord enabled: {'✅' if CONFIG['DISCORD_WEBHOOK_URL'] else '❌'}")
    logger.info(f"📱 Telegram enabled: {'✅' if CONFIG['TELEGRAM_BOT_TOKEN'] and CONFIG['TELEGRAM_CHAT_ID'] else '❌'}")
    
    init_database()
    
    session = create_session()
    search_params = {
        "search_text": "tuta calcio",
        "order": "newest_first",
        "per_page": 30,
        "page": 1,
        "currency": "EUR"
    }
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            logger.info(f"\n📍 Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            found_count = 0
            approved_count = 0
            
            for vinted_url in CONFIG["VINTED_URLS"]:
                items = fetch_vinted_items(session, vinted_url, search_params)
                
                if not items:
                    continue
                
                for item in items:
                    item_id = item.get("id")
                    found_count += 1
                    
                    # Skip if already processed
                    if item_exists(item_id):
                        logger.debug(f"⏭️  Item {item_id} already processed")
                        continue
                    
                    # Validate item
                    is_valid, team, reason = validate_item(item)
                    
                    if is_valid:
                        approved_count += 1
                        save_item(item, "approved", team)
                        
                        # Send notifications
                        send_discord_notification(item, team)
                        send_telegram_notification(item, team)
                    else:
                        save_item(item, "rejected", reason=reason)
            
            logger.info(f"📊 Cycle Summary: {found_count} items scanned, {approved_count} approved")
            logger.info(f"⏳ Next check in {CONFIG['CHECK_INTERVAL']}s...\n")
            
            time.sleep(CONFIG["CHECK_INTERVAL"])
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            time.sleep(CONFIG["CHECK_INTERVAL"])

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    monitor_vinted()
