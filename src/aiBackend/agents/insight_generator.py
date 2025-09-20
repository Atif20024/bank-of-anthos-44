"""
Insight Generator Agent - Creates actionable insights from data.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from vertex_ai_client import vertex_ai_client
from database import db_manager

logger = logging.getLogger(__name__)

class InsightGeneratorAgent:
    """Agent responsible for generating actionable insights from data."""
    
    def __init__(self):
        """Initialize insight generator agent."""
        logger.info("Insight Generator Agent initialized")
    
    async def generate_insights(self, data: List[Dict[str, Any]], query_intent: Dict[str, Any], 
                              username: str, user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate insights from data based on query intent.
        
        Args:
            data: Data to analyze
            query_intent: Intent of the user's query
            username: Username of the user
            user_preferences: User's preferences
            
        Returns:
            List of generated insights
        """
        try:
            insights = []
            analysis_type = query_intent.get("analysis_type", "general")
            
            if analysis_type == "spending_trends":
                insights.extend(await self._analyze_spending_trends(data, username, user_preferences))
            elif analysis_type == "category_analysis":
                insights.extend(await self._analyze_categories(data, username, user_preferences))
            elif analysis_type == "improvement":
                insights.extend(await self._analyze_improvements(data, username, user_preferences))
            else:
                # General analysis
                insights.extend(await self._general_analysis(data, username, user_preferences))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def analyze_spending_trends(self, transactions: List[Dict[str, Any]], 
                                    username: str, user_preferences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze spending trends for a user.
        
        Args:
            transactions: User's transaction data
            username: Username of the user
            user_preferences: User's preferences
            
        Returns:
            Spending trend insight or None
        """
        try:
            if not transactions:
                return None
            
            # Analyze data using Vertex AI
            analysis_result = vertex_ai_client.analyze_data(
                transactions, 
                "spending_trends",
                f"Analyze spending trends for user {username}"
            )
            
            if not analysis_result:
                return None
            
            # Generate insight description
            description = vertex_ai_client.generate_insight_description(
                analysis_result, 
                "spending_trends"
            )
            
            if not description:
                description = "Your spending patterns show interesting trends over time."
            
            return {
                "type": "spending_trends",
                "title": "Spending Trend Analysis",
                "description": description,
                "data": analysis_result,
                "priority": 2,
                "visualization_config": {
                    "chart_type": "line",
                    "x_axis": "date",
                    "y_axis": "amount"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending trends: {e}")
            return None
    
    async def analyze_spending_categories(self, transactions: List[Dict[str, Any]], 
                                        username: str, user_preferences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze spending by categories.
        
        Args:
            transactions: User's transaction data
            username: Username of the user
            user_preferences: User's preferences
            
        Returns:
            Category analysis insight or None
        """
        try:
            if not transactions:
                return None
            
            # Categorize transactions by amount ranges
            categories = {
                "Small purchases (<$50)": 0,
                "Medium purchases ($50-$200)": 0,
                "Large purchases ($200-$500)": 0,
                "Very large purchases (>$500)": 0
            }
            
            total_amount = 0
            for transaction in transactions:
                amount = transaction.get("amount", 0)
                total_amount += amount
                
                if amount < 50:
                    categories["Small purchases (<$50)"] += amount
                elif amount < 200:
                    categories["Medium purchases ($50-$200)"] += amount
                elif amount < 500:
                    categories["Large purchases ($200-$500)"] += amount
                else:
                    categories["Very large purchases (>$500)"] += amount
            
            # Find top category
            top_category = max(categories, key=categories.get)
            top_amount = categories[top_category]
            top_percentage = (top_amount / total_amount * 100) if total_amount > 0 else 0
            
            # Generate insight using AI
            analysis_data = {
                "categories": categories,
                "total_amount": total_amount,
                "top_category": top_category,
                "top_percentage": top_percentage
            }
            
            description = vertex_ai_client.generate_insight_description(
                analysis_data, 
                "category_analysis"
            )
            
            if not description:
                description = f"Your spending is highest in {top_category} at ${top_amount:.2f} ({top_percentage:.1f}% of total spending)."
            
            return {
                "type": "category_analysis",
                "title": "Spending Category Breakdown",
                "description": description,
                "data": analysis_data,
                "priority": 2,
                "visualization_config": {
                    "chart_type": "pie",
                    "data_key": "categories"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending categories: {e}")
            return None
    
    async def analyze_improvements(self, transactions: List[Dict[str, Any]], 
                                 username: str, user_preferences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Analyze improvements in spending patterns.
        
        Args:
            transactions: User's transaction data
            username: Username of the user
            user_preferences: User's preferences
            
        Returns:
            Improvement analysis insight or None
        """
        try:
            if len(transactions) < 10:  # Need enough data for comparison
                return None
            
            # Split transactions into two periods for comparison
            mid_point = len(transactions) // 2
            recent_transactions = transactions[:mid_point]
            older_transactions = transactions[mid_point:]
            
            # Calculate metrics for both periods
            recent_total = sum(t.get("amount", 0) for t in recent_transactions)
            older_total = sum(t.get("amount", 0) for t in older_transactions)
            
            recent_avg = recent_total / len(recent_transactions) if recent_transactions else 0
            older_avg = older_total / len(older_transactions) if older_transactions else 0
            
            # Calculate improvement percentage
            if older_avg > 0:
                improvement_pct = ((older_avg - recent_avg) / older_avg) * 100
            else:
                improvement_pct = 0
            
            # Determine if it's improvement or concern
            is_improvement = improvement_pct > 5  # 5% threshold
            trend_direction = "decreased" if is_improvement else "increased"
            
            analysis_data = {
                "recent_period": {
                    "total": recent_total,
                    "average": recent_avg,
                    "count": len(recent_transactions)
                },
                "older_period": {
                    "total": older_total,
                    "average": older_avg,
                    "count": len(older_transactions)
                },
                "improvement_percentage": improvement_pct,
                "is_improvement": is_improvement,
                "trend_direction": trend_direction
            }
            
            # Generate insight description
            description = vertex_ai_client.generate_insight_description(
                analysis_data, 
                "improvement_analysis"
            )
            
            if not description:
                if is_improvement:
                    description = f"Great news! Your average spending has {trend_direction} by {abs(improvement_pct):.1f}% compared to the previous period."
                else:
                    description = f"Your average spending has {trend_direction} by {abs(improvement_pct):.1f}% compared to the previous period. Consider reviewing your spending habits."
            
            return {
                "type": "improvement_analysis",
                "title": "Spending Improvement Analysis",
                "description": description,
                "data": analysis_data,
                "priority": 3 if is_improvement else 2,
                "visualization_config": {
                    "chart_type": "bar",
                    "x_axis": "period",
                    "y_axis": "amount"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing improvements: {e}")
            return None
    
    async def _analyze_spending_trends(self, data: List[Dict[str, Any]], username: str, 
                                     user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze spending trends from data."""
        insights = []
        
        trend_insight = await self.analyze_spending_trends(data, username, user_preferences)
        if trend_insight:
            insights.append(trend_insight)
        
        return insights
    
    async def _analyze_categories(self, data: List[Dict[str, Any]], username: str, 
                                user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze spending categories from data."""
        insights = []
        
        category_insight = await self.analyze_spending_categories(data, username, user_preferences)
        if category_insight:
            insights.append(category_insight)
        
        return insights
    
    async def _analyze_improvements(self, data: List[Dict[str, Any]], username: str, 
                                  user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze improvements from data."""
        insights = []
        
        improvement_insight = await self.analyze_improvements(data, username, user_preferences)
        if improvement_insight:
            insights.append(improvement_insight)
        
        return insights
    
    async def _general_analysis(self, data: List[Dict[str, Any]], username: str, 
                              user_preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform general analysis on data."""
        insights = []
        
        # Try all analysis types
        trend_insight = await self.analyze_spending_trends(data, username, user_preferences)
        if trend_insight:
            insights.append(trend_insight)
        
        category_insight = await self.analyze_spending_categories(data, username, user_preferences)
        if category_insight:
            insights.append(category_insight)
        
        improvement_insight = await self.analyze_improvements(data, username, user_preferences)
        if improvement_insight:
            insights.append(improvement_insight)
        
        return insights
