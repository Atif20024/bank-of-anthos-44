#!/bin/bash
# AI Backend setup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up AI Backend for Bank of Anthos${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Please run this script from the aiBackend directory${NC}"
    exit 1
fi

# 1. Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# 2. Set up environment variables
echo -e "${YELLOW}🔧 Setting up environment variables...${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
# AI Backend Configuration
VERSION=v1.0.0
PORT=8080
LOG_LEVEL=INFO

# Database Configuration (Update these with your actual values)
ACCOUNTS_DB_URI=postgresql://user:password@localhost:5432/accounts
LEDGER_DB_URI=postgresql://user:password@localhost:5432/ledger

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro

# JWT Configuration
PUB_KEY_PATH=/etc/secrets/jwtRS256.key.pub
LOCAL_ROUTING_NUM=883745000

# AI Backend Configuration
MAX_RETRIES=1
INSIGHT_EXPIRY_DAYS=7
MAX_INSIGHTS_PER_USER=50
EOF
    echo -e "${GREEN}✓ Created .env file. Please update the database URIs and project ID.${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# 3. Make scripts executable
echo -e "${YELLOW}🔧 Making scripts executable...${NC}"
chmod +x deploy.sh
chmod +x test/test_aibackend.py

echo -e "${GREEN}✅ Setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Update the .env file with your actual database URIs and project ID"
echo "2. Run: python init_db.py (to initialize database tables)"
echo "3. Run: python test/test_aibackend.py (to test the service)"
echo "4. Run: python main.py (to start the service locally)"
echo "5. Run: ./deploy.sh (to deploy to GKE)"
