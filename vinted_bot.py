#!/usr/bin/env python3
"""
VINTED FOOTBALL TRACKSUIT BOT 🔍⚽
Monitor real-time adult complete football tracksuits (jacket + long pants)
Using Selenium for real browser automation to bypass API restrictions
"""

import sys
import subprocess

# Auto-install dependencies
required_packages = ["selenium", "webdriver-manager"]
for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        print(f"[INSTALLING] {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "DISCORD_WEBHOOK_URL": "",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "CHECK_INTERVAL": 120,  # Increased for Selenium
    "DB_NAME": "vinted_bot.db",
    "LOG_LEVEL": logging.INFO,
    "HEADLESS": True,  # Run without GUI
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
    for keyword in FORBIDDEN_KEYWORDS + FORBIDDEN_AGE_KEYWORDS:
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

def save_item(item_id: str, title: str, price: str, vinted_url: str, status: str, team: Optional[str] = None, reason: Optional[str] = None):
    """Save item to database"""
    try:
        conn = sqlite3.connect(CONFIG["DB_NAME"])
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO items (item_id, title, price, team, brand, status, vinted_url, reason_rejected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            title,
            price,
            team,
            check_brand(title),
            status,
            vinted_url,
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
        import requests
        data = {"embeds": [{"title": title[:256], "description": f"👥 **{team}** | 💰 **{price}", "color": 65280}]}
        requests.post(CONFIG["DISCORD_WEBHOOK_URL"], json=data, timeout=5)
        logger.info("✅ Discord sent")
    except:
        pass

def send_telegram(item_id: str, title: str, price: str, team: str):
    """Send Telegram notification"""
    if not CONFIG["TELEGRAM_BOT_TOKEN"] or not CONFIG["TELEGRAM_CHAT_ID"]:
        return
    try:
        import requests
        text = f"🎯 *{title}*\n👥 {team}\n💰 {price}"
        url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
        requests.post(url, json={"chat_id": CONFIG["TELEGRAM_CHAT_ID"], "text": text, "parse_mode": "Markdown"}, timeout=5)
        logger.info("✅ Telegram sent")
    except:
        pass

# ============================================================================
# SELENIUM BROWSER
# ============================================================================

def create_browser():
    """Create Selenium Chrome browser with anti-detection settings"""
    chrome_options = Options()
    
    if CONFIG["HEADLESS"]:
        chrome_options.add_argument("--headless")
    
    # Anti-detection
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def fetch_vinted_items() -> List[Dict]:
    """Fetch items from Vinted using Selenium"""
    driver = None
    items = []
    
    try:
        logger.info("🌐 Starting browser...")
        driver = create_browser()
        driver.set_page_load_timeout(20)
        
        # Navigate to Vinted search
        search_url = "https://www.vinted.it/items?search_text=tuta%20calcio&order=newest_first"
        logger.info(f"📄 Loading {search_url}...")
        driver.get(search_url)
        
        # Wait for items to load
        logger.info("⏳ Waiting for items to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='item-card']"))
        )
        
        # Give extra time for JS rendering
        time.sleep(3)
        
        # Find all item cards
        item_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='item-card']")
        logger.info(f"📦 Found {len(item_elements)} items on page")
        
        for element in item_elements[:20]:  # Limit to 20 items
            try:
                # Extract item data
                item_id = element.get_attribute("href").split("/items/")[-1] if element.get_attribute("href") else None
                title_elem = element.find_element(By.CSS_SELECTOR, "[data-testid='item-title']")
                price_elem = element.find_element(By.CSS_SELECTOR, "[data-testid='item-price']")
                
                if item_id and title_elem and price_elem:
                    item = {
                        "id": item_id,
                        "title": title_elem.text,
                        "price": price_elem.text,
                        "url": element.get_attribute("href")
                    }
                    items.append(item)
                    logger.debug(f"Extracted: {item['id']} - {item['title'][:50]}")
            except Exception as e:
                logger.debug(f"Error extracting item: {e}")
                continue
        
        logger.info(f"✅ Successfully scraped {len(items)} items")
    
    except Exception as e:
        logger.error(f"❌ Selenium error: {e}")
    
    finally:
        if driver:
            logger.info("🔒 Closing browser...")
            driver.quit()
    
    return items

# ============================================================================
# MAIN LOOP
# ============================================================================

def monitor_vinted():
    """Main monitoring loop"""
    logger.info("🚀 Starting Vinted Bot (Selenium Edition)...")
    logger.info(f"Discord: {'✅' if CONFIG['DISCORD_WEBHOOK_URL'] else '❌'}")
    logger.info(f"Telegram: {'✅' if CONFIG['TELEGRAM_BOT_TOKEN'] else '❌'}")
    
    init_database()
    cycle = 0
    
    while True:
        try:
            cycle += 1
            logger.info(f"\n🔍 Cycle #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            items = fetch_vinted_items()
            
            if not items:
                logger.warning("⚠️ No items found")
                logger.info(f"⏳ Next check in {CONFIG['CHECK_INTERVAL']}s\n")
                time.sleep(CONFIG['CHECK_INTERVAL'])
                continue
            
            total_approved = 0
            for item in items:
                item_id = str(item.get("id", ""))
                title = item.get("title", "")
                price = item.get("price", "N/A")
                url = item.get("url", "")
                
                if not item_id or not title:
                    continue
                
                if item_exists(item_id):
                    logger.debug(f"Already processed: {item_id}")
                    continue
                
                is_valid, reason = is_valid_tracksuit(title)
                
                if is_valid:
                    team = check_team(title)
                    total_approved += 1
                    save_item(item_id, title, price, url, "approved", team)
                    logger.info(f"✅ {item_id} | {title} | {team}")
                    send_discord(item_id, title, price, team)
                    send_telegram(item_id, title, price, team)
                else:
                    save_item(item_id, title, price, url, "rejected", reason=reason)
                    logger.debug(f"❌ {item_id} | {reason}")
            
            logger.info(f"📊 Found: {len(items)} | Approved: {total_approved}")
            logger.info(f"⏳ Next check in {CONFIG['CHECK_INTERVAL']}s\n")
            
            time.sleep(CONFIG['CHECK_INTERVAL'])
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Bot stopped")
            break
        except Exception as e:
            logger.error(f"💥 Error: {e}")
            time.sleep(CONFIG['CHECK_INTERVAL'])

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    monitor_vinted()
