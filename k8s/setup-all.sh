#!/bin/bash
# Complete AliceMultiverse Kubernetes Setup
# Run this to set up everything from scratch

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}AliceMultiverse Complete Kubernetes Setup${NC}"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Install prerequisites (CloudNativePG)"
echo "  2. Create namespaces"
echo "  3. Deploy Redis (single instance)"
echo "  4. Build and deploy the Asset Processor service"
echo ""
# Check for non-interactive mode
if [[ "${1:-}" != "--non-interactive" ]]; then
    echo "Press Enter to continue or Ctrl+C to abort..."
    read -r
fi

# Step 1: Bootstrap
echo ""
echo -e "${YELLOW}Step 1: Bootstrapping cluster...${NC}"
"${SCRIPT_DIR}/bootstrap/bootstrap.sh"

# Step 2: Deploy Redis
echo ""
echo -e "${YELLOW}Step 2: Deploying Redis...${NC}"
"${SCRIPT_DIR}/bootstrap/deploy-redis.sh"

# Step 3: Build services
echo ""
echo -e "${YELLOW}Step 3: Building services...${NC}"
cd "$ROOT_DIR"

# Build asset processor
echo "Building asset-processor image..."
docker build -t alice-assets:latest services/asset-processor --quiet && echo "✅ Built alice-assets:latest"

# Step 4: Deploy services
echo ""
echo -e "${YELLOW}Step 4: Deploying services...${NC}"

# Deploy asset processor
echo "Deploying asset-processor..."
helm upgrade --install asset-processor charts/alice-service \
    -f services/asset-processor/k8s-values.yaml \
    -n alice-assets \
    --set image.tag=latest \
    --wait --timeout 2m

# Verify deployment
echo ""
echo -e "${YELLOW}Verifying deployment...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=asset-processor -n alice-assets --timeout=60s || {
    echo -e "${YELLOW}⚠️  Service might need more time to start${NC}"
}

# Summary
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Deployed components:"
echo "  - CloudNativePG operator"
echo "  - Redis event bus (single instance)"
echo "  - Asset Processor service with PostgreSQL"
echo ""
echo "Test the deployment:"
echo "  # Port forward to service"
echo "  kubectl port-forward -n alice-assets svc/asset-processor-alice-service 8001:80"
echo "  # In another terminal:"
echo "  curl http://localhost:8001/health"
echo ""
echo "View logs:"
echo "  kubectl logs -n alice-assets -l app.kubernetes.io/name=asset-processor -f"
echo ""
echo "To reset everything:"
echo "  ${SCRIPT_DIR}/bootstrap/reset-cluster.sh"
echo ""