#!/usr/bin/env python3
"""
Database initialization script for AI Backend.
This script creates the necessary tables and indexes for the AI Backend service.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_ai_backend_tables():
    """Initialize AI Backend tables in the accounts database."""
    try:
        # Create engine for accounts database
        engine = create_engine(settings.accounts_db_uri)
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                # Create user_preferences table
                logger.info("Creating user_preferences table...")
                connection.execute(text("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                  id SERIAL PRIMARY KEY,
                  username VARCHAR(64) NOT NULL,
                  preference_type VARCHAR(50) NOT NULL,
                  preference_key VARCHAR(100) NOT NULL,
                  preference_value JSONB NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                );
                """))
                
                # Create ai_insights table
                logger.info("Creating ai_insights table...")
                connection.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_insights (
                  id SERIAL PRIMARY KEY,
                  username VARCHAR(64) NOT NULL,
                  insight_type VARCHAR(50) NOT NULL,
                  title VARCHAR(200) NOT NULL,
                  description TEXT NOT NULL,
                  data JSONB NOT NULL,
                  visualization_config JSONB,
                  priority INTEGER DEFAULT 1,
                  is_read BOOLEAN DEFAULT FALSE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  expires_at TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                );
                """))
                
                # Create user_interactions table
                logger.info("Creating user_interactions table...")
                connection.execute(text("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                  id SERIAL PRIMARY KEY,
                  username VARCHAR(64) NOT NULL,
                  interaction_type VARCHAR(50) NOT NULL,
                  insight_id INTEGER,
                  interaction_data JSONB,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
                  FOREIGN KEY (insight_id) REFERENCES ai_insights(id) ON DELETE SET NULL
                );
                """))
                
                # Create alert_configurations table
                logger.info("Creating alert_configurations table...")
                connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alert_configurations (
                  id SERIAL PRIMARY KEY,
                  username VARCHAR(64) NOT NULL,
                  alert_type VARCHAR(50) NOT NULL,
                  alert_name VARCHAR(100) NOT NULL,
                  threshold_value DECIMAL(15,2) NOT NULL,
                  threshold_period VARCHAR(20) NOT NULL,
                  is_active BOOLEAN DEFAULT TRUE,
                  notification_method VARCHAR(20) DEFAULT 'in_app',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                );
                """))
                
                # Create indexes
                logger.info("Creating indexes...")
                connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_preferences_username ON user_preferences (username);
                CREATE INDEX IF NOT EXISTS idx_user_preferences_type ON user_preferences (preference_type);
                CREATE INDEX IF NOT EXISTS idx_ai_insights_username ON ai_insights (username);
                CREATE INDEX IF NOT EXISTS idx_ai_insights_type ON ai_insights (insight_type);
                CREATE INDEX IF NOT EXISTS idx_ai_insights_created ON ai_insights (created_at);
                CREATE INDEX IF NOT EXISTS idx_ai_insights_unread ON ai_insights (username, is_read) WHERE is_read = FALSE;
                CREATE INDEX IF NOT EXISTS idx_user_interactions_username ON user_interactions (username);
                CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions (interaction_type);
                CREATE INDEX IF NOT EXISTS idx_user_interactions_created ON user_interactions (created_at);
                CREATE INDEX IF NOT EXISTS idx_alert_configs_username ON alert_configurations (username);
                CREATE INDEX IF NOT EXISTS idx_alert_configs_type ON alert_configurations (alert_type);
                CREATE INDEX IF NOT EXISTS idx_alert_configs_active ON alert_configurations (username, is_active) WHERE is_active = TRUE;
                """))
                
                # Commit transaction
                trans.commit()
                logger.info("AI Backend tables created successfully!")
                
            except Exception as e:
                # Rollback transaction on error
                trans.rollback()
                logger.error(f"Error creating tables: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

def verify_tables():
    """Verify that all tables were created successfully."""
    try:
        engine = create_engine(settings.accounts_db_uri)
        
        with engine.connect() as connection:
            # Check if tables exist
            tables = [
                'user_preferences',
                'ai_insights', 
                'user_interactions',
                'alert_configurations'
            ]
            
            for table in tables:
                result = connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                );
                """))
                
                exists = result.scalar()
                if exists:
                    logger.info(f"✓ Table {table} exists")
                else:
                    logger.error(f"✗ Table {table} does not exist")
                    return False
            
            logger.info("All AI Backend tables verified successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Table verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting AI Backend database initialization...")
    
    # Initialize tables
    init_ai_backend_tables()
    
    # Verify tables
    if verify_tables():
        logger.info("Database initialization completed successfully!")
        sys.exit(0)
    else:
        logger.error("Database initialization failed verification!")
        sys.exit(1)
