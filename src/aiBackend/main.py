"""
Main FastAPI application for AI Backend service.
"""
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import uvicorn
from datetime import datetime

from config import settings
from auth import get_username_from_token, is_token_valid
from agents.orchestrator import orchestrator
from database import db_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Backend Service",
    description="AI-powered insights and analytics for Bank of Anthos",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class InsightResponse(BaseModel):
    success: bool
    insights: List[Dict[str, Any]] = []
    error: Optional[str] = None
    timestamp: str

class PreferenceRequest(BaseModel):
    preferences: Dict[str, Any]

class AlertConfigRequest(BaseModel):
    alert_type: str
    alert_name: str
    threshold_value: float
    threshold_period: str
    notification_method: str = "in_app"

class InteractionRequest(BaseModel):
    interaction_type: str
    insight_id: Optional[int] = None
    interaction_data: Optional[Dict[str, Any]] = None

# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Get current user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    
    if not is_token_valid(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = get_username_from_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Could not extract username from token")
    
    return username

# Health check endpoints
@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint."""
    try:
        # Check database connections
        db_manager.execute_query("SELECT 1", database="accounts")
        db_manager.execute_query("SELECT 1", database="ledger")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/healthy")
async def liveness_check():
    """Liveness probe endpoint."""
    return {"status": "healthy"}

@app.get("/version")
async def get_version():
    """Get service version."""
    return {"version": settings.version}

# Main AI endpoints
@app.post("/query", response_model=QueryResponse)
async def process_user_query(
    request: QueryRequest,
    username: str = Depends(get_current_user)
):
    """
    Process a natural language query from the user.
    """
    try:
        logger.info(f"Processing query for user {username}: {request.query}")
        
        result = await orchestrator.process_user_query(username, request.query)
        
        return QueryResponse(
            success=result["success"],
            data=result if result["success"] else None,
            error=result.get("error") if not result["success"] else None,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            error="Internal server error",
            timestamp=datetime.utcnow().isoformat()
        )

@app.get("/insights", response_model=InsightResponse)
async def get_user_insights(
    unread_only: bool = False,
    limit: int = 20,
    username: str = Depends(get_current_user)
):
    """
    Get AI insights for the user.
    """
    try:
        insights = db_manager.get_user_insights(username, limit=limit, unread_only=unread_only)
        
        return InsightResponse(
            success=True,
            insights=insights,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return InsightResponse(
            success=False,
            error="Internal server error",
            timestamp=datetime.utcnow().isoformat()
        )

@app.post("/insights/generate")
async def generate_daily_insights(username: str = Depends(get_current_user)):
    """
    Generate daily insights for the user.
    """
    try:
        insights = await orchestrator.generate_daily_insights(username)
        
        return {
            "success": True,
            "insights_generated": len(insights),
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating daily insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard")
async def get_dashboard_data(username: str = Depends(get_current_user)):
    """
    Get comprehensive dashboard data for the user.
    """
    try:
        dashboard_data = await orchestrator.get_user_dashboard_data(username)
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/preferences")
async def update_user_preferences(
    request: PreferenceRequest,
    username: str = Depends(get_current_user)
):
    """
    Update user preferences.
    """
    try:
        success = await orchestrator.update_user_preferences(username, request.preferences)
        
        return {
            "success": success,
            "message": "Preferences updated successfully" if success else "Failed to update preferences",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/preferences")
async def get_user_preferences(username: str = Depends(get_current_user)):
    """
    Get user preferences.
    """
    try:
        preferences = await orchestrator.user_preference.get_user_preferences(username)
        
        return {
            "success": True,
            "preferences": preferences,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/alerts")
async def create_alert_configuration(
    request: AlertConfigRequest,
    username: str = Depends(get_current_user)
):
    """
    Create a new alert configuration.
    """
    try:
        success = await orchestrator.alert_notification.create_alert_configuration(
            username=username,
            alert_type=request.alert_type,
            alert_name=request.alert_name,
            threshold_value=request.threshold_value,
            threshold_period=request.threshold_period,
            notification_method=request.notification_method
        )
        
        return {
            "success": success,
            "message": "Alert configuration created successfully" if success else "Failed to create alert configuration",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/alerts")
async def get_alert_configurations(username: str = Depends(get_current_user)):
    """
    Get user's alert configurations.
    """
    try:
        alerts = await orchestrator.alert_notification._get_user_alert_configs(username)
        
        return {
            "success": True,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alert configurations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/interactions")
async def log_user_interaction(
    request: InteractionRequest,
    username: str = Depends(get_current_user)
):
    """
    Log user interaction for learning.
    """
    try:
        interaction_id = await orchestrator.user_preference.log_interaction(
            username=username,
            interaction_type=request.interaction_type,
            insight_id=request.insight_id,
            interaction_data=request.interaction_data
        )
        
        return {
            "success": interaction_id is not None,
            "interaction_id": interaction_id,
            "message": "Interaction logged successfully" if interaction_id else "Failed to log interaction",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/insights/{insight_id}/read")
async def mark_insight_read(
    insight_id: int,
    username: str = Depends(get_current_user)
):
    """
    Mark an insight as read.
    """
    try:
        success = db_manager.mark_insight_read(insight_id, username)
        
        return {
            "success": success,
            "message": "Insight marked as read" if success else "Failed to mark insight as read",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error marking insight as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/recommendations")
async def get_personalized_recommendations(username: str = Depends(get_current_user)):
    """
    Get personalized recommendations for the user.
    """
    try:
        recommendations = await orchestrator.user_preference.get_personalized_recommendations(username)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=True
    )
