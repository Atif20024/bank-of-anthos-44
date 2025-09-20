"""
User Preference Agent - Manages and learns from user preferences.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from vertex_ai_client import vertex_ai_client
from database import db_manager

logger = logging.getLogger(__name__)

class UserPreferenceAgent:
    """Agent responsible for managing user preferences and learning from interactions."""
    
    def __init__(self):
        """Initialize user preference agent."""
        logger.info("User Preference Agent initialized")
    
    async def get_user_preferences(self, username: str) -> List[Dict[str, Any]]:
        """
        Get user preferences from database.
        
        Args:
            username: Username of the user
            
        Returns:
            List of user preferences
        """
        try:
            preferences = db_manager.get_user_preferences(username)
            logger.info(f"Retrieved {len(preferences)} preferences for user {username}")
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return []
    
    async def update_preferences(self, username: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.
        
        Args:
            username: Username of the user
            preferences: New preferences to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success_count = 0
            
            for pref_type, pref_data in preferences.items():
                if isinstance(pref_data, dict):
                    for key, value in pref_data.items():
                        pref_id = db_manager.save_user_preference(
                            username=username,
                            preference_type=pref_type,
                            preference_key=key,
                            preference_value=value
                        )
                        if pref_id:
                            success_count += 1
                else:
                    # Single preference
                    pref_id = db_manager.save_user_preference(
                        username=username,
                        preference_type=pref_type,
                        preference_key="default",
                        preference_value=pref_data
                    )
                    if pref_id:
                        success_count += 1
            
            logger.info(f"Updated {success_count} preferences for user {username}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    async def learn_from_interaction(self, username: str, interaction_type: str, 
                                   interaction_data: Dict[str, Any], insight_id: Optional[int] = None) -> bool:
        """
        Learn from user interaction to improve future recommendations.
        
        Args:
            username: Username of the user
            interaction_type: Type of interaction (viewed_insight, dismissed_insight, etc.)
            interaction_data: Additional context about the interaction
            insight_id: ID of the insight if applicable
            
        Returns:
            True if learning was successful, False otherwise
        """
        try:
            # Log the interaction
            interaction_id = db_manager.log_interaction(
                username=username,
                interaction_type=interaction_type,
                insight_id=insight_id,
                interaction_data=interaction_data
            )
            
            if not interaction_id:
                return False
            
            # Learn from the interaction using AI
            await self._process_interaction_learning(username, interaction_type, interaction_data)
            
            logger.info(f"Processed learning from interaction for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")
            return False
    
    async def _process_interaction_learning(self, username: str, interaction_type: str, 
                                          interaction_data: Dict[str, Any]) -> None:
        """
        Process interaction data to learn user preferences.
        
        Args:
            username: Username of the user
            interaction_type: Type of interaction
            interaction_data: Interaction context
        """
        try:
            # Get user's interaction history
            interactions = db_manager.execute_query(
                "SELECT * FROM user_interactions WHERE username = :username ORDER BY created_at DESC LIMIT 50",
                {"username": username},
                database="accounts"
            )
            
            if not interactions:
                return
            
            # Use AI to analyze interaction patterns
            learning_prompt = f"""
            Analyze the following user interactions to learn their preferences:
            
            User: {username}
            Current interaction: {interaction_type} - {interaction_data}
            
            Recent interactions:
            {interactions[:10]}  # Last 10 interactions
            
            Based on this data, suggest:
            1. What types of insights this user prefers
            2. What time periods they're most interested in
            3. What categories they care about most
            4. How to improve future recommendations
            
            Respond in JSON format with preference suggestions.
            """
            
            learning_result = vertex_ai_client.generate_structured_response(learning_prompt)
            
            if learning_result and "preferences" in learning_result:
                # Update user preferences based on learning
                await self._apply_learned_preferences(username, learning_result["preferences"])
            
        except Exception as e:
            logger.error(f"Error processing interaction learning: {e}")
    
    async def _apply_learned_preferences(self, username: str, learned_preferences: Dict[str, Any]) -> None:
        """
        Apply learned preferences to user's profile.
        
        Args:
            username: Username of the user
            learned_preferences: Preferences learned from interactions
        """
        try:
            for pref_type, pref_data in learned_preferences.items():
                if isinstance(pref_data, dict):
                    for key, value in pref_data.items():
                        # Get current preference
                        current_prefs = db_manager.execute_query(
                            "SELECT preference_value FROM user_preferences WHERE username = :username AND preference_type = :type AND preference_key = :key",
                            {
                                "username": username,
                                "type": pref_type,
                                "key": key
                            },
                            database="accounts"
                        )
                        
                        if current_prefs:
                            # Update existing preference with learned data
                            current_value = current_prefs[0]["preference_value"]
                            if isinstance(current_value, dict) and isinstance(value, dict):
                                # Merge dictionaries
                                updated_value = {**current_value, **value}
                            else:
                                updated_value = value
                            
                            db_manager.save_user_preference(
                                username=username,
                                preference_type=pref_type,
                                preference_key=key,
                                preference_value=updated_value
                            )
                        else:
                            # Create new preference
                            db_manager.save_user_preference(
                                username=username,
                                preference_type=pref_type,
                                preference_key=key,
                                preference_value=value
                            )
            
            logger.info(f"Applied learned preferences for user {username}")
            
        except Exception as e:
            logger.error(f"Error applying learned preferences: {e}")
    
    async def get_personalized_recommendations(self, username: str) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user preferences and history.
        
        Args:
            username: Username of the user
            
        Returns:
            List of personalized recommendations
        """
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(username)
            
            # Get recent interactions
            interactions = db_manager.execute_query(
                "SELECT * FROM user_interactions WHERE username = :username ORDER BY created_at DESC LIMIT 20",
                {"username": username},
                database="accounts"
            )
            
            # Get recent insights
            insights = db_manager.get_user_insights(username, limit=10)
            
            # Generate personalized recommendations using AI
            recommendation_prompt = f"""
            Based on the following user data, generate personalized recommendations:
            
            User preferences: {preferences}
            Recent interactions: {interactions[:5]}
            Recent insights: {[insight['title'] for insight in insights[:5]]}
            
            Suggest:
            1. What insights to generate next
            2. What spending patterns to analyze
            3. What alerts to set up
            4. What improvements to track
            
            Respond in JSON format with specific, actionable recommendations.
            """
            
            recommendations = vertex_ai_client.generate_structured_response(recommendation_prompt)
            
            if recommendations:
                return recommendations.get("recommendations", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []
    
    async def set_alert_preferences(self, username: str, alert_config: Dict[str, Any]) -> bool:
        """
        Set up alert preferences for a user.
        
        Args:
            username: Username of the user
            alert_config: Alert configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            INSERT INTO alert_configurations (username, alert_type, alert_name, threshold_value, threshold_period, notification_method)
            VALUES (:username, :alert_type, :alert_name, :threshold_value, :threshold_period, :notification_method)
            ON CONFLICT (username, alert_type, alert_name) 
            DO UPDATE SET 
                threshold_value = EXCLUDED.threshold_value,
                threshold_period = EXCLUDED.threshold_period,
                notification_method = EXCLUDED.notification_method,
                updated_at = CURRENT_TIMESTAMP
            """
            
            db_manager.execute_query(query, {
                "username": username,
                "alert_type": alert_config.get("alert_type", "spending_threshold"),
                "alert_name": alert_config.get("alert_name", "Default Alert"),
                "threshold_value": alert_config.get("threshold_value", 100.0),
                "threshold_period": alert_config.get("threshold_period", "daily"),
                "notification_method": alert_config.get("notification_method", "in_app")
            }, database="accounts")
            
            logger.info(f"Set alert preferences for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting alert preferences: {e}")
            return False
    
    async def log_interaction(self, username: str, interaction_type: str, 
                            insight_id: Optional[int] = None, interaction_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Log user interaction for learning.
        
        Args:
            username: Username of the user
            interaction_type: Type of interaction
            insight_id: ID of the insight if applicable
            interaction_data: Additional context
            
        Returns:
            Interaction ID if successful, None otherwise
        """
        try:
            return db_manager.log_interaction(username, interaction_type, insight_id, interaction_data)
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            return None
