#!/bin/bash
# Deploy Redis for AliceMultiverse (Single Instance)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}Deploying Redis Event Bus (Single Instance)${NC}"
echo "==========================================="
echo ""

# Check if Redis is already installed
if helm list -n alice-events | grep -q alice-events; then
    echo -e "${YELLOW}Redis is already installed. Upgrading...${NC}"
    helm upgrade alice-events bitnami/redis \
        -f "${SCRIPT_DIR}/redis-single.yaml" \
        -n alice-events \
        --wait
else
    echo "Installing Redis..."
    helm install alice-events bitnami/redis \
        -f "${SCRIPT_DIR}/redis-single.yaml" \
        -n alice-events \
        --wait
fi

echo ""
echo "✅ Redis deployed successfully!"
echo ""
echo "Connection details:"
echo "  Host: alice-events-redis-master.alice-events.svc.cluster.local"
echo "  Port: 6379"
echo "  URL:  redis://alice-events-redis-master.alice-events.svc.cluster.local:6379"
echo ""
echo "To test Redis:"
echo "  kubectl run redis-test --rm -it --image=redis:alpine --restart=Never -- redis-cli -h alice-events-redis-master.alice-events.svc.cluster.local ping"
echo ""