#!/usr/bin/env python3
"""
Local startup script for AI Backend with environment setup
"""
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if required packages are installed."""
    logger.info("Checking requirements...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        import google.cloud.aiplatform
        logger.info("✓ All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing package: {e}")
        logger.info("Please run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment variables for local development."""
    logger.info("Setting up environment...")
    
    # Default values for local development
    env_vars = {
        'VERSION': 'v1.0.0',
        'PORT': '8080',
        'LOG_LEVEL': 'INFO',
        'ACCOUNTS_DB_URI': os.getenv('ACCOUNTS_DB_URI', 'postgresql://user:password@localhost:5432/accounts'),
        'LEDGER_DB_URI': os.getenv('LEDGER_DB_URI', 'postgresql://user:password@localhost:5432/ledger'),
        'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id'),
        'GOOGLE_CLOUD_REGION': os.getenv('GOOGLE_CLOUD_REGION', 'us-central1'),
        'VERTEX_AI_LOCATION': os.getenv('VERTEX_AI_LOCATION', 'us-central1'),
        'VERTEX_AI_MODEL': os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-pro'),
        'PUB_KEY_PATH': os.getenv('PUB_KEY_PATH', '/etc/secrets/jwtRS256.key.pub'),
        'LOCAL_ROUTING_NUM': os.getenv('LOCAL_ROUTING_NUM', '883745000'),
        'MAX_RETRIES': '1',
        'INSIGHT_EXPIRY_DAYS': '7',
        'MAX_INSIGHTS_PER_USER': '50'
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"✓ {key}: {value}")
    
    return True

def start_service():
    """Start the AI Backend service."""
    logger.info("Starting AI Backend service...")
    
    try:
        # Import and run the service
        import uvicorn
        from main import app
        
        logger.info("🚀 Starting AI Backend on http://localhost:8080")
        logger.info("📚 API Documentation: http://localhost:8080/docs")
        logger.info("🔍 Health Check: http://localhost:8080/healthy")
        logger.info("✅ Ready Check: http://localhost:8080/ready")
        logger.info("\nPress Ctrl+C to stop the service")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080,
            log_level="info",
            reload=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n👋 Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        return False
    
    return True

def main():
    """Main function."""
    logger.info("🚀 AI Backend Local Startup")
    logger.info("="*40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Start service
    start_service()

if __name__ == "__main__":
    main()
