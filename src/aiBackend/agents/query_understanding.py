"""
Query Understanding Agent - Processes natural language queries.
"""
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from vertex_ai_client import vertex_ai_client

logger = logging.getLogger(__name__)

class QueryUnderstandingAgent:
    """Agent responsible for understanding natural language queries."""
    
    def __init__(self):
        """Initialize query understanding agent."""
        self.time_patterns = {
            "today": 0,
            "yesterday": 1,
            "this week": 7,
            "last week": 14,
            "this month": 30,
            "last month": 60,
            "this year": 365,
            "last year": 730
        }
        
        self.category_keywords = {
            "food": ["food", "restaurant", "dining", "coffee", "lunch", "dinner", "grocery"],
            "entertainment": ["movie", "game", "entertainment", "netflix", "spotify", "subscription"],
            "transportation": ["gas", "fuel", "uber", "lyft", "taxi", "transport", "parking"],
            "shopping": ["amazon", "store", "shopping", "retail", "clothes", "clothing"],
            "utilities": ["electric", "water", "internet", "phone", "utility", "bill"],
            "healthcare": ["doctor", "pharmacy", "medical", "health", "hospital"],
            "education": ["school", "university", "course", "book", "education", "learning"]
        }
        
        logger.info("Query Understanding Agent initialized")
    
    async def understand_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Understand and parse a natural language query.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Parsed query intent or None if failed
        """
        try:
            query_lower = query.lower().strip()
            
            # Use AI to understand the query
            ai_understanding = await self._ai_understand_query(query)
            
            # Combine AI understanding with rule-based parsing
            intent = {
                "original_query": query,
                "analysis_type": self._determine_analysis_type(query_lower, ai_understanding),
                "time_period": self._extract_time_period(query_lower, ai_understanding),
                "categories": self._extract_categories(query_lower, ai_understanding),
                "needs_visualization": self._needs_visualization(query_lower, ai_understanding),
                "priority": self._determine_priority(query_lower, ai_understanding),
                "confidence": ai_understanding.get("confidence", 0.8) if ai_understanding else 0.7
            }
            
            logger.info(f"Understood query: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error understanding query: {e}")
            return None
    
    async def _ai_understand_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Use AI to understand the query.
        
        Args:
            query: Natural language query
            
        Returns:
            AI understanding of the query
        """
        try:
            prompt = f"""
            Analyze this user query about their banking/spending data:
            
            Query: "{query}"
            
            Determine:
            1. What type of analysis they want (spending_trends, category_analysis, improvement, general)
            2. What time period they're interested in (today, this week, this month, etc.)
            3. What spending categories they care about (food, entertainment, shopping, etc.)
            4. Whether they want visualizations (charts, graphs)
            5. How urgent/important this request is (1-5 scale)
            6. Your confidence in understanding this query (0-1 scale)
            
            Respond in JSON format:
            {{
                "analysis_type": "spending_trends",
                "time_period": "this_month",
                "categories": ["food", "entertainment"],
                "needs_visualization": true,
                "priority": 3,
                "confidence": 0.9,
                "intent_summary": "User wants to see spending trends for food and entertainment this month"
            }}
            """
            
            return vertex_ai_client.generate_structured_response(prompt)
            
        except Exception as e:
            logger.error(f"Error in AI query understanding: {e}")
            return None
    
    def _determine_analysis_type(self, query: str, ai_understanding: Optional[Dict[str, Any]]) -> str:
        """Determine the type of analysis requested."""
        if ai_understanding and "analysis_type" in ai_understanding:
            return ai_understanding["analysis_type"]
        
        # Rule-based fallback
        if any(word in query for word in ["trend", "over time", "change", "increase", "decrease"]):
            return "spending_trends"
        elif any(word in query for word in ["category", "breakdown", "spend on", "where"]):
            return "category_analysis"
        elif any(word in query for word in ["improve", "better", "worse", "progress", "doing"]):
            return "improvement"
        else:
            return "general"
    
    def _extract_time_period(self, query: str, ai_understanding: Optional[Dict[str, Any]]) -> str:
        """Extract time period from query."""
        if ai_understanding and "time_period" in ai_understanding:
            return ai_understanding["time_period"]
        
        # Rule-based fallback
        for period, days in self.time_patterns.items():
            if period in query:
                return period.replace(" ", "_")
        
        # Default to this month
        return "this_month"
    
    def _extract_categories(self, query: str, ai_understanding: Optional[Dict[str, Any]]) -> List[str]:
        """Extract spending categories from query."""
        if ai_understanding and "categories" in ai_understanding:
            return ai_understanding["categories"]
        
        # Rule-based fallback
        found_categories = []
        for category, keywords in self.category_keywords.items():
            if any(keyword in query for keyword in keywords):
                found_categories.append(category)
        
        return found_categories
    
    def _needs_visualization(self, query: str, ai_understanding: Optional[Dict[str, Any]]) -> bool:
        """Determine if query needs visualization."""
        if ai_understanding and "needs_visualization" in ai_understanding:
            return ai_understanding["needs_visualization"]
        
        # Rule-based fallback
        visualization_keywords = ["chart", "graph", "visual", "show", "plot", "display"]
        return any(keyword in query for keyword in visualization_keywords)
    
    def _determine_priority(self, query: str, ai_understanding: Optional[Dict[str, Any]]) -> int:
        """Determine query priority."""
        if ai_understanding and "priority" in ai_understanding:
            return ai_understanding["priority"]
        
        # Rule-based fallback
        urgent_keywords = ["urgent", "important", "asap", "quickly", "immediately"]
        if any(keyword in query for keyword in urgent_keywords):
            return 5
        
        return 3  # Default priority
    
    async def clarify_ambiguous_query(self, query: str, possible_intents: List[Dict[str, Any]]) -> str:
        """
        Generate clarification questions for ambiguous queries.
        
        Args:
            query: Original ambiguous query
            possible_intents: List of possible interpretations
            
        Returns:
            Clarification question
        """
        try:
            prompt = f"""
            The user asked: "{query}"
            
            I found {len(possible_intents)} possible interpretations:
            {possible_intents}
            
            Generate a helpful clarification question to help the user specify what they want.
            Be friendly and offer 2-3 specific options.
            
            Example: "I can help you with that! Did you want to see:
            1. Your spending trends over time
            2. A breakdown by spending categories
            3. How your spending has improved recently"
            """
            
            clarification = vertex_ai_client.generate_text(prompt, max_tokens=200)
            return clarification or "Could you please be more specific about what you'd like to see?"
            
        except Exception as e:
            logger.error(f"Error generating clarification: {e}")
            return "Could you please be more specific about what you'd like to see?"
    
    async def suggest_related_queries(self, query: str, username: str) -> List[str]:
        """
        Suggest related queries based on the current query and user history.
        
        Args:
            query: Current query
            username: Username for context
            
        Returns:
            List of suggested related queries
        """
        try:
            prompt = f"""
            Based on this user query: "{query}"
            
            Suggest 3-5 related questions the user might want to ask about their spending data.
            Make them specific and actionable.
            
            Examples:
            - "Show me my coffee spending this month"
            - "How much did I spend on entertainment last week?"
            - "Compare my spending this month vs last month"
            - "What's my biggest expense category?"
            - "Am I spending more or less than usual?"
            
            Return as a JSON array of strings.
            """
            
            suggestions = vertex_ai_client.generate_structured_response(prompt)
            
            if suggestions and isinstance(suggestions, list):
                return suggestions[:5]  # Limit to 5 suggestions
            
            # Fallback suggestions
            return [
                "Show me my spending trends this month",
                "What categories am I spending most on?",
                "How am I doing compared to last month?",
                "What are my biggest expenses?",
                "Show me my recent transactions"
            ]
            
        except Exception as e:
            logger.error(f"Error generating related queries: {e}")
            return []
    
    def get_time_period_days(self, time_period: str) -> int:
        """
        Convert time period string to number of days.
        
        Args:
            time_period: Time period string (e.g., "this_week", "last_month")
            
        Returns:
            Number of days
        """
        period_mapping = {
            "today": 1,
            "yesterday": 1,
            "this_week": 7,
            "last_week": 14,
            "this_month": 30,
            "last_month": 60,
            "this_year": 365,
            "last_year": 730
        }
        
        return period_mapping.get(time_period, 30)  # Default to 30 days
    
    def get_time_period_dates(self, time_period: str) -> tuple:
        """
        Get start and end dates for a time period.
        
        Args:
            time_period: Time period string
            
        Returns:
            Tuple of (start_date, end_date)
        """
        days = self.get_time_period_days(time_period)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return start_date, end_date
