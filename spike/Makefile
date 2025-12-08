.PHONY: all help create delete list setup-ai-agent
.ONESHELL:

# Define the YAML config file
KIND_CONFIG_FILE := kind-cluster.yaml

# Check if yq is installed
YQ_CHECK := $(shell which yq)
ifeq ($(YQ_CHECK),)
$(error "Error: yq is not installed. Please install yq to use this Makefile (e.g., brew install yq, sudo snap install yq).")
endif

all: help

help: ## Display help for this Makefile
	@echo "Kind Cluster Management Makefile (using $(KIND_CONFIG_FILE))"
	@echo "---------------------------------------------------------"
	@echo "This Makefile reads cluster configuration from $(KIND_CONFIG_FILE)."
	@echo "Ensure $(KIND_CONFIG_FILE) exists and contains at least the 'name' property."
	@echo "Any local images you want preloaded into the Kind cluster can be specified using the 'preloadImages' property."
	@echo ""
	@echo "Example $(KIND_CONFIG_FILE) content:"
	@echo "  name: my-kind-cluster"
	@echo "  preloadImages:"
	@echo "    - nginx:latest"
	@echo "    - busybox:latest"
	@echo ""	
	@echo "Usage:"
	@echo ""
	@grep -Eh '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Function to check for config file and exit if not found
define check_config_file
	@if [ ! -f "$(KIND_CONFIG_FILE)" ]; then \
		echo "Error: $(KIND_CONFIG_FILE) not found."; \
		echo "Please create this file with 'name' and 'preloadImages' properties. Refer to 'make help' for an example."; \
		exit 1; \
	fi
endef

create: ## Create the Kind cluster defined in $(KIND_CONFIG_FILE) and preload images
	$(call check_config_file)
	$(eval CLUSTER_NAME := $(shell yq '.name' $(KIND_CONFIG_FILE)))
	$(eval PRELOAD_IMAGES := $(shell yq '.preloadImages[]' $(KIND_CONFIG_FILE) | tr '\n' ' '))

	kind create cluster --name $(CLUSTER_NAME)

	@for img in $(PRELOAD_IMAGES); do \
		echo "Loading image: $$img"; \
		kind load docker-image $$img --name $(CLUSTER_NAME); \
	done
	@echo "--- Kind cluster $(CLUSTER_NAME) created ---"

delete: ## Delete the Kind cluster defined in $(KIND_CONFIG_FILE)
	$(call check_config_file)
	$(eval CLUSTER_NAME := $(shell yq '.name' $(KIND_CONFIG_FILE)))

	kind delete cluster --name $(CLUSTER_NAME)

list: ## List all existing Kind clusters
	kind get clusters

setup-ai-agent: ## Setup the AI agent service account (ai-agent) in the Kubernetes cluster
	@echo "--- Applying Kubernetes manifests..."
	kubectl apply -f ./01-vulnerable-setup.yaml
	kubectl apply -f ./02-prod-env.yaml

	@echo "--- Creating AI agent token..."
	export AGENT_TOKEN=$$(kubectl create token ai-agent -n ai-workspace --duration=24h)

	@echo "--- Gathering cluster information..."
	export CLUSTER_NAME=$$(kubectl config view --minify -o jsonpath='{.clusters[0].name}')
	export CLUSTER_SERVER=$$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
	export CLUSTER_CA=$$(kubectl config view --minify --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

	@echo "--- Creating ai-agent-kubeconfig.yaml..."
	@envsubst < ./ai-agent-kubeconfig.yaml.tpl > ./ai-agent-kubeconfig.yaml
	@echo "--- Done. 'ai-agent-kubeconfig.yaml' is ready."