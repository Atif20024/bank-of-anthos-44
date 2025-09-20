"""
Vertex AI client for interacting with Gemini API.
"""
import logging
from typing import Optional, Dict, Any, List
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
from config import settings

logger = logging.getLogger(__name__)

class VertexAIClient:
    """Client for interacting with Vertex AI Gemini API."""
    
    def __init__(self):
        """Initialize Vertex AI client."""
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=settings.project_id,
                location=settings.vertex_ai_location
            )
            
            # Initialize the model
            self.model = GenerativeModel(settings.vertex_ai_model)
            logger.info(f"Vertex AI client initialized with model: {settings.vertex_ai_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {e}")
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using Gemini API.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated text or None if failed
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return None
    
    def generate_structured_response(self, prompt: str, response_format: str = "json") -> Optional[Dict[str, Any]]:
        """
        Generate structured response (JSON) using Gemini API.
        
        Args:
            prompt: Input prompt
            response_format: Expected response format
            
        Returns:
            Parsed JSON response or None if failed
        """
        try:
            # Add format instruction to prompt
            formatted_prompt = f"{prompt}\n\nPlease respond in valid JSON format."
            
            response_text = self.generate_text(formatted_prompt, max_tokens=2000)
            
            if response_text:
                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        logger.warning("No valid JSON found in response")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating structured response: {e}")
            return None
    
    def analyze_data(self, data: List[Dict[str, Any]], analysis_type: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        Analyze data using Gemini API.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis (e.g., "spending_trends", "category_analysis")
            context: Additional context for analysis
            
        Returns:
            Analysis results or None if failed
        """
        try:
            # Convert data to string for prompt
            data_str = json.dumps(data, indent=2, default=str)
            
            prompt = f"""
            Analyze the following banking data for {analysis_type}:
            
            Context: {context}
            
            Data:
            {data_str}
            
            Please provide:
            1. Key insights and patterns
            2. Trends and changes over time
            3. Recommendations for the user
            4. Any concerning patterns or opportunities
            
            Format your response as JSON with the following structure:
            {{
                "insights": ["insight1", "insight2", ...],
                "trends": ["trend1", "trend2", ...],
                "recommendations": ["rec1", "rec2", ...],
                "concerns": ["concern1", "concern2", ...],
                "summary": "Overall summary of the analysis"
            }}
            """
            
            return self.generate_structured_response(prompt)
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return None
    
    def generate_sql_query(self, natural_language_query: str, schema_info: str) -> Optional[str]:
        """
        Generate SQL query from natural language using Gemini API.
        
        Args:
            natural_language_query: User's question in natural language
            schema_info: Database schema information
            
        Returns:
            SQL query string or None if failed
        """
        try:
            prompt = f"""
            Convert the following natural language query to SQL:
            
            Query: {natural_language_query}
            
            Database Schema:
            {schema_info}
            
            Rules:
            1. Only use the tables and columns mentioned in the schema
            2. Use proper SQL syntax for PostgreSQL
            3. Include appropriate WHERE clauses for filtering
            4. Use proper JOINs when needed
            5. Return only the SQL query, no explanations
            
            SQL Query:
            """
            
            response = self.generate_text(prompt, max_tokens=500, temperature=0.3)
            
            if response:
                # Clean up the response to extract just the SQL
                sql_query = response.strip()
                # Remove any markdown formatting
                if sql_query.startswith('```sql'):
                    sql_query = sql_query[6:]
                if sql_query.endswith('```'):
                    sql_query = sql_query[:-3]
                return sql_query.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return None
    
    def generate_insight_description(self, data: Dict[str, Any], insight_type: str) -> Optional[str]:
        """
        Generate human-readable description for an insight.
        
        Args:
            data: Data that led to the insight
            insight_type: Type of insight
            
        Returns:
            Description string or None if failed
        """
        try:
            data_str = json.dumps(data, indent=2, default=str)
            
            prompt = f"""
            Generate a clear, actionable description for this {insight_type} insight:
            
            Data: {data_str}
            
            Requirements:
            1. Write in a friendly, conversational tone
            2. Be specific about numbers and time periods
            3. Provide actionable advice
            4. Keep it concise (2-3 sentences)
            5. Use positive language when possible
            
            Description:
            """
            
            return self.generate_text(prompt, max_tokens=200, temperature=0.7)
            
        except Exception as e:
            logger.error(f"Error generating insight description: {e}")
            return None

# Global Vertex AI client instance
vertex_ai_client = VertexAIClient()
