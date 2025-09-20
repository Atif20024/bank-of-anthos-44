#!/bin/bash
# AI Backend deployment script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
CLUSTER_NAME=${GKE_CLUSTER:-"bank-of-anthos"}
ZONE=${GKE_ZONE:-"us-central1-a"}
SERVICE_NAME="aibackend"

echo -e "${GREEN}🚀 Starting AI Backend deployment...${NC}"

# Check if required tools are installed
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ docker not found. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites found${NC}"
}

# Set up authentication
setup_auth() {
    echo -e "${YELLOW}🔐 Setting up authentication...${NC}"
    
    # Get current project
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        echo -e "${YELLOW}Switching to project $PROJECT_ID...${NC}"
        gcloud config set project $PROJECT_ID
    fi
    
    # Get cluster credentials
    echo -e "${YELLOW}Getting GKE cluster credentials...${NC}"
    gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID
    
    echo -e "${GREEN}✓ Authentication set up${NC}"
}

# Build and push Docker image
build_and_push() {
    echo -e "${YELLOW}🐳 Building and pushing Docker image...${NC}"
    
    # Build the image
    docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
    
    # Push to Container Registry
    docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
    
    echo -e "${GREEN}✓ Docker image built and pushed${NC}"
}

# Deploy to Kubernetes
deploy_to_k8s() {
    echo -e "${YELLOW}☸️  Deploying to Kubernetes...${NC}"
    
    # Update the Kubernetes manifest with the correct project ID
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" k8s/aibackend.yaml
    
    # Apply the Kubernetes manifest
    kubectl apply -f k8s/aibackend.yaml
    
    # Wait for deployment to be ready
    echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/$SERVICE_NAME
    
    echo -e "${GREEN}✓ Deployment successful${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
    
    # Check if pods are running
    PODS=$(kubectl get pods -l app=$SERVICE_NAME --no-headers | wc -l)
    RUNNING_PODS=$(kubectl get pods -l app=$SERVICE_NAME --no-headers | grep Running | wc -l)
    
    if [ "$PODS" -eq "$RUNNING_PODS" ] && [ "$PODS" -gt 0 ]; then
        echo -e "${GREEN}✓ All pods are running ($RUNNING_PODS/$PODS)${NC}"
    else
        echo -e "${RED}❌ Some pods are not running ($RUNNING_PODS/$PODS)${NC}"
        kubectl get pods -l app=$SERVICE_NAME
        exit 1
    fi
    
    # Check service
    SERVICE_IP=$(kubectl get service $SERVICE_NAME -o jsonpath='{.spec.clusterIP}')
    if [ -n "$SERVICE_IP" ]; then
        echo -e "${GREEN}✓ Service is available at $SERVICE_IP:8080${NC}"
    else
        echo -e "${RED}❌ Service not found${NC}"
        exit 1
    fi
}

# Show deployment information
show_info() {
    echo -e "${GREEN}🎉 AI Backend deployment completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Deployment Information:${NC}"
    echo "  Project ID: $PROJECT_ID"
    echo "  Cluster: $CLUSTER_NAME"
    echo "  Zone: $ZONE"
    echo "  Service: $SERVICE_NAME"
    echo ""
    echo -e "${YELLOW}🔗 Useful Commands:${NC}"
    echo "  View pods: kubectl get pods -l app=$SERVICE_NAME"
    echo "  View logs: kubectl logs -l app=$SERVICE_NAME"
    echo "  Port forward: kubectl port-forward service/$SERVICE_NAME 8080:8080"
    echo "  Delete deployment: kubectl delete -f k8s/aibackend.yaml"
    echo ""
    echo -e "${YELLOW}🧪 Test the service:${NC}"
    echo "  kubectl port-forward service/$SERVICE_NAME 8080:8080"
    echo "  curl http://localhost:8080/healthy"
    echo "  curl http://localhost:8080/ready"
}

# Main deployment flow
main() {
    check_prerequisites
    setup_auth
    build_and_push
    deploy_to_k8s
    verify_deployment
    show_info
}

# Run main function
main "$@"
