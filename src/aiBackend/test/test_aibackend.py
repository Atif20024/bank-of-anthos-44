#!/usr/bin/env python3
"""
Test script for AI Backend service.
This script tests the basic functionality of the AI Backend service.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import orchestrator
from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connections."""
    logger.info("Testing database connections...")
    
    try:
        # Test accounts database
        result = db_manager.execute_query("SELECT 1 as test", database="accounts")
        logger.info(f"✓ Accounts database connection successful: {result}")
        
        # Test ledger database
        result = db_manager.execute_query("SELECT 1 as test", database="ledger")
        logger.info(f"✓ Ledger database connection successful: {result}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

async def test_query_understanding():
    """Test query understanding agent."""
    logger.info("Testing query understanding...")
    
    try:
        from agents.query_understanding import QueryUnderstandingAgent
        agent = QueryUnderstandingAgent()
        
        test_queries = [
            "Show me my coffee spending this month",
            "How much did I spend on food last week?",
            "Am I spending more or less than usual?",
            "What are my biggest expenses?"
        ]
        
        for query in test_queries:
            intent = await agent.understand_query(query)
            if intent:
                logger.info(f"✓ Query understood: '{query}' -> {intent['analysis_type']}")
            else:
                logger.error(f"✗ Failed to understand query: '{query}'")
                return False
        
        return True
    except Exception as e:
        logger.error(f"✗ Query understanding test failed: {e}")
        return False

async def test_data_analyst():
    """Test data analyst agent."""
    logger.info("Testing data analyst...")
    
    try:
        from agents.data_analyst import DataAnalystAgent
        agent = DataAnalystAgent()
        
        # Test spending by category
        result = await agent.get_spending_by_category("testuser", days=30)
        logger.info(f"✓ Spending by category query successful: {len(result)} results")
        
        # Test spending trends
        result = await agent.get_spending_trends("testuser", days=30)
        logger.info(f"✓ Spending trends query successful: {len(result)} results")
        
        return True
    except Exception as e:
        logger.error(f"✗ Data analyst test failed: {e}")
        return False

async def test_insight_generator():
    """Test insight generator agent."""
    logger.info("Testing insight generator...")
    
    try:
        from agents.insight_generator import InsightGeneratorAgent
        agent = InsightGeneratorAgent()
        
        # Mock transaction data
        mock_transactions = [
            {"amount": 50, "timestamp": "2024-01-01T10:00:00Z", "description": "Coffee"},
            {"amount": 25, "timestamp": "2024-01-01T12:00:00Z", "description": "Lunch"},
            {"amount": 100, "timestamp": "2024-01-02T09:00:00Z", "description": "Groceries"},
        ]
        
        # Test category analysis
        insight = await agent.analyze_spending_categories(
            mock_transactions, 
            "testuser", 
            []
        )
        
        if insight:
            logger.info(f"✓ Category analysis insight generated: {insight['title']}")
        else:
            logger.warning("⚠ No category analysis insight generated")
        
        return True
    except Exception as e:
        logger.error(f"✗ Insight generator test failed: {e}")
        return False

async def test_user_preference():
    """Test user preference agent."""
    logger.info("Testing user preference agent...")
    
    try:
        from agents.user_preference import UserPreferenceAgent
        agent = UserPreferenceAgent()
        
        # Test getting preferences
        preferences = await agent.get_user_preferences("testuser")
        logger.info(f"✓ User preferences retrieved: {len(preferences)} preferences")
        
        # Test updating preferences
        test_preferences = {
            "spending_category": {
                "coffee": {"enabled": True, "threshold": 50.0},
                "food": {"enabled": True, "threshold": 200.0}
            }
        }
        
        success = await agent.update_preferences("testuser", test_preferences)
        if success:
            logger.info("✓ User preferences updated successfully")
        else:
            logger.warning("⚠ Failed to update user preferences")
        
        return True
    except Exception as e:
        logger.error(f"✗ User preference test failed: {e}")
        return False

async def test_alert_notification():
    """Test alert notification agent."""
    logger.info("Testing alert notification agent...")
    
    try:
        from agents.alert_notification import AlertNotificationAgent
        agent = AlertNotificationAgent()
        
        # Mock transaction data
        mock_transactions = [
            {"amount": 50, "timestamp": "2024-01-01T10:00:00Z", "description": "Coffee"},
            {"amount": 25, "timestamp": "2024-01-01T12:00:00Z", "description": "Lunch"},
        ]
        
        # Test alert checking
        alerts = await agent.check_alerts(mock_transactions, "testuser", [])
        logger.info(f"✓ Alert checking successful: {len(alerts)} alerts generated")
        
        return True
    except Exception as e:
        logger.error(f"✗ Alert notification test failed: {e}")
        return False

async def test_orchestrator():
    """Test orchestrator agent."""
    logger.info("Testing orchestrator...")
    
    try:
        # Test dashboard data
        dashboard_data = await orchestrator.get_user_dashboard_data("testuser")
        logger.info(f"✓ Dashboard data retrieved: {len(dashboard_data.get('insights', []))} insights")
        
        return True
    except Exception as e:
        logger.error(f"✗ Orchestrator test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    logger.info("Starting AI Backend tests...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Query Understanding", test_query_understanding),
        ("Data Analyst", test_data_analyst),
        ("Insight Generator", test_insight_generator),
        ("User Preference", test_user_preference),
        ("Alert Notification", test_alert_notification),
        ("Orchestrator", test_orchestrator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if await test_func():
                logger.info(f"✓ {test_name} test passed")
                passed += 1
            else:
                logger.error(f"✗ {test_name} test failed")
        except Exception as e:
            logger.error(f"✗ {test_name} test failed with exception: {e}")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ.setdefault("ACCOUNTS_DB_URI", "postgresql://user:password@localhost:5432/accounts")
    os.environ.setdefault("LEDGER_DB_URI", "postgresql://user:password@localhost:5432/ledger")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
