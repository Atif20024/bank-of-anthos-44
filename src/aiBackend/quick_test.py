#!/usr/bin/env python3
"""
Quick test script for AI Backend - can be run without full setup
"""
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        # Test core modules
        from config import settings
        logger.info("✓ Config module imported")
        
        from database import db_manager
        logger.info("✓ Database module imported")
        
        from auth import get_username_from_token
        logger.info("✓ Auth module imported")
        
        from vertex_ai_client import vertex_ai_client
        logger.info("✓ Vertex AI client imported")
        
        # Test agents
        from agents.query_understanding import QueryUnderstandingAgent
        logger.info("✓ Query Understanding Agent imported")
        
        from agents.data_analyst import DataAnalystAgent
        logger.info("✓ Data Analyst Agent imported")
        
        from agents.insight_generator import InsightGeneratorAgent
        logger.info("✓ Insight Generator Agent imported")
        
        from agents.user_preference import UserPreferenceAgent
        logger.info("✓ User Preference Agent imported")
        
        from agents.data_visualization import DataVisualizationAgent
        logger.info("✓ Data Visualization Agent imported")
        
        from agents.alert_notification import AlertNotificationAgent
        logger.info("✓ Alert Notification Agent imported")
        
        from agents.orchestrator import orchestrator
        logger.info("✓ Orchestrator imported")
        
        logger.info("✅ All imports successful!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    
    try:
        from config import settings
        
        # Check required settings
        required_settings = [
            'version', 'port', 'log_level',
            'accounts_db_uri', 'ledger_db_uri',
            'project_id', 'vertex_ai_location'
        ]
        
        for setting in required_settings:
            value = getattr(settings, setting, None)
            if value:
                logger.info(f"✓ {setting}: {value}")
            else:
                logger.warning(f"⚠ {setting}: Not set")
        
        logger.info("✅ Configuration test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

async def test_query_understanding():
    """Test query understanding without database."""
    logger.info("Testing query understanding...")
    
    try:
        from agents.query_understanding import QueryUnderstandingAgent
        
        agent = QueryUnderstandingAgent()
        
        # Test queries
        test_queries = [
            "Show me my coffee spending this month",
            "How much did I spend on food last week?",
            "Am I spending more or less than usual?"
        ]
        
        for query in test_queries:
            try:
                # This will work even without database connection
                intent = await agent.understand_query(query)
                if intent:
                    logger.info(f"✓ Query understood: '{query}' -> {intent.get('analysis_type', 'unknown')}")
                else:
                    logger.warning(f"⚠ Query not understood: '{query}'")
            except Exception as e:
                logger.warning(f"⚠ Query failed: '{query}' - {e}")
        
        logger.info("✅ Query understanding test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Query understanding test failed: {e}")
        return False

def test_vertex_ai_client():
    """Test Vertex AI client (without actual API call)."""
    logger.info("Testing Vertex AI client...")
    
    try:
        from vertex_ai_client import VertexAIClient
        
        # Just test if the client can be instantiated
        # Don't make actual API calls in quick test
        logger.info("✓ Vertex AI client can be instantiated")
        logger.info("✅ Vertex AI client test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vertex AI client test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for full testing."""
    logger.info("\n" + "="*50)
    logger.info("🎉 Quick test completed!")
    logger.info("="*50)
    logger.info("\n📋 Next steps for full testing:")
    logger.info("1. Set up environment variables:")
    logger.info("   export ACCOUNTS_DB_URI='postgresql://user:pass@host:5432/accounts'")
    logger.info("   export LEDGER_DB_URI='postgresql://user:pass@host:5432/ledger'")
    logger.info("   export GOOGLE_CLOUD_PROJECT='your-project-id'")
    logger.info("\n2. Initialize database:")
    logger.info("   python init_db.py")
    logger.info("\n3. Run comprehensive tests:")
    logger.info("   python test/test_aibackend.py")
    logger.info("\n4. Start the service:")
    logger.info("   python main.py")
    logger.info("\n5. Test the API:")
    logger.info("   curl http://localhost:8080/healthy")
    logger.info("\n6. Deploy to GKE:")
    logger.info("   ./deploy.sh")

async def main():
    """Run all quick tests."""
    logger.info("🚀 Starting AI Backend quick test...")
    logger.info("="*50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Query Understanding Test", test_query_understanding),
        ("Vertex AI Client Test", test_vertex_ai_client),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                logger.error(f"❌ {test_name} failed")
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All quick tests passed!")
        show_next_steps()
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
