# Kafka Skill - Professional Deployment
#
# Usage:
#   make install    # Full installation
#   make test       # Run tests
#   make clean      # Remove everything

NAMESPACE := kafka
CLUSTER := dev-cluster
HELM_RELEASE := strimzi-operator

.PHONY: all install clean test status help

help:
	@echo "Kafka Deployment Commands:"
	@echo "  make install     - Install Strimzi + Kafka cluster"
	@echo "  make uninstall   - Remove everything"
	@echo "  make test        - Verify deployment"
	@echo "  make status      - Show current status"
	@echo "  make topic       - Create test topic"
	@echo "  make produce     - Produce test messages"
	@echo "  make consume     - Consume test messages"

# === Installation ===

install: namespace strimzi kafka wait-ready
	@echo "✓ Kafka cluster ready"

namespace:
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -

strimzi:
	@helm repo add strimzi https://strimzi.io/charts 2>/dev/null || true
	@helm repo update strimzi
	@helm upgrade --install $(HELM_RELEASE) strimzi/strimzi-kafka-operator \
		-n $(NAMESPACE) --wait --timeout 5m

kafka:
	@kubectl apply -f manifests/kafka-cluster.yaml -n $(NAMESPACE)

wait-ready:
	@echo "Waiting for Kafka cluster..."
	@kubectl wait kafka/$(CLUSTER) --for=condition=Ready --timeout=300s -n $(NAMESPACE)

# === Uninstall ===

uninstall: clean-kafka clean-strimzi clean-namespace
	@echo "✓ Cleanup complete"

clean-kafka:
	@kubectl delete kafka $(CLUSTER) -n $(NAMESPACE) --ignore-not-found
	@kubectl delete kafkanodepool -l strimzi.io/cluster=$(CLUSTER) -n $(NAMESPACE) --ignore-not-found

clean-strimzi:
	@helm uninstall $(HELM_RELEASE) -n $(NAMESPACE) --ignore-not-found || true

clean-namespace:
	@kubectl delete namespace $(NAMESPACE) --ignore-not-found

clean: uninstall

# === Testing ===

test: test-cluster test-topic test-produce test-consume
	@echo "✓ All tests passed"

test-cluster:
	@echo "Testing cluster status..."
	@kubectl get kafka $(CLUSTER) -n $(NAMESPACE) -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q True
	@echo "  ✓ Cluster ready"

test-topic: topic
	@kubectl get kafkatopic test-topic -n $(NAMESPACE) -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q True
	@echo "  ✓ Topic ready"

test-produce:
	@echo "Testing produce..."
	@echo "test-message-$$(date +%s)" | kubectl exec -i -n $(NAMESPACE) $(CLUSTER)-dual-role-0 -- \
		bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test-topic
	@echo "  ✓ Produce works"

test-consume:
	@echo "Testing consume..."
	@kubectl exec -n $(NAMESPACE) $(CLUSTER)-dual-role-0 -- \
		bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
		--topic test-topic --from-beginning --max-messages 1 --timeout-ms 10000 >/dev/null
	@echo "  ✓ Consume works"

# === Operations ===

status:
	@echo "=== Kafka Status ==="
	@kubectl get kafka,kafkanodepool,kafkatopic,pods -n $(NAMESPACE)

topic:
	@kubectl apply -f manifests/kafka-topic.yaml -n $(NAMESPACE)

produce:
	@echo "Enter messages (Ctrl+D to finish):"
	@kubectl exec -i -n $(NAMESPACE) $(CLUSTER)-dual-role-0 -- \
		bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test-topic

consume:
	@kubectl exec -n $(NAMESPACE) $(CLUSTER)-dual-role-0 -- \
		bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
		--topic test-topic --from-beginning

logs:
	@kubectl logs -n $(NAMESPACE) -l strimzi.io/cluster=$(CLUSTER) --tail=50
