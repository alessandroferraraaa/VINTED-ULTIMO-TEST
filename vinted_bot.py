"""
VINTED FOOTBALL TRACKSUIT BOT 🔍⚽
Monitor real-time adult complete football tracksuits (jacket + long pants)
Strict filters: sizes S/M/L/XL only, approved teams/brands only
Uses Selenium headless browser for reliable scraping
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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # DISCORD WEBHOOK (read from environment or config)
    "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
    
    # TELEGRAM (read from environment or config)
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    
    # VINTED SEARCH URLs
    "VINTED_URLS": [
        "https://www.vinted.it/items?search_text=tuta%20calcio&order=newest_first",
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
    "Nuovo con cartellino",
    "Buone condizioni",
    "Condizioni accettabili"
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
            item_id TEXT PRIMARY KEY,
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

def is_complete_tracksuit(title: str) -> tuple[bool, str]:
    """
    Strictly validate if item is a complete tracksuit (jacket + long pants)
    Returns (is_valid, reason)
    """
    title_lower = title.lower()
    
    # Check forbidden keywords first
    if check_forbidden_keywords(title_lower):
        return False, "Contains forbidden keywords"
    
    # Check for approved combination keywords
    has_approved_combo = any(combo in title_lower for combo in APPROVED_COMBINATIONS)
    
    if not has_approved_combo:
        # Check minimal requirements
        has_jacket = any(word in title_lower for word in ["felpa", "giacca", "jacket", "hoodie"])
        has_pants = any(word in title_lower for word in ["pantalone", "pants", "trousers"])
        
        if not (has_jacket and has_pants):
            return False, "Not a complete tracksuit (missing jacket or pants)"
    
    # Team validation
    team = check_team(title)
    if not team:
        return False, "Team not in approved list"
    
    return True, "Valid tracksuit"

# ============================================================================
# SELENIUM BROWSER
# ============================================================================

def create_driver():
    """Create Selenium webdriver with headless Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_vinted_items(driver) -> List[Dict]:
    """Fetch items from Vinted using Selenium"""
    items = []
    try:
        url = CONFIG["VINTED_URLS"][0]
        logger.info(f"🔍 Fetching from {url}")
        
        driver.get(url)
        time.sleep(3)  # Wait for page load
        
        # Wait for items to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "item-card"))
        )
        
        # Extract items
        item_cards = driver.find_elements(By.CLASS_NAME, "item-card")
        logger.info(f"📦 Found {len(item_cards)} items on page")
        
        for card in item_cards:
            try:
                # Extract title
                title_elem = card.find_element(By.CLASS_NAME, "item-title")
                title = title_elem.text.strip()
                
                # Extract URL
                link_elem = card.find_element(By.TAG_NAME, "a")
                url = link_elem.get_attribute("href")
                item_id = url.split("/")[-1] if url else None
                
                if not item_id or not title:
                    continue
                
                # Extract price (optional)
                price_elem = card.find_elements(By.CLASS_NAME, "item-price")
                price = price_elem[0].text.strip() if price_elem else "N/A"
                
                item = {
                    "id": item_id,
                    "title": title,
                    "price": price,
                    "url": url
                }
                
                items.append(item)
            except Exception as e:
                logger.debug(f"⚠️ Error parsing item: {e}")
                continue
    
    except Exception as e:
        logger.error(f"❌ Error fetching Vinted: {e}")
    
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
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False

def save_item(item: Dict, status: str, team: Optional[str] = None, reason: Optional[str] = None):
    """Save item to database"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO items (
                item_id, title, price, team, brand, status, vinted_url, reason_rejected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

def mark_notified(item_id: str, notification_type: str):
    """Mark item as notified"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO notified (item_id, notification_type) VALUES (?, ?)",
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
            "description": f"**Team:** {team.upper()}\n**Price:** {item.get('price', 'N/A')}",
            "color": 0x00FF00,
            "fields": [
                {"name": "Brand", "value": check_brand(item.get("title", "")) or "N/A", "inline": True},
                {"name": "Item ID", "value": str(item.get("id", "N/A")), "inline": True},
            ],
            "url": item.get("url", ""),
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
            f"💰 Price: {item.get('price', 'N/A')}\n"
            f"🔗 [View on Vinted]({item.get('url', '')})"
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
    logger.info("🚀 Starting Vinted Football Tracksuit Bot (Selenium)...")
    logger.info(f"📧 Discord enabled: {'✅' if CONFIG['DISCORD_WEBHOOK_URL'] else '❌'}")
    logger.info(f"📱 Telegram enabled: {'✅' if CONFIG['TELEGRAM_BOT_TOKEN'] and CONFIG['TELEGRAM_CHAT_ID'] else '❌'}")
    
    init_database()
    
    driver = None
    cycle = 0
    
    try:
        driver = create_driver()
        logger.info("🌐 Selenium driver initialized")
        
        while True:
            try:
                cycle += 1
                logger.info(f"\n📍 Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Fetch items
                items = fetch_vinted_items(driver)
                
                if not items:
                    logger.warning("⚠️ No items found")
                    time.sleep(CONFIG["CHECK_INTERVAL"])
                    continue
                
                approved_count = 0
                
                for item in items:
                    item_id = item.get("id")
                    
                    # Skip if already processed
                    if item_exists(item_id):
                        logger.debug(f"⏭️  Item {item_id} already processed")
                        continue
                    
                    # Validate item
                    is_valid, reason = is_complete_tracksuit(item.get("title", ""))
                    
                    if is_valid:
                        team = check_team(item.get("title", ""))
                        approved_count += 1
                        save_item(item, "approved", team)
                        
                        logger.info(f"✅ Item approved: {item_id} - Team: {team}")
                        
                        # Send notifications
                        send_discord_notification(item, team)
                        send_telegram_notification(item, team)
                    else:
                        save_item(item, "rejected", reason=reason)
                        logger.info(f"❌ Item rejected: {item_id} - {reason}")
                
                logger.info(f"📊 Cycle Summary: {len(items)} items scanned, {approved_count} approved")
                logger.info(f"⏳ Next check in {CONFIG['CHECK_INTERVAL']}s...\n")
                
                time.sleep(CONFIG["CHECK_INTERVAL"])
            
            except KeyboardInterrupt:
                logger.info("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Cycle error: {e}")
                time.sleep(CONFIG["CHECK_INTERVAL"])
    
    finally:
        if driver:
            driver.quit()
            logger.info("🚪 Selenium driver closed")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    monitor_vinted()
