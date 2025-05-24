# Kubernetes operations for AliceMultiverse
# Usage: make -f k8s.mk <target>

.PHONY: help
help: ## Show this help message
	@echo "AliceMultiverse Kubernetes Operations"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Variables
KUBE_CONTEXT := docker-desktop
CLOUDNATIVEPG_VERSION := 1.26.0
MONITORING_NAMESPACE := alice-monitoring

# Cluster Setup
.PHONY: setup-cluster
setup-cluster: ## Complete cluster setup (use k8s/setup-all.sh instead)
	@echo "Running complete setup..."
	@./k8s/setup-all.sh

.PHONY: check-context
check-context: ## Verify Kubernetes context
	@echo "Checking Kubernetes context..."
	@current_context=$$(kubectl config current-context); \
	if [ "$$current_context" != "$(KUBE_CONTEXT)" ]; then \
		echo "❌ Wrong context: $$current_context. Expected: $(KUBE_CONTEXT)"; \
		echo "Run: kubectl config use-context $(KUBE_CONTEXT)"; \
		exit 1; \
	else \
		echo "✅ Using context: $(KUBE_CONTEXT)"; \
	fi

.PHONY: install-operators
install-operators: ## Install required operators
	@echo "Installing CloudNativePG operator..."
	kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-$(CLOUDNATIVEPG_VERSION)/releases/cnpg-$(CLOUDNATIVEPG_VERSION).yaml
	@echo "Waiting for operator to be ready..."
	kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=120s
	@echo "✅ CloudNativePG operator installed"

.PHONY: create-namespaces
create-namespaces: ## Create all service namespaces
	@echo "Creating namespaces..."
	@for ns in alice-interface alice-assets alice-quality alice-metadata alice-search alice-workflow alice-events alice-monitoring; do \
		kubectl create namespace $$ns --dry-run=client -o yaml | kubectl apply -f -; \
		kubectl label namespace $$ns name=$$ns --overwrite; \
	done
	@echo "✅ Namespaces created"

.PHONY: install-redis
install-redis: ## Install Redis for event bus
	@echo "Installing Redis event bus..."
	helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
	helm repo update
	helm upgrade --install alice-events bitnami/redis \
		--namespace alice-events \
		--set auth.enabled=false \
		--set master.persistence.size=1Gi \
		--wait
	@echo "✅ Redis event bus installed"

# Service Deployment
.PHONY: build-images
build-images: ## Build all service Docker images
	@echo "Building Docker images..."
	@for service in asset-processor quality-analyzer metadata-extractor alice-interface; do \
		echo "Building $$service..."; \
		docker build -t alice-$$service:local -f services/$$service/Dockerfile services/$$service || exit 1; \
	done
	@echo "✅ All images built"

.PHONY: deploy-asset-processor
deploy-asset-processor: ## Deploy asset processor service
	@echo "Deploying asset processor..."
	docker build -t alice-assets:local services/asset-processor
	helm upgrade --install asset-processor charts/alice-service \
		-f services/asset-processor/k8s-values.yaml \
		-n alice-assets \
		--wait
	@echo "✅ Asset processor deployed"

.PHONY: deploy-all-services
deploy-all-services: build-images ## Deploy all services
	@make -f k8s.mk deploy-asset-processor
	# Add other services as they're ready
	@echo "✅ All services deployed"

# Development Tools
.PHONY: port-forward-asset
port-forward-asset: ## Port forward to asset processor
	kubectl port-forward -n alice-assets svc/asset-processor 8001:80

.PHONY: port-forward-redis
port-forward-redis: ## Port forward to Redis
	kubectl port-forward -n alice-events svc/alice-events-redis-master 6379:6379

.PHONY: logs-asset
logs-asset: ## Show asset processor logs
	kubectl logs -n alice-assets -l app.kubernetes.io/name=asset-processor -f

.PHONY: logs-asset-db
logs-asset-db: ## Show asset database logs
	kubectl logs -n alice-assets -l cnpg.io/cluster=asset-processor-alice-service-db -f

# Database Operations
.PHONY: db-asset-shell
db-asset-shell: ## Open psql shell to asset database
	@echo "Connecting to asset database..."
	@password=$$(kubectl get secret -n alice-assets asset-processor-alice-service-db-credentials -o jsonpath='{.data.password}' | base64 -d); \
	kubectl exec -it -n alice-assets asset-processor-alice-service-db-1 -- env PGPASSWORD=$$password psql -U alice -d assets

.PHONY: db-asset-port-forward
db-asset-port-forward: ## Port forward to asset database
	kubectl port-forward -n alice-assets svc/asset-processor-alice-service-db-rw 5432:5432

# Monitoring
.PHONY: install-monitoring
install-monitoring: ## Install Prometheus and Grafana
	@echo "Installing monitoring stack..."
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
	helm repo update
	helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
		-n $(MONITORING_NAMESPACE) \
		--set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=standard \
		--set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=5Gi \
		--set grafana.persistence.enabled=true \
		--set grafana.persistence.size=1Gi
	@echo "✅ Monitoring stack installed"

.PHONY: port-forward-grafana
port-forward-grafana: ## Access Grafana dashboard
	@echo "Grafana admin password:"
	@kubectl get secret -n $(MONITORING_NAMESPACE) monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d
	@echo ""
	@echo "Access Grafana at: http://localhost:3000"
	kubectl port-forward -n $(MONITORING_NAMESPACE) svc/monitoring-grafana 3000:80

# Cleanup
.PHONY: delete-asset-processor
delete-asset-processor: ## Delete asset processor deployment
	helm uninstall asset-processor -n alice-assets

.PHONY: clean-namespace
clean-namespace: ## Clean a specific namespace (NS=namespace)
	@if [ -z "$(NS)" ]; then \
		echo "❌ Please specify namespace: make -f k8s.mk clean-namespace NS=alice-assets"; \
		exit 1; \
	fi
	kubectl delete all --all -n $(NS)

.PHONY: clean-all
clean-all: ## Remove all AliceMultiverse resources (WARNING: Destructive)
	@echo "⚠️  WARNING: This will delete all AliceMultiverse resources!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@for ns in alice-interface alice-assets alice-quality alice-metadata alice-search alice-workflow alice-events; do \
		echo "Cleaning namespace: $$ns"; \
		kubectl delete namespace $$ns --ignore-not-found; \
	done
	@echo "✅ Cleanup complete"

# Troubleshooting
.PHONY: debug-pods
debug-pods: ## Show all pods status
	@echo "AliceMultiverse Pods Status:"
	@for ns in alice-interface alice-assets alice-quality alice-metadata alice-search alice-workflow alice-events; do \
		echo "\n=== Namespace: $$ns ==="; \
		kubectl get pods -n $$ns 2>/dev/null || echo "Namespace not found"; \
	done

.PHONY: debug-events
debug-events: ## Show recent events (NS=namespace)
	@if [ -z "$(NS)" ]; then \
		kubectl get events --all-namespaces --sort-by='.lastTimestamp' | grep alice-; \
	else \
		kubectl get events -n $(NS) --sort-by='.lastTimestamp'; \
	fi

.PHONY: debug-asset
debug-asset: ## Debug asset processor issues
	@echo "=== Asset Processor Pod ==="
	kubectl describe pod -n alice-assets -l app.kubernetes.io/name=asset-processor
	@echo "\n=== Recent Events ==="
	kubectl get events -n alice-assets --sort-by='.lastTimestamp' | head -20

# Quick Start
.PHONY: quickstart
quickstart: ## Complete setup and deploy asset processor
	@echo "🚀 Starting AliceMultiverse on Kubernetes..."
	@make -f k8s.mk setup-cluster
	@make -f k8s.mk deploy-asset-processor
	@echo ""
	@echo "✅ Quickstart complete!"
	@echo ""
	@echo "Test the service:"
	@echo "  make -f k8s.mk port-forward-asset"
	@echo "  curl http://localhost:8001/health"
	@echo ""
	@echo "View logs:"
	@echo "  make -f k8s.mk logs-asset"