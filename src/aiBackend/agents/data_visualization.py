"""
Data Visualization Agent - Creates appropriate visualizations for data.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from vertex_ai_client import vertex_ai_client

logger = logging.getLogger(__name__)

class DataVisualizationAgent:
    """Agent responsible for creating data visualizations."""
    
    def __init__(self):
        """Initialize data visualization agent."""
        self.chart_types = {
            "line": "Line chart for trends over time",
            "bar": "Bar chart for categorical comparisons",
            "pie": "Pie chart for proportional data",
            "scatter": "Scatter plot for correlations",
            "area": "Area chart for cumulative data",
            "histogram": "Histogram for distribution analysis"
        }
        logger.info("Data Visualization Agent initialized")
    
    async def create_visualizations(self, data: List[Dict[str, Any]], 
                                  insights: List[Dict[str, Any]], 
                                  query_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create visualizations based on data and insights.
        
        Args:
            data: Raw data to visualize
            insights: Generated insights
            query_intent: User's query intent
            
        Returns:
            List of visualization configurations
        """
        try:
            visualizations = []
            
            # Determine what visualizations to create
            if query_intent.get("needs_visualization", False):
                # Create visualizations based on query intent
                viz_configs = await self._create_visualizations_for_intent(data, query_intent)
                visualizations.extend(viz_configs)
            
            # Create visualizations for insights
            for insight in insights:
                if insight.get("visualization_config"):
                    viz_config = await self._enhance_visualization_config(
                        insight["visualization_config"], 
                        data, 
                        insight
                    )
                    visualizations.append(viz_config)
            
            logger.info(f"Created {len(visualizations)} visualizations")
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            return []
    
    async def _create_visualizations_for_intent(self, data: List[Dict[str, Any]], 
                                              query_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create visualizations based on query intent."""
        visualizations = []
        analysis_type = query_intent.get("analysis_type", "general")
        
        if analysis_type == "spending_trends":
            viz = await self._create_trend_visualization(data, query_intent)
            if viz:
                visualizations.append(viz)
        
        elif analysis_type == "category_analysis":
            viz = await self._create_category_visualization(data, query_intent)
            if viz:
                visualizations.append(viz)
        
        elif analysis_type == "improvement":
            viz = await self._create_improvement_visualization(data, query_intent)
            if viz:
                visualizations.append(viz)
        
        else:
            # General visualization
            viz = await self._create_general_visualization(data, query_intent)
            if viz:
                visualizations.append(viz)
        
        return visualizations
    
    async def _create_trend_visualization(self, data: List[Dict[str, Any]], 
                                        query_intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create trend visualization."""
        try:
            # Check if data has time-based information
            if not data or "timestamp" not in data[0]:
                return None
            
            # Use AI to determine best visualization approach
            prompt = f"""
            Create a visualization configuration for spending trends data:
            
            Data sample: {data[:5]}
            Query intent: {query_intent}
            
            Determine:
            1. Best chart type (line, area, bar)
            2. X-axis configuration (time field)
            3. Y-axis configuration (amount field)
            4. Color scheme
            5. Title and labels
            
            Respond in JSON format with visualization configuration.
            """
            
            config = vertex_ai_client.generate_structured_response(prompt)
            
            if config:
                return {
                    "id": f"trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "trend_analysis",
                    "chart_type": config.get("chart_type", "line"),
                    "title": config.get("title", "Spending Trends"),
                    "x_axis": {
                        "field": config.get("x_axis_field", "timestamp"),
                        "label": config.get("x_axis_label", "Date"),
                        "type": "datetime"
                    },
                    "y_axis": {
                        "field": config.get("y_axis_field", "amount"),
                        "label": config.get("y_axis_label", "Amount ($)"),
                        "type": "number"
                    },
                    "data": data,
                    "color_scheme": config.get("color_scheme", "blue"),
                    "description": "Shows your spending patterns over time"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating trend visualization: {e}")
            return None
    
    async def _create_category_visualization(self, data: List[Dict[str, Any]], 
                                           query_intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create category visualization."""
        try:
            # Use AI to determine best visualization approach
            prompt = f"""
            Create a visualization configuration for spending category data:
            
            Data sample: {data[:5]}
            Query intent: {query_intent}
            
            Determine:
            1. Best chart type (pie, bar, donut)
            2. Category field
            3. Value field
            4. Color scheme
            5. Title and labels
            
            Respond in JSON format with visualization configuration.
            """
            
            config = vertex_ai_client.generate_structured_response(prompt)
            
            if config:
                return {
                    "id": f"category_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "category_analysis",
                    "chart_type": config.get("chart_type", "pie"),
                    "title": config.get("title", "Spending by Category"),
                    "category_field": config.get("category_field", "category"),
                    "value_field": config.get("value_field", "amount"),
                    "data": data,
                    "color_scheme": config.get("color_scheme", "rainbow"),
                    "description": "Shows how your spending is distributed across categories"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating category visualization: {e}")
            return None
    
    async def _create_improvement_visualization(self, data: List[Dict[str, Any]], 
                                              query_intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create improvement visualization."""
        try:
            # Use AI to determine best visualization approach
            prompt = f"""
            Create a visualization configuration for spending improvement data:
            
            Data sample: {data[:5]}
            Query intent: {query_intent}
            
            Determine:
            1. Best chart type (bar, line, area)
            2. Comparison fields
            3. Color scheme (use green for improvements, red for concerns)
            4. Title and labels
            
            Respond in JSON format with visualization configuration.
            """
            
            config = vertex_ai_client.generate_structured_response(prompt)
            
            if config:
                return {
                    "id": f"improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "improvement_analysis",
                    "chart_type": config.get("chart_type", "bar"),
                    "title": config.get("title", "Spending Improvement"),
                    "comparison_fields": config.get("comparison_fields", ["current", "previous"]),
                    "data": data,
                    "color_scheme": config.get("color_scheme", "improvement"),
                    "description": "Shows how your spending has improved over time"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating improvement visualization: {e}")
            return None
    
    async def _create_general_visualization(self, data: List[Dict[str, Any]], 
                                          query_intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create general visualization."""
        try:
            # Use AI to determine best visualization approach
            prompt = f"""
            Create a visualization configuration for general spending data:
            
            Data sample: {data[:5]}
            Query intent: {query_intent}
            
            Determine:
            1. Best chart type based on data structure
            2. Appropriate fields for axes
            3. Color scheme
            4. Title and labels
            
            Respond in JSON format with visualization configuration.
            """
            
            config = vertex_ai_client.generate_structured_response(prompt)
            
            if config:
                return {
                    "id": f"general_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "general_analysis",
                    "chart_type": config.get("chart_type", "bar"),
                    "title": config.get("title", "Spending Analysis"),
                    "x_axis": config.get("x_axis", {}),
                    "y_axis": config.get("y_axis", {}),
                    "data": data,
                    "color_scheme": config.get("color_scheme", "blue"),
                    "description": "Shows your spending data in an easy-to-understand format"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating general visualization: {e}")
            return None
    
    async def _enhance_visualization_config(self, base_config: Dict[str, Any], 
                                          data: List[Dict[str, Any]], 
                                          insight: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance visualization configuration with data and insight context."""
        try:
            enhanced_config = base_config.copy()
            
            # Add data
            enhanced_config["data"] = data
            
            # Add insight context
            enhanced_config["insight_id"] = insight.get("id")
            enhanced_config["insight_type"] = insight.get("type")
            
            # Generate description if not present
            if "description" not in enhanced_config:
                enhanced_config["description"] = insight.get("description", "Data visualization")
            
            # Add timestamp
            enhanced_config["created_at"] = datetime.now().isoformat()
            
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Error enhancing visualization config: {e}")
            return base_config
    
    async def suggest_visualization_improvements(self, visualization: Dict[str, Any], 
                                               user_feedback: str) -> Dict[str, Any]:
        """
        Suggest improvements to visualization based on user feedback.
        
        Args:
            visualization: Current visualization configuration
            user_feedback: User's feedback about the visualization
            
        Returns:
            Improved visualization configuration
        """
        try:
            prompt = f"""
            Improve this visualization based on user feedback:
            
            Current visualization: {visualization}
            User feedback: "{user_feedback}"
            
            Suggest improvements for:
            1. Chart type
            2. Color scheme
            3. Labels and titles
            4. Data presentation
            5. Overall clarity
            
            Respond with an improved visualization configuration in JSON format.
            """
            
            improved_config = vertex_ai_client.generate_structured_response(prompt)
            
            if improved_config:
                # Merge improvements with existing config
                enhanced_config = visualization.copy()
                enhanced_config.update(improved_config)
                return enhanced_config
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error suggesting visualization improvements: {e}")
            return visualization
    
    def get_chart_type_description(self, chart_type: str) -> str:
        """Get description for a chart type."""
        return self.chart_types.get(chart_type, "Custom chart")
    
    def validate_visualization_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate visualization configuration.
        
        Args:
            config: Visualization configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ["id", "type", "chart_type", "title", "data"]
            
            for field in required_fields:
                if field not in config:
                    logger.warning(f"Missing required field in visualization config: {field}")
                    return False
            
            if not config["data"]:
                logger.warning("Empty data in visualization config")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating visualization config: {e}")
            return False
