# AI Backend Service

The AI Backend service provides intelligent insights and analytics for the Bank of Anthos application using Google Vertex AI and Gemini API.

## Features

### 🤖 AI Agents
- **Orchestrator Agent**: Main coordinator that manages all other agents
- **Data Analyst Agent**: Generates SQL queries from natural language
- **Insight Generator Agent**: Creates actionable insights from spending data
- **User Preference Agent**: Learns from user interactions and manages preferences
- **Query Understanding Agent**: Processes natural language queries
- **Data Visualization Agent**: Creates appropriate charts and visualizations
- **Alert/Notification Agent**: Monitors spending patterns and generates alerts

### 📊 Capabilities
- Natural language query processing
- Spending trend analysis
- Category-based spending breakdown
- Improvement tracking and recommendations
- Personalized insights based on user behavior
- Real-time alert generation
- Interactive dashboard data

### 🔧 Technology Stack
- **Framework**: FastAPI (Python)
- **AI/ML**: Google Vertex AI with Gemini API
- **Database**: PostgreSQL (Cloud SQL)
- **Deployment**: Google Kubernetes Engine (GKE)
- **Authentication**: JWT tokens
- **Monitoring**: Google Cloud Logging

## API Endpoints

### Core AI Endpoints
- `POST /query` - Process natural language queries
- `GET /insights` - Get user insights
- `POST /insights/generate` - Generate daily insights
- `GET /dashboard` - Get comprehensive dashboard data

### User Management
- `GET /preferences` - Get user preferences
- `POST /preferences` - Update user preferences
- `POST /interactions` - Log user interactions

### Alerts
- `GET /alerts` - Get alert configurations
- `POST /alerts` - Create alert configuration

### Utility
- `GET /recommendations` - Get personalized recommendations
- `PUT /insights/{id}/read` - Mark insight as read

## Database Schema

### New Tables Added to accounts-db

#### user_preferences
Stores user preferences for AI insights and personalization.

#### ai_insights
Stores generated AI insights with metadata and visualization configs.

#### user_interactions
Tracks user interactions for learning and personalization.

#### alert_configurations
Stores user-defined alert thresholds and configurations.

## Environment Variables

```bash
# Service Configuration
VERSION=v1.0.0
PORT=8080
LOG_LEVEL=INFO

# Database Configuration
ACCOUNTS_DB_URI=postgresql://...
LEDGER_DB_URI=postgresql://...

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro

# JWT Configuration
PUB_KEY_PATH=/etc/secrets/jwtRS256.key.pub
LOCAL_ROUTING_NUM=123456789

# AI Backend Configuration
MAX_RETRIES=1
INSIGHT_EXPIRY_DAYS=7
MAX_INSIGHTS_PER_USER=50
```

## Deployment

### Prerequisites
- Google Cloud Project with Vertex AI enabled
- Cloud SQL instances for accounts and ledger databases
- GKE cluster
- Workload Identity configured

### 1. Database Initialization
```bash
# Run the database initialization script
python init_db.py
```

### 2. Build and Deploy
```bash
# Using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Using Skaffold
skaffold run --profile dev
```

### 3. Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/aibackend.yaml
```

## Usage Examples

### Natural Language Query
```bash
curl -X POST "https://aibackend.example.com/query" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me my coffee spending this month"}'
```

### Get Insights
```bash
curl -X GET "https://aibackend.example.com/insights" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Set Alert Configuration
```bash
curl -X POST "https://aibackend.example.com/alerts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "spending_threshold",
    "alert_name": "Daily Coffee Budget",
    "threshold_value": 20.0,
    "threshold_period": "daily",
    "notification_method": "in_app"
  }'
```

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ACCOUNTS_DB_URI="postgresql://..."
export LEDGER_DB_URI="postgresql://..."
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Run the service
python main.py
```

### Testing
```bash
# Run tests
pytest test/

# Run with coverage
pytest --cov=. test/
```

## Monitoring and Logging

The service integrates with Google Cloud Logging and Monitoring for:
- Request/response logging
- Error tracking
- Performance metrics
- AI model usage tracking

## Security

- JWT token authentication
- Database connection encryption
- Secure secret management
- Input validation and sanitization
- SQL injection prevention

## Contributing

1. Follow the existing code structure
2. Add appropriate logging
3. Include error handling
4. Update documentation
5. Add tests for new features

## License

Copyright 2024 Google LLC. Licensed under the Apache License, Version 2.0.
