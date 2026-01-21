#!/usr/bin/env python3
"""
TEST SCRIPT FOR VINTED BOT
Verifies all functions work correctly
"""

import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vinted_bot import (
    check_forbidden_keywords,
    check_team,
    check_brand,
    is_valid_tracksuit,
    init_database,
    item_exists,
    save_item,
    create_session,
    fetch_items,
    APPROVED_TEAMS,
    APPROVED_BRANDS,
    FORBIDDEN_KEYWORDS,
    APPROVED_COMBINATIONS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_validation():
    """Test validation functions"""
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 1: VALIDATION FUNCTIONS")
    logger.info("="*60)
    
    # Test 1: Valid tracksuit
    test_cases = [
        ("Tuta calcio Nike Inter XL", True, "inter"),
        ("Football tracksuit Adidas Liverpool M", True, "liverpool"),
        ("Completo calcio Puma Barcelona S", True, "barcellona"),
        ("Solo pantalone calcio", False, "rejected - missing jacket"),
        ("Tuta bimbo", False, "rejected - kids"),
        ("Tracksuit summer estivo", False, "rejected - forbidden keyword"),
    ]
    
    for title, should_pass, expected_team in test_cases:
        is_valid, reason = is_valid_tracksuit(title)
        team = check_team(title) if is_valid else None
        status = "✅" if (is_valid == should_pass) else "❌"
        logger.info(f"{status} '{title}' -> Valid: {is_valid}, Reason: {reason}, Team: {team}")
    
    # Test 2: Team extraction
    logger.info("\n📍 Team Extraction:")
    for team in list(APPROVED_TEAMS)[:5]:
        extracted = check_team(f"Tuta calcio {team} S")
        status = "✅" if extracted == team else "❌"
        logger.info(f"{status} '{team}' -> Extracted: {extracted}")
    
    # Test 3: Brand extraction
    logger.info("\n🏷️ Brand Extraction:")
    for brand in list(APPROVED_BRANDS)[:5]:
        extracted = check_brand(f"Tuta {brand} calcio M")
        status = "✅" if extracted == brand else "❌"
        logger.info(f"{status} '{brand}' -> Extracted: {extracted}")
    
    # Test 4: Forbidden keywords
    logger.info("\n🚫 Forbidden Keywords:")
    forbidden_tests = ["kids", "bambino", "solo pantalone", "shorts", "training set"]
    for keyword in forbidden_tests:
        has_forbidden = check_forbidden_keywords(f"Tuta {keyword} calcio")
        status = "✅" if has_forbidden else "❌"
        logger.info(f"{status} Keyword '{keyword}' -> Detected: {has_forbidden}")

def test_database():
    """Test database functions"""
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 2: DATABASE FUNCTIONS")
    logger.info("="*60)
    
    try:
        # Initialize database
        logger.info("📝 Initializing database...")
        init_database()
        logger.info("✅ Database initialized successfully")
        
        # Test save and retrieve
        test_item = {
            "id": "test_item_12345",
            "title": "Tuta calcio Nike Inter M",
            "price": "€25.99",
            "url": "https://www.vinted.it/items/123"
        }
        
        logger.info(f"💾 Saving test item...")
        save_item(test_item, "approved", "inter")
        logger.info("✅ Item saved")
        
        logger.info(f"🔍 Checking if item exists...")
        exists = item_exists("test_item_12345")
        if exists:
            logger.info("✅ Item retrieved from database")
        else:
            logger.warning("❌ Item not found in database")
    
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")

def test_session():
    """Test session creation"""
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 3: SESSION CREATION")
    logger.info("="*60)
    
    try:
        session = create_session()
        logger.info(f"✅ Session created")
        logger.info(f"✅ Headers: {len(session.headers)} headers configured")
        return session
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}")
        return None

def test_scraping(session):
    """Test web scraping"""
    logger.info("\n" + "="*60)
    logger.info("🧪 TEST 4: WEB SCRAPING (PRODUCTION TEST)")
    logger.info("="*60)
    
    if not session:
        logger.warning("⚠️ Session not available, skipping scraping test")
        return
    
    try:
        logger.info(f"🔗 Fetching items from Vinted...")
        items = fetch_items(session)
        
        if items:
            logger.info(f"✅ Fetched {len(items)} items")
            
            # Show first 3 items
            logger.info("\n📋 Sample items:")
            for i, item in enumerate(items[:3], 1):
                logger.info(f"{i}. ID: {item['id']}")
                logger.info(f"   Title: {item['title'][:60]}...")
                logger.info(f"   Price: {item['price']}")
                logger.info(f"   URL: {item['url'][:50]}...")
                
                # Test validation on real items
                is_valid, reason = is_valid_tracksuit(item['title'])
                team = check_team(item['title']) if is_valid else None
                logger.info(f"   Valid: {is_valid} ({reason}), Team: {team}")
        else:
            logger.warning("⚠️ No items fetched")
    
    except Exception as e:
        logger.error(f"❌ Scraping test failed: {e}")

def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "#"*60)
    logger.info("# VINTED BOT - COMPREHENSIVE TEST SUITE")
    logger.info("#"*60)
    
    # Test 1: Validation
    test_validation()
    
    # Test 2: Database
    test_database()
    
    # Test 3: Session
    session = test_session()
    
    # Test 4: Web Scraping
    if session:
        test_scraping(session)
    
    logger.info("\n" + "#"*60)
    logger.info("# ✅ ALL TESTS COMPLETED")
    logger.info("#"*60 + "\n")

if __name__ == "__main__":
    run_all_tests()
