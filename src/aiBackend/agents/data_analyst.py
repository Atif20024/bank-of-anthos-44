"""
Data Analyst Agent - Generates SQL queries and executes them.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from vertex_ai_client import vertex_ai_client
from database import db_manager

logger = logging.getLogger(__name__)

class DataAnalystAgent:
    """Agent responsible for generating and executing SQL queries."""
    
    def __init__(self):
        """Initialize data analyst agent."""
        self.schema_info = self._get_database_schema()
        logger.info("Data Analyst Agent initialized")
    
    def _get_database_schema(self) -> str:
        """Get database schema information for SQL generation."""
        return """
        Database Schema:
        
        ACCOUNTS DATABASE:
        - users: accountid (CHAR(10)), username (VARCHAR(64)), firstname, lastname, birthday, timezone, address, state, zip, ssn
        - contacts: username (VARCHAR(64)), label, account_num (CHAR(10)), routing_num (CHAR(9)), is_external (BOOLEAN)
        - user_preferences: username, preference_type, preference_key, preference_value (JSONB)
        - ai_insights: username, insight_type, title, description, data (JSONB), priority, is_read, created_at
        - user_interactions: username, interaction_type, insight_id, interaction_data (JSONB), created_at
        - alert_configurations: username, alert_type, alert_name, threshold_value, threshold_period, is_active
        
        LEDGER DATABASE:
        - transactions: transaction_id (BIGINT), from_acct (CHAR(10)), to_acct (CHAR(10)), 
          from_route (CHAR(9)), to_route (CHAR(9)), amount (INT), timestamp (TIMESTAMP)
        
        Common query patterns:
        - Get user transactions: JOIN transactions with users table on account numbers
        - Filter by time: WHERE timestamp >= 'YYYY-MM-DD' AND timestamp <= 'YYYY-MM-DD'
        - Group by categories: Use CASE statements to categorize transactions
        - Calculate totals: SUM(amount) with appropriate GROUP BY clauses
        """
    
    async def generate_sql_query(self, query_intent: Dict[str, Any], username: str, 
                               user_preferences: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate SQL query based on query intent and user preferences.
        
        Args:
            query_intent: Parsed intent from natural language query
            username: Username of the user
            user_preferences: User's preferences for context
            
        Returns:
            SQL query string or None if failed
        """
        try:
            # Build context for SQL generation
            context = self._build_query_context(query_intent, username, user_preferences)
            
            # Generate SQL using Vertex AI
            natural_language_query = query_intent.get("original_query", "")
            sql_query = vertex_ai_client.generate_sql_query(
                natural_language_query, 
                self.schema_info + "\n\nContext: " + context
            )
            
            if sql_query:
                # Validate and clean the SQL query
                sql_query = self._validate_sql_query(sql_query, username)
                logger.info(f"Generated SQL query: {sql_query}")
                return sql_query
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return None
    
    def _build_query_context(self, query_intent: Dict[str, Any], username: str, 
                           user_preferences: List[Dict[str, Any]]) -> str:
        """Build context string for SQL generation."""
        context_parts = []
        
        # Add user context
        context_parts.append(f"User: {username}")
        
        # Add query intent context
        if query_intent.get("time_period"):
            context_parts.append(f"Time period: {query_intent['time_period']}")
        
        if query_intent.get("categories"):
            context_parts.append(f"Categories: {', '.join(query_intent['categories'])}")
        
        if query_intent.get("analysis_type"):
            context_parts.append(f"Analysis type: {query_intent['analysis_type']}")
        
        # Add user preferences context
        if user_preferences:
            pref_context = []
            for pref in user_preferences:
                if pref.get("preference_type") == "spending_category":
                    pref_context.append(f"{pref['preference_key']}: {pref['preference_value']}")
            if pref_context:
                context_parts.append(f"User preferences: {', '.join(pref_context)}")
        
        return "; ".join(context_parts)
    
    def _validate_sql_query(self, sql_query: str, username: str) -> str:
        """
        Validate and clean SQL query for security and correctness.
        
        Args:
            sql_query: Raw SQL query
            username: Username for security validation
            
        Returns:
            Cleaned and validated SQL query
        """
        # Basic security checks
        sql_query = sql_query.strip()
        
        # Ensure username is properly escaped in WHERE clauses
        if "username" in sql_query.lower() and username not in sql_query:
            # This is a basic check - in production, use parameterized queries
            logger.warning("SQL query may not be properly parameterized")
        
        # Ensure only SELECT queries are allowed
        if not sql_query.upper().startswith("SELECT"):
            logger.error("Only SELECT queries are allowed")
            return None
        
        # Add basic safety measures
        if any(keyword in sql_query.upper() for keyword in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
            logger.error("Dangerous SQL keywords detected")
            return None
        
        return sql_query
    
    async def execute_query(self, sql_query: str, username: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: SQL query to execute
            username: Username for context
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            # Determine which database to use based on query
            database = "ledger" if "transactions" in sql_query.lower() else "accounts"
            
            # Execute query
            results = db_manager.execute_query(sql_query, database=database)
            
            logger.info(f"Executed query, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []
    
    async def get_spending_by_category(self, username: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get user's spending by category for the last N days.
        
        Args:
            username: Username of the user
            days: Number of days to look back
            
        Returns:
            List of spending by category
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT 
                CASE 
                    WHEN t.amount < 50 THEN 'Small purchases'
                    WHEN t.amount < 200 THEN 'Medium purchases'
                    WHEN t.amount < 500 THEN 'Large purchases'
                    ELSE 'Very large purchases'
                END as category,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount
            FROM transactions t
            JOIN users u ON t.from_acct = u.accountid
            WHERE u.username = :username 
            AND t.timestamp >= :start_date 
            AND t.timestamp <= :end_date
            GROUP BY category
            ORDER BY total_amount DESC
            """
            
            results = db_manager.execute_query(query, {
                "username": username,
                "start_date": start_date,
                "end_date": end_date
            }, database="ledger")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting spending by category: {e}")
            return []
    
    async def get_spending_trends(self, username: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get user's spending trends over time.
        
        Args:
            username: Username of the user
            days: Number of days to look back
            
        Returns:
            List of daily spending data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT 
                DATE(t.timestamp) as date,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount
            FROM transactions t
            JOIN users u ON t.from_acct = u.accountid
            WHERE u.username = :username 
            AND t.timestamp >= :start_date 
            AND t.timestamp <= :end_date
            GROUP BY DATE(t.timestamp)
            ORDER BY date ASC
            """
            
            results = db_manager.execute_query(query, {
                "username": username,
                "start_date": start_date,
                "end_date": end_date
            }, database="ledger")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting spending trends: {e}")
            return []
    
    async def get_monthly_comparison(self, username: str) -> List[Dict[str, Any]]:
        """
        Get monthly spending comparison for the user.
        
        Args:
            username: Username of the user
            
        Returns:
            Monthly spending comparison data
        """
        try:
            query = """
            SELECT 
                EXTRACT(YEAR FROM t.timestamp) as year,
                EXTRACT(MONTH FROM t.timestamp) as month,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_amount
            FROM transactions t
            JOIN users u ON t.from_acct = u.accountid
            WHERE u.username = :username 
            AND t.timestamp >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY EXTRACT(YEAR FROM t.timestamp), EXTRACT(MONTH FROM t.timestamp)
            ORDER BY year DESC, month DESC
            """
            
            results = db_manager.execute_query(query, {
                "username": username
            }, database="ledger")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting monthly comparison: {e}")
            return []
