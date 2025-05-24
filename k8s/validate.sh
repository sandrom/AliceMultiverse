#!/bin/bash
# Validate AliceMultiverse Kubernetes deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}AliceMultiverse Deployment Validation${NC}"
echo "===================================="
echo ""

# Check CloudNativePG
echo "Checking CloudNativePG operator..."
if kubectl get deployment -n cnpg-system cnpg-controller-manager &>/dev/null; then
    READY=$(kubectl get deployment -n cnpg-system cnpg-controller-manager -o jsonpath='{.status.readyReplicas}')
    if [[ "$READY" == "1" ]]; then
        echo "✅ CloudNativePG operator is running"
    else
        echo -e "${RED}❌ CloudNativePG operator is not ready${NC}"
    fi
else
    echo -e "${RED}❌ CloudNativePG operator not found${NC}"
fi

# Check Redis
echo ""
echo "Checking Redis..."
if kubectl get pod -n alice-events alice-events-redis-master-0 &>/dev/null; then
    STATUS=$(kubectl get pod -n alice-events alice-events-redis-master-0 -o jsonpath='{.status.phase}')
    if [[ "$STATUS" == "Running" ]]; then
        echo "✅ Redis is running"
        # Test Redis connectivity
        kubectl run redis-test --rm -it --image=redis:alpine --restart=Never \
            -- redis-cli -h alice-events-redis-master.alice-events.svc.cluster.local ping 2>/dev/null | grep -q PONG && \
            echo "✅ Redis is responding to PING" || echo -e "${YELLOW}⚠️  Could not test Redis connectivity${NC}"
    else
        echo -e "${RED}❌ Redis is not running (status: $STATUS)${NC}"
    fi
else
    echo -e "${RED}❌ Redis not found${NC}"
fi

# Check Asset Processor
echo ""
echo "Checking Asset Processor service..."
POD=$(kubectl get pods -n alice-assets -l app.kubernetes.io/name=alice-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [[ -n "$POD" ]]; then
    STATUS=$(kubectl get pod -n alice-assets "$POD" -o jsonpath='{.status.phase}')
    READY=$(kubectl get pod -n alice-assets "$POD" -o jsonpath='{.status.containerStatuses[0].ready}')
    if [[ "$STATUS" == "Running" && "$READY" == "true" ]]; then
        echo "✅ Asset Processor pod is running"
        
        # Test service endpoint
        echo "Testing service endpoint..."
        kubectl port-forward -n alice-assets svc/asset-processor-alice-service 8001:80 &>/dev/null &
        PF_PID=$!
        sleep 3
        
        if curl -s http://localhost:8001/health | grep -q "healthy"; then
            echo "✅ Asset Processor API is healthy"
        else
            echo -e "${RED}❌ Asset Processor API is not responding${NC}"
        fi
        
        kill $PF_PID 2>/dev/null || true
    else
        echo -e "${RED}❌ Asset Processor is not ready (status: $STATUS, ready: $READY)${NC}"
    fi
else
    echo -e "${RED}❌ Asset Processor not found${NC}"
fi

# Check Database
echo ""
echo "Checking Asset Processor database..."
DB_POD=$(kubectl get pods -n alice-assets -l cnpg.io/cluster=asset-processor-alice-service-db -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [[ -n "$DB_POD" ]]; then
    STATUS=$(kubectl get pod -n alice-assets "$DB_POD" -o jsonpath='{.status.phase}')
    if [[ "$STATUS" == "Running" ]]; then
        echo "✅ PostgreSQL database is running"
        # Check database exists
        kubectl exec -n alice-assets "$DB_POD" -- psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='assets';" 2>/dev/null | grep -q assets && \
            echo "✅ 'assets' database exists" || echo -e "${RED}❌ 'assets' database not found${NC}"
    else
        echo -e "${RED}❌ PostgreSQL is not running (status: $STATUS)${NC}"
    fi
else
    echo -e "${RED}❌ PostgreSQL database not found${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}Summary${NC}"
echo "======="
kubectl get pods --all-namespaces | grep -E "(alice-|cnpg-)" | awk '{printf "%-20s %-50s %-10s\n", $1, $2, $4}'