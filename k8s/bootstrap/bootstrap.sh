#!/bin/bash
# AliceMultiverse Kubernetes Bootstrap Script
# This script sets up all prerequisites for running AliceMultiverse on local Kubernetes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLOUDNATIVEPG_VERSION="1.24.1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}AliceMultiverse Kubernetes Bootstrap${NC}"
echo "===================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi
echo "✅ kubectl found"

# Check helm
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ helm not found. Please install helm first.${NC}"
    exit 1
fi
echo "✅ helm found"

# Check docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ docker not found. Please install Docker Desktop.${NC}"
    exit 1
fi
echo "✅ docker found"

# Check Kubernetes context
CURRENT_CONTEXT=$(kubectl config current-context)
if [[ "$CURRENT_CONTEXT" != "docker-desktop" ]]; then
    echo -e "${YELLOW}⚠️  Current context is '$CURRENT_CONTEXT', expected 'docker-desktop'${NC}"
    echo "Do you want to switch to docker-desktop context? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        kubectl config use-context docker-desktop
    else
        echo -e "${RED}Aborting. Please switch to docker-desktop context manually.${NC}"
        exit 1
    fi
fi
echo "✅ Using docker-desktop context"

# Check if Kubernetes is running
if ! kubectl get nodes &> /dev/null; then
    echo -e "${RED}❌ Kubernetes is not running. Please start Docker Desktop and enable Kubernetes.${NC}"
    exit 1
fi
echo "✅ Kubernetes is running"

echo ""
echo -e "${YELLOW}Installing CloudNativePG operator...${NC}"

# Check if CloudNativePG is already installed
if kubectl get deployment -n cnpg-system cnpg-controller-manager &> /dev/null; then
    echo "✅ CloudNativePG operator already installed"
else
    # Install CloudNativePG
    echo "Installing CloudNativePG v${CLOUDNATIVEPG_VERSION}..."
    kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-${CLOUDNATIVEPG_VERSION}.yaml || true
    
    # Create minimal Pooler CRD to fix the issue
    echo "Creating Pooler CRD..."
    kubectl apply -f "${SCRIPT_DIR}/pooler-crd.yaml"
    
    # Wait for operator to be ready
    echo "Waiting for CloudNativePG operator to be ready..."
    kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=120s || {
        echo -e "${YELLOW}⚠️  CloudNativePG might need more time to start. Continuing...${NC}"
    }
    echo "✅ CloudNativePG operator installed"
fi

echo ""
echo -e "${YELLOW}Creating namespaces...${NC}"

# Create namespaces
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
    if kubectl get namespace "$ns" &> /dev/null; then
        echo "  Namespace $ns already exists"
    else
        kubectl create namespace "$ns"
        kubectl label namespace "$ns" name="$ns"
        echo "  ✅ Created namespace: $ns"
    fi
done
echo "✅ All namespaces ready"

echo ""
echo -e "${YELLOW}Adding Helm repositories...${NC}"

# Add required Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami &> /dev/null || true
helm repo update
echo "✅ Helm repositories updated"

echo ""
echo -e "${GREEN}Bootstrap complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Deploy Redis: ./deploy-redis.sh"
echo "  2. Deploy services: cd ../.. && make k8s-deploy"
echo ""