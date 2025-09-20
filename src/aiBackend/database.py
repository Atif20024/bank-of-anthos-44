"""
Database connection and models for AI Backend service.
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, DECIMAL, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

logger = logging.getLogger(__name__)

# Database engines
accounts_engine = None
ledger_engine = None

def get_accounts_engine():
    """Get or create accounts database engine."""
    global accounts_engine
    if accounts_engine is None:
        accounts_engine = create_engine(
            settings.accounts_db_uri,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.log_level == "DEBUG"
        )
    return accounts_engine

def get_ledger_engine():
    """Get or create ledger database engine."""
    global ledger_engine
    if ledger_engine is None:
        ledger_engine = create_engine(
            settings.ledger_db_uri,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.log_level == "DEBUG"
        )
    return ledger_engine

def get_accounts_connection():
    """Get raw connection to accounts database."""
    return psycopg2.connect(
        settings.accounts_db_uri,
        cursor_factory=RealDictCursor
    )

def get_ledger_connection():
    """Get raw connection to ledger database."""
    return psycopg2.connect(
        settings.ledger_db_uri,
        cursor_factory=RealDictCursor
    )

class DatabaseManager:
    """Database manager for AI Backend operations."""
    
    def __init__(self):
        self.accounts_engine = get_accounts_engine()
        self.ledger_engine = get_ledger_engine()
    
    def execute_query(self, query: str, params: Optional[Dict] = None, database: str = "accounts") -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            database: "accounts" or "ledger"
            
        Returns:
            List of dictionaries containing query results
        """
        engine = self.accounts_engine if database == "accounts" else self.ledger_engine
        
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    def get_user_transactions(self, username: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's transactions from ledger database."""
        query = """
        SELECT t.*, u.username as from_username, u2.username as to_username
        FROM transactions t
        LEFT JOIN users u ON t.from_acct = u.accountid
        LEFT JOIN users u2 ON t.to_acct = u2.accountid
        WHERE u.username = :username OR u2.username = :username
        ORDER BY t.timestamp DESC
        LIMIT :limit OFFSET :offset
        """
        return self.execute_query(query, {
            "username": username,
            "limit": limit,
            "offset": offset
        }, database="ledger")
    
    def get_user_balance(self, username: str) -> Optional[float]:
        """Get user's current balance."""
        # This would need to be implemented based on how balances are calculated
        # For now, we'll calculate it from transactions
        query = """
        SELECT 
            COALESCE(SUM(CASE WHEN u.username = :username THEN t.amount ELSE 0 END), 0) as total_incoming,
            COALESCE(SUM(CASE WHEN u2.username = :username THEN t.amount ELSE 0 END), 0) as total_outgoing
        FROM transactions t
        LEFT JOIN users u ON t.to_acct = u.accountid
        LEFT JOIN users u2 ON t.from_acct = u2.accountid
        WHERE u.username = :username OR u2.username = :username
        """
        result = self.execute_query(query, {"username": username}, database="ledger")
        if result:
            balance = result[0]["total_incoming"] - result[0]["total_outgoing"]
            return float(balance)
        return 0.0
    
    def get_user_preferences(self, username: str) -> List[Dict[str, Any]]:
        """Get user preferences."""
        query = "SELECT * FROM user_preferences WHERE username = :username ORDER BY created_at DESC"
        return self.execute_query(query, {"username": username}, database="accounts")
    
    def save_user_preference(self, username: str, preference_type: str, preference_key: str, preference_value: Dict[str, Any]) -> int:
        """Save or update user preference."""
        # Check if preference exists
        check_query = """
        SELECT id FROM user_preferences 
        WHERE username = :username AND preference_type = :type AND preference_key = :key
        """
        existing = self.execute_query(check_query, {
            "username": username,
            "type": preference_type,
            "key": preference_key
        }, database="accounts")
        
        if existing:
            # Update existing preference
            update_query = """
            UPDATE user_preferences 
            SET preference_value = :value, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
            self.execute_query(update_query, {
                "value": preference_value,
                "id": existing[0]["id"]
            }, database="accounts")
            return existing[0]["id"]
        else:
            # Insert new preference
            insert_query = """
            INSERT INTO user_preferences (username, preference_type, preference_key, preference_value)
            VALUES (:username, :type, :key, :value)
            RETURNING id
            """
            result = self.execute_query(insert_query, {
                "username": username,
                "type": preference_type,
                "key": preference_key,
                "value": preference_value
            }, database="accounts")
            return result[0]["id"] if result else None
    
    def save_insight(self, username: str, insight_type: str, title: str, description: str, 
                    data: Dict[str, Any], visualization_config: Optional[Dict[str, Any]] = None,
                    priority: int = 1) -> int:
        """Save AI insight for user."""
        query = """
        INSERT INTO ai_insights (username, insight_type, title, description, data, visualization_config, priority)
        VALUES (:username, :type, :title, :description, :data, :viz_config, :priority)
        RETURNING id
        """
        result = self.execute_query(query, {
            "username": username,
            "type": insight_type,
            "title": title,
            "description": description,
            "data": data,
            "viz_config": visualization_config,
            "priority": priority
        }, database="accounts")
        return result[0]["id"] if result else None
    
    def get_user_insights(self, username: str, limit: int = 20, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get user's AI insights."""
        query = """
        SELECT * FROM ai_insights 
        WHERE username = :username
        """
        if unread_only:
            query += " AND is_read = FALSE"
        query += " ORDER BY priority DESC, created_at DESC LIMIT :limit"
        
        return self.execute_query(query, {
            "username": username,
            "limit": limit
        }, database="accounts")
    
    def mark_insight_read(self, insight_id: int, username: str) -> bool:
        """Mark insight as read."""
        query = """
        UPDATE ai_insights 
        SET is_read = TRUE 
        WHERE id = :insight_id AND username = :username
        """
        try:
            self.execute_query(query, {
                "insight_id": insight_id,
                "username": username
            }, database="accounts")
            return True
        except Exception as e:
            logger.error(f"Failed to mark insight as read: {e}")
            return False
    
    def log_interaction(self, username: str, interaction_type: str, insight_id: Optional[int] = None, 
                       interaction_data: Optional[Dict[str, Any]] = None) -> int:
        """Log user interaction for learning."""
        query = """
        INSERT INTO user_interactions (username, interaction_type, insight_id, interaction_data)
        VALUES (:username, :type, :insight_id, :data)
        RETURNING id
        """
        result = self.execute_query(query, {
            "username": username,
            "type": interaction_type,
            "insight_id": insight_id,
            "data": interaction_data
        }, database="accounts")
        return result[0]["id"] if result else None

# Global database manager instance
db_manager = DatabaseManager()
