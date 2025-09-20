"""
Orchestrator Agent - Main coordinator for AI Backend operations.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .data_analyst import DataAnalystAgent
from .insight_generator import InsightGeneratorAgent
from .user_preference import UserPreferenceAgent
from .query_understanding import QueryUnderstandingAgent
from .data_visualization import DataVisualizationAgent
from .alert_notification import AlertNotificationAgent
from database import db_manager
from vertex_ai_client import vertex_ai_client

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Main orchestrator that coordinates all AI agents."""
    
    def __init__(self):
        """Initialize orchestrator with all sub-agents."""
        self.data_analyst = DataAnalystAgent()
        self.insight_generator = InsightGeneratorAgent()
        self.user_preference = UserPreferenceAgent()
        self.query_understanding = QueryUnderstandingAgent()
        self.data_visualization = DataVisualizationAgent()
        self.alert_notification = AlertNotificationAgent()
        
        logger.info("Orchestrator Agent initialized with all sub-agents")
    
    async def process_user_query(self, username: str, query: str) -> Dict[str, Any]:
        """
        Process a user's natural language query.
        
        Args:
            username: Username of the user
            query: Natural language query
            
        Returns:
            Response containing insights and recommendations
        """
        try:
            logger.info(f"Processing query for user {username}: {query}")
            
            # Step 1: Understand the query intent
            query_intent = await self.query_understanding.understand_query(query)
            if not query_intent:
                return {
                    "success": False,
                    "error": "Could not understand your query. Please try rephrasing it."
                }
            
            # Step 2: Get user preferences for context
            user_preferences = await self.user_preference.get_user_preferences(username)
            
            # Step 3: Generate SQL query based on intent
            sql_query = await self.data_analyst.generate_sql_query(
                query_intent, 
                username, 
                user_preferences
            )
            
            if not sql_query:
                return {
                    "success": False,
                    "error": "Could not generate appropriate query for your request."
                }
            
            # Step 4: Execute query and get data
            data = await self.data_analyst.execute_query(sql_query, username)
            
            if not data:
                return {
                    "success": False,
                    "error": "No data found for your query."
                }
            
            # Step 5: Generate insights from data
            insights = await self.insight_generator.generate_insights(
                data, 
                query_intent, 
                username,
                user_preferences
            )
            
            # Step 6: Generate visualizations if needed
            visualizations = []
            if query_intent.get("needs_visualization", False):
                visualizations = await self.data_visualization.create_visualizations(
                    data, 
                    insights, 
                    query_intent
                )
            
            # Step 7: Log user interaction for learning
            await self.user_preference.log_interaction(
                username, 
                "query_processed", 
                interaction_data={
                    "query": query,
                    "intent": query_intent,
                    "insights_generated": len(insights)
                }
            )
            
            return {
                "success": True,
                "query_intent": query_intent,
                "data": data,
                "insights": insights,
                "visualizations": visualizations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing user query: {e}")
            return {
                "success": False,
                "error": "An error occurred while processing your query. Please try again."
            }
    
    async def generate_daily_insights(self, username: str) -> List[Dict[str, Any]]:
        """
        Generate daily insights for a user based on their spending patterns.
        
        Args:
            username: Username of the user
            
        Returns:
            List of generated insights
        """
        try:
            logger.info(f"Generating daily insights for user {username}")
            
            # Get user preferences
            user_preferences = await self.user_preference.get_user_preferences(username)
            
            # Get recent transaction data
            recent_transactions = db_manager.get_user_transactions(username, limit=100)
            
            if not recent_transactions:
                return []
            
            # Generate various types of insights
            insights = []
            
            # 1. Spending trend analysis
            trend_insight = await self.insight_generator.analyze_spending_trends(
                recent_transactions, 
                username,
                user_preferences
            )
            if trend_insight:
                insights.append(trend_insight)
            
            # 2. Category analysis
            category_insight = await self.insight_generator.analyze_spending_categories(
                recent_transactions, 
                username,
                user_preferences
            )
            if category_insight:
                insights.append(category_insight)
            
            # 3. Improvement analysis
            improvement_insight = await self.insight_generator.analyze_improvements(
                recent_transactions, 
                username,
                user_preferences
            )
            if improvement_insight:
                insights.append(improvement_insight)
            
            # 4. Check for alerts
            alerts = await self.alert_notification.check_alerts(
                recent_transactions, 
                username,
                user_preferences
            )
            insights.extend(alerts)
            
            # Save insights to database
            for insight in insights:
                insight_id = db_manager.save_insight(
                    username=username,
                    insight_type=insight["type"],
                    title=insight["title"],
                    description=insight["description"],
                    data=insight["data"],
                    visualization_config=insight.get("visualization_config"),
                    priority=insight.get("priority", 1)
                )
                insight["id"] = insight_id
            
            logger.info(f"Generated {len(insights)} insights for user {username}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating daily insights: {e}")
            return []
    
    async def get_user_dashboard_data(self, username: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a user.
        
        Args:
            username: Username of the user
            
        Returns:
            Dashboard data including insights, preferences, and recent activity
        """
        try:
            # Get recent insights
            insights = db_manager.get_user_insights(username, limit=10, unread_only=True)
            
            # Get user preferences
            preferences = await self.user_preference.get_user_preferences(username)
            
            # Get recent transactions
            recent_transactions = db_manager.get_user_transactions(username, limit=20)
            
            # Get current balance
            balance = db_manager.get_user_balance(username)
            
            # Get alert configurations
            alert_configs = db_manager.execute_query(
                "SELECT * FROM alert_configurations WHERE username = :username AND is_active = TRUE",
                {"username": username},
                database="accounts"
            )
            
            return {
                "insights": insights,
                "preferences": preferences,
                "recent_transactions": recent_transactions,
                "current_balance": balance,
                "alert_configurations": alert_configs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "insights": [],
                "preferences": [],
                "recent_transactions": [],
                "current_balance": 0.0,
                "alert_configurations": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def update_user_preferences(self, username: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences based on their interactions.
        
        Args:
            username: Username of the user
            preferences: New preferences to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.user_preference.update_preferences(username, preferences)
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

# Global orchestrator instance
orchestrator = OrchestratorAgent()
