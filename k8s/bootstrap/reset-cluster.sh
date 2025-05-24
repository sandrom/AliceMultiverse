#!/bin/bash
# Reset AliceMultiverse Kubernetes Installation
# WARNING: This will delete all AliceMultiverse resources!

set -euo pipefail

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}WARNING: Cluster Reset${NC}"
echo "====================="
echo ""
echo "This will delete:"
echo "  - All AliceMultiverse namespaces and their contents"
echo "  - CloudNativePG operator"
echo "  - All persistent data"
echo ""
echo -e "${YELLOW}Are you sure you want to continue? Type 'yes' to confirm:${NC}"
read -r response

if [[ "$response" != "yes" ]]; then
    echo "Aborting reset."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting cluster reset...${NC}"

# Delete all Helm releases
echo "Uninstalling Helm releases..."
NAMESPACES=(
    "alice-interface"
    "alice-assets" 
    "alice-quality"
    "alice-metadata"
    "alice-search"
    "alice-workflow"
    "alice-events"
    "alice-monitoring"
)

for ns in "${NAMESPACES[@]}"; do
    echo -n "  Checking $ns... "
    RELEASES=$(helm list -n "$ns" -q 2>/dev/null || true)
    if [[ -n "$RELEASES" ]]; then
        for release in $RELEASES; do
            helm uninstall "$release" -n "$ns" 2>/dev/null || true
            echo -n "✓ "
        done
    fi
    echo ""
done

# Delete namespaces
echo ""
echo "Deleting namespaces..."
for ns in "${NAMESPACES[@]}"; do
    if kubectl get namespace "$ns" &> /dev/null; then
        echo "  Deleting $ns..."
        kubectl delete namespace "$ns" --wait=false
    fi
done

# Delete CloudNativePG
echo ""
echo "Removing CloudNativePG operator..."
if kubectl get namespace cnpg-system &> /dev/null; then
    # Delete the operator
    kubectl delete -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.1.yaml 2>/dev/null || true
    # Delete custom CRDs
    kubectl delete crd clusters.postgresql.cnpg.io 2>/dev/null || true
    kubectl delete crd poolers.postgresql.cnpg.io 2>/dev/null || true
    kubectl delete crd backups.postgresql.cnpg.io 2>/dev/null || true
    kubectl delete crd scheduledbackups.postgresql.cnpg.io 2>/dev/null || true
    # Force delete namespace if stuck
    kubectl delete namespace cnpg-system --wait=false 2>/dev/null || true
fi

# Clean up any remaining resources
echo ""
echo "Cleaning up remaining resources..."

# Remove any stuck PVCs
echo "  Checking for persistent volume claims..."
for ns in "${NAMESPACES[@]}"; do
    kubectl delete pvc --all -n "$ns" 2>/dev/null || true
done

# Wait for namespace deletion
echo ""
echo "Waiting for namespace deletion (this may take a minute)..."
for ns in "${NAMESPACES[@]}"; do
    while kubectl get namespace "$ns" &> /dev/null; do
        echo -n "."
        sleep 2
    done
done
echo ""

echo ""
echo -e "${GREEN}✅ Cluster reset complete!${NC}"
echo ""
echo "To set up again:"
echo "  1. Run: ./bootstrap.sh"
echo "  2. Run: ./deploy-redis.sh"
echo "  3. Deploy services as needed"
echo ""