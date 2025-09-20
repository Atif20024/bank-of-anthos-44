"""
Alert/Notification Agent - Monitors spending patterns and generates alerts.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from vertex_ai_client import vertex_ai_client
from database import db_manager

logger = logging.getLogger(__name__)

class AlertNotificationAgent:
    """Agent responsible for monitoring spending patterns and generating alerts."""
    
    def __init__(self):
        """Initialize alert notification agent."""
        self.alert_types = {
            "spending_threshold": "Daily/weekly/monthly spending exceeds threshold",
            "category_budget": "Spending in specific category exceeds budget",
            "unusual_spending": "Unusual spending pattern detected",
            "low_balance": "Account balance below threshold",
            "improvement_alert": "Positive spending improvement detected"
        }
        logger.info("Alert Notification Agent initialized")
    
    async def check_alerts(self, transactions: List[Dict[str, Any]], 
                          username: str, user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check for various types of alerts based on user's transactions and preferences.
        
        Args:
            transactions: User's recent transactions
            username: Username of the user
            user_preferences: User's preferences and thresholds
            
        Returns:
            List of generated alerts
        """
        try:
            alerts = []
            
            if not transactions:
                return alerts
            
            # Get user's alert configurations
            alert_configs = await self._get_user_alert_configs(username)
            
            # Check different types of alerts
            alerts.extend(await self._check_spending_threshold_alerts(transactions, username, alert_configs))
            alerts.extend(await self._check_category_budget_alerts(transactions, username, alert_configs))
            alerts.extend(await self._check_unusual_spending_alerts(transactions, username, alert_configs))
            alerts.extend(await self._check_balance_alerts(username, alert_configs))
            alerts.extend(await self._check_improvement_alerts(transactions, username, user_preferences))
            
            logger.info(f"Generated {len(alerts)} alerts for user {username}")
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []
    
    async def _get_user_alert_configs(self, username: str) -> List[Dict[str, Any]]:
        """Get user's alert configurations."""
        try:
            configs = db_manager.execute_query(
                "SELECT * FROM alert_configurations WHERE username = :username AND is_active = TRUE",
                {"username": username},
                database="accounts"
            )
            return configs
        except Exception as e:
            logger.error(f"Error getting alert configs: {e}")
            return []
    
    async def _check_spending_threshold_alerts(self, transactions: List[Dict[str, Any]], 
                                             username: str, alert_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for spending threshold alerts."""
        alerts = []
        
        try:
            # Get spending threshold configs
            threshold_configs = [config for config in alert_configs if config["alert_type"] == "spending_threshold"]
            
            for config in threshold_configs:
                threshold_value = float(config["threshold_value"])
                period = config["threshold_period"]
                
                # Calculate spending for the period
                spending = await self._calculate_spending_for_period(transactions, period)
                
                if spending > threshold_value:
                    alert = {
                        "type": "spending_threshold",
                        "title": f"Spending Alert: {config['alert_name']}",
                        "description": f"You've spent ${spending:.2f} this {period}, exceeding your threshold of ${threshold_value:.2f}",
                        "data": {
                            "threshold_value": threshold_value,
                            "actual_spending": spending,
                            "period": period,
                            "excess_amount": spending - threshold_value
                        },
                        "priority": 3,
                        "alert_config_id": config["id"]
                    }
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking spending threshold alerts: {e}")
            return []
    
    async def _check_category_budget_alerts(self, transactions: List[Dict[str, Any]], 
                                          username: str, alert_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for category budget alerts."""
        alerts = []
        
        try:
            # Get category budget configs
            category_configs = [config for config in alert_configs if config["alert_type"] == "category_budget"]
            
            for config in category_configs:
                threshold_value = float(config["threshold_value"])
                period = config["threshold_period"]
                category = config.get("alert_name", "Unknown Category")
                
                # Calculate spending for the category in the period
                category_spending = await self._calculate_category_spending(transactions, category, period)
                
                if category_spending > threshold_value:
                    alert = {
                        "type": "category_budget",
                        "title": f"Category Budget Alert: {category}",
                        "description": f"You've spent ${category_spending:.2f} on {category} this {period}, exceeding your budget of ${threshold_value:.2f}",
                        "data": {
                            "category": category,
                            "threshold_value": threshold_value,
                            "actual_spending": category_spending,
                            "period": period,
                            "excess_amount": category_spending - threshold_value
                        },
                        "priority": 3,
                        "alert_config_id": config["id"]
                    }
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking category budget alerts: {e}")
            return []
    
    async def _check_unusual_spending_alerts(self, transactions: List[Dict[str, Any]], 
                                           username: str, alert_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for unusual spending pattern alerts."""
        alerts = []
        
        try:
            if len(transactions) < 10:  # Need enough data for pattern analysis
                return alerts
            
            # Use AI to detect unusual spending patterns
            unusual_patterns = await self._detect_unusual_patterns(transactions, username)
            
            for pattern in unusual_patterns:
                alert = {
                    "type": "unusual_spending",
                    "title": "Unusual Spending Pattern Detected",
                    "description": pattern["description"],
                    "data": pattern["data"],
                    "priority": 2,
                    "alert_config_id": None
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking unusual spending alerts: {e}")
            return []
    
    async def _check_balance_alerts(self, username: str, alert_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for low balance alerts."""
        alerts = []
        
        try:
            # Get low balance configs
            balance_configs = [config for config in alert_configs if config["alert_type"] == "low_balance"]
            
            if not balance_configs:
                return alerts
            
            # Get current balance
            current_balance = db_manager.get_user_balance(username)
            
            for config in balance_configs:
                threshold_value = float(config["threshold_value"])
                
                if current_balance < threshold_value:
                    alert = {
                        "type": "low_balance",
                        "title": "Low Balance Alert",
                        "description": f"Your current balance (${current_balance:.2f}) is below your threshold (${threshold_value:.2f})",
                        "data": {
                            "current_balance": current_balance,
                            "threshold_value": threshold_value,
                            "deficit": threshold_value - current_balance
                        },
                        "priority": 4,
                        "alert_config_id": config["id"]
                    }
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking balance alerts: {e}")
            return []
    
    async def _check_improvement_alerts(self, transactions: List[Dict[str, Any]], 
                                      username: str, user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for positive improvement alerts."""
        alerts = []
        
        try:
            if len(transactions) < 20:  # Need enough data for comparison
                return alerts
            
            # Analyze spending improvements
            improvements = await self._analyze_spending_improvements(transactions, username)
            
            for improvement in improvements:
                if improvement["is_positive"]:
                    alert = {
                        "type": "improvement_alert",
                        "title": "Great Job! Spending Improvement Detected",
                        "description": improvement["description"],
                        "data": improvement["data"],
                        "priority": 1,  # Low priority for positive alerts
                        "alert_config_id": None
                    }
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking improvement alerts: {e}")
            return []
    
    async def _calculate_spending_for_period(self, transactions: List[Dict[str, Any]], period: str) -> float:
        """Calculate total spending for a given period."""
        try:
            now = datetime.now()
            
            if period == "daily":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                start_date = now - timedelta(days=7)
            elif period == "monthly":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Default to daily
            
            total_spending = 0
            for transaction in transactions:
                if isinstance(transaction.get("timestamp"), str):
                    trans_date = datetime.fromisoformat(transaction["timestamp"].replace("Z", "+00:00"))
                else:
                    trans_date = transaction["timestamp"]
                
                if trans_date >= start_date:
                    total_spending += transaction.get("amount", 0)
            
            return total_spending
            
        except Exception as e:
            logger.error(f"Error calculating spending for period: {e}")
            return 0.0
    
    async def _calculate_category_spending(self, transactions: List[Dict[str, Any]], 
                                         category: str, period: str) -> float:
        """Calculate spending for a specific category in a period."""
        try:
            # This is a simplified implementation
            # In a real system, you'd have proper category mapping
            category_keywords = {
                "coffee": ["coffee", "starbucks", "cafe"],
                "food": ["restaurant", "dining", "food", "lunch", "dinner"],
                "entertainment": ["movie", "game", "netflix", "spotify"],
                "shopping": ["amazon", "store", "retail"]
            }
            
            keywords = category_keywords.get(category.lower(), [category.lower()])
            
            now = datetime.now()
            if period == "daily":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                start_date = now - timedelta(days=7)
            elif period == "monthly":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)
            
            category_spending = 0
            for transaction in transactions:
                if isinstance(transaction.get("timestamp"), str):
                    trans_date = datetime.fromisoformat(transaction["timestamp"].replace("Z", "+00:00"))
                else:
                    trans_date = transaction["timestamp"]
                
                if trans_date >= start_date:
                    # Simple keyword matching - in production, use proper categorization
                    transaction_desc = str(transaction.get("description", "")).lower()
                    if any(keyword in transaction_desc for keyword in keywords):
                        category_spending += transaction.get("amount", 0)
            
            return category_spending
            
        except Exception as e:
            logger.error(f"Error calculating category spending: {e}")
            return 0.0
    
    async def _detect_unusual_patterns(self, transactions: List[Dict[str, Any]], username: str) -> List[Dict[str, Any]]:
        """Detect unusual spending patterns using AI."""
        try:
            # Use AI to analyze spending patterns
            analysis_result = vertex_ai_client.analyze_data(
                transactions,
                "unusual_spending_detection",
                f"Detect unusual spending patterns for user {username}"
            )
            
            if not analysis_result or "unusual_patterns" not in analysis_result:
                return []
            
            patterns = []
            for pattern in analysis_result["unusual_patterns"]:
                patterns.append({
                    "description": pattern.get("description", "Unusual spending pattern detected"),
                    "data": pattern.get("data", {})
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting unusual patterns: {e}")
            return []
    
    async def _analyze_spending_improvements(self, transactions: List[Dict[str, Any]], username: str) -> List[Dict[str, Any]]:
        """Analyze spending improvements using AI."""
        try:
            # Use AI to analyze improvements
            analysis_result = vertex_ai_client.analyze_data(
                transactions,
                "spending_improvement_analysis",
                f"Analyze spending improvements for user {username}"
            )
            
            if not analysis_result or "improvements" not in analysis_result:
                return []
            
            improvements = []
            for improvement in analysis_result["improvements"]:
                if improvement.get("is_positive", False):
                    improvements.append({
                        "description": improvement.get("description", "Positive spending improvement detected"),
                        "data": improvement.get("data", {}),
                        "is_positive": True
                    })
            
            return improvements
            
        except Exception as e:
            logger.error(f"Error analyzing spending improvements: {e}")
            return []
    
    async def create_alert_configuration(self, username: str, alert_type: str, 
                                       alert_name: str, threshold_value: float, 
                                       threshold_period: str, notification_method: str = "in_app") -> bool:
        """
        Create a new alert configuration for a user.
        
        Args:
            username: Username of the user
            alert_type: Type of alert
            alert_name: Name of the alert
            threshold_value: Threshold value
            threshold_period: Period for the threshold
            notification_method: How to notify the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            INSERT INTO alert_configurations (username, alert_type, alert_name, threshold_value, threshold_period, notification_method)
            VALUES (:username, :alert_type, :alert_name, :threshold_value, :threshold_period, :notification_method)
            """
            
            db_manager.execute_query(query, {
                "username": username,
                "alert_type": alert_type,
                "alert_name": alert_name,
                "threshold_value": threshold_value,
                "threshold_period": threshold_period,
                "notification_method": notification_method
            }, database="accounts")
            
            logger.info(f"Created alert configuration for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating alert configuration: {e}")
            return False
    
    async def update_alert_configuration(self, alert_id: int, username: str, 
                                       updates: Dict[str, Any]) -> bool:
        """
        Update an existing alert configuration.
        
        Args:
            alert_id: ID of the alert configuration
            username: Username of the user
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            set_clauses = []
            params = {"alert_id": alert_id, "username": username}
            
            for key, value in updates.items():
                if key in ["threshold_value", "threshold_period", "notification_method", "is_active"]:
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
            
            if not set_clauses:
                return False
            
            query = f"""
            UPDATE alert_configurations 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :alert_id AND username = :username
            """
            
            db_manager.execute_query(query, params, database="accounts")
            
            logger.info(f"Updated alert configuration {alert_id} for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert configuration: {e}")
            return False
