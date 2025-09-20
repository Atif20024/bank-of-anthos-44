# AI Backend Testing Guide

This guide will help you test and run the AI Backend service both locally and in production.

## 🚀 Quick Start

### 1. Initial Setup
```bash
cd src/aiBackend
./setup.sh
```

### 2. Configure Environment
Edit the `.env` file with your actual values:
```bash
# Update these with your actual values
ACCOUNTS_DB_URI=postgresql://user:password@your-db-host:5432/accounts
LEDGER_DB_URI=postgresql://user:password@your-db-host:5432/ledger
GOOGLE_CLOUD_PROJECT=your-actual-project-id
```

## 🧪 Local Testing

### Option 1: Test Individual Components
```bash
# Test database connections
python -c "from database import db_manager; print('DB OK')"

# Test Vertex AI client
python -c "from vertex_ai_client import vertex_ai_client; print('Vertex AI OK')"

# Test individual agents
python -c "from agents.query_understanding import QueryUnderstandingAgent; print('Query Agent OK')"
```

### Option 2: Run Comprehensive Tests
```bash
# Run the test suite
python test/test_aibackend.py
```

### Option 3: Test with Mock Data
```bash
# Create a simple test script
cat > test_simple.py << 'EOF'
import asyncio
from agents.query_understanding import QueryUnderstandingAgent

async def test():
    agent = QueryUnderstandingAgent()
    result = await agent.understand_query("Show me my coffee spending this month")
    print(f"Query result: {result}")

asyncio.run(test())
EOF

python test_simple.py
```

## 🏃‍♂️ Running Locally

### 1. Start the Service
```bash
# Make sure your environment variables are set
export ACCOUNTS_DB_URI="postgresql://user:password@localhost:5432/accounts"
export LEDGER_DB_URI="postgresql://user:password@localhost:5432/ledger"
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Start the service
python main.py
```

### 2. Test the API
```bash
# Health check
curl http://localhost:8080/healthy

# Ready check
curl http://localhost:8080/ready

# Version info
curl http://localhost:8080/version
```

### 3. Test with Authentication
```bash
# Get a JWT token from your userservice
JWT_TOKEN="your-jwt-token-here"

# Test query endpoint
curl -X POST "http://localhost:8080/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me my spending this month"}'

# Test insights endpoint
curl -X GET "http://localhost:8080/insights" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## 🐳 Docker Testing

### 1. Build Docker Image
```bash
docker build -t aibackend:test .
```

### 2. Run with Environment Variables
```bash
docker run -p 8080:8080 \
  -e ACCOUNTS_DB_URI="postgresql://user:password@host.docker.internal:5432/accounts" \
  -e LEDGER_DB_URI="postgresql://user:password@host.docker.internal:5432/ledger" \
  -e GOOGLE_CLOUD_PROJECT="your-project-id" \
  aibackend:test
```

### 3. Test Docker Container
```bash
curl http://localhost:8080/healthy
```

## ☸️ Kubernetes Testing

### 1. Deploy to GKE
```bash
# Make sure you're authenticated with gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy using the script
./deploy.sh
```

### 2. Test in Kubernetes
```bash
# Port forward to test locally
kubectl port-forward service/aibackend 8080:8080

# Test the service
curl http://localhost:8080/healthy
```

### 3. Check Logs
```bash
# View logs
kubectl logs -l app=aibackend

# Follow logs
kubectl logs -f deployment/aibackend
```

## 🔍 Debugging

### 1. Check Database Connection
```bash
python -c "
from database import db_manager
try:
    result = db_manager.execute_query('SELECT 1', database='accounts')
    print('Accounts DB: OK')
except Exception as e:
    print(f'Accounts DB Error: {e}')

try:
    result = db_manager.execute_query('SELECT 1', database='ledger')
    print('Ledger DB: OK')
except Exception as e:
    print(f'Ledger DB Error: {e}')
"
```

### 2. Check Vertex AI Access
```bash
python -c "
from vertex_ai_client import vertex_ai_client
try:
    result = vertex_ai_client.generate_text('Hello, test message')
    print(f'Vertex AI: OK - {result}')
except Exception as e:
    print(f'Vertex AI Error: {e}')
"
```

### 3. Check JWT Authentication
```bash
python -c "
from auth import is_token_valid
# Test with a sample token
token = 'your-test-token'
print(f'JWT Test: {is_token_valid(token)}')
"
```

## 📊 API Testing Examples

### 1. Natural Language Queries
```bash
# Coffee spending
curl -X POST "http://localhost:8080/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How much did I spend on coffee this month?"}'

# Spending trends
curl -X POST "http://localhost:8080/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me my spending trends over the last 3 months"}'

# Category analysis
curl -X POST "http://localhost:8080/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What categories am I spending most on?"}'
```

### 2. Dashboard Data
```bash
# Get comprehensive dashboard data
curl -X GET "http://localhost:8080/dashboard" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 3. User Preferences
```bash
# Get preferences
curl -X GET "http://localhost:8080/preferences" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Set preferences
curl -X POST "http://localhost:8080/preferences" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "spending_category": {
        "coffee": {"enabled": true, "threshold": 50.0},
        "food": {"enabled": true, "threshold": 200.0}
      }
    }
  }'
```

### 4. Alert Configuration
```bash
# Create alert
curl -X POST "http://localhost:8080/alerts" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "spending_threshold",
    "alert_name": "Daily Coffee Budget",
    "threshold_value": 20.0,
    "threshold_period": "daily",
    "notification_method": "in_app"
  }'
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database URIs in .env file
   - Ensure databases are running and accessible
   - Verify network connectivity

2. **Vertex AI Authentication Failed**
   - Ensure GOOGLE_CLOUD_PROJECT is set correctly
   - Check if Vertex AI API is enabled
   - Verify service account permissions

3. **JWT Authentication Failed**
   - Check if JWT public key path is correct
   - Ensure the key file exists and is readable
   - Verify token format and expiration

4. **Import Errors**
   - Ensure you're in the correct directory
   - Check if all dependencies are installed
   - Verify Python path

### Getting Help

1. Check logs: `kubectl logs -l app=aibackend`
2. Check service status: `kubectl get pods -l app=aibackend`
3. Check service endpoints: `kubectl get svc aibackend`
4. Run tests: `python test/test_aibackend.py`

## 🎯 Production Deployment

### 1. Pre-deployment Checklist
- [ ] Database tables initialized
- [ ] Environment variables configured
- [ ] Vertex AI API enabled
- [ ] Service account permissions set
- [ ] JWT keys configured
- [ ] Tests passing

### 2. Deploy to Production
```bash
# Update project ID in manifests
sed -i 's/PROJECT_ID/your-actual-project-id/g' k8s/aibackend.yaml

# Deploy
kubectl apply -f k8s/aibackend.yaml

# Verify deployment
kubectl get pods -l app=aibackend
kubectl get svc aibackend
```

### 3. Monitor Production
```bash
# Check health
kubectl get pods -l app=aibackend

# View logs
kubectl logs -f deployment/aibackend

# Check metrics (if monitoring is set up)
kubectl top pods -l app=aibackend
```
