# Kafka KRaft Mode Configuration and Architecture

## Overview

This project implements Apache Kafka 4.1.1 configured in KRaft (Kafka Raft Metadata) mode. KRaft eliminates the requirement for an external Apache ZooKeeper quorum by embedding consensus and metadata management directly within the Kafka cluster brokers.

---

## Technical Specifications

| Component | Version | Release | Details |
|---|---|---|---|
| Apache Kafka | 4.1.1 | November 2025 | Native KRaft consensus (ZooKeeper-free) |
| Apache Spark | 4.0.1 | September 2025 | Scala 2.13, Java 17 runtime |
| Redis | 7-alpine | Stable | In-memory time-series and alert cache |
| Python | 3.12-slim | Stable | Base image for FastAPI gateway and Streamlit UI |

---

## Architectural Comparison: ZooKeeper vs. KRaft

| Dimension | ZooKeeper Mode | KRaft Mode |
|---|---|---|
| Topology | Separate ZooKeeper cluster + Kafka brokers | Consolidated Kafka broker/controller nodes |
| Resource Footprint | High memory and network overhead | Lightweight single-process footprint |
| Metadata Management | External tree-structured z-nodes | Internal partitioned metadata topic (`__cluster_metadata`) |
| Controller Failover | Multi-second re-election latency | Sub-second deterministic raft leader election |
| Operational Complexity | Two distributed systems to monitor and patch | Single unified system with shared security controls |

---

## Broker Configuration Reference

The broker is configured to operate in combined controller-broker mode (`broker,controller`):

```yaml
# Unique node identifier
KAFKA_NODE_ID: 1

# Process roles
KAFKA_PROCESS_ROLES: broker,controller

# Controller quorum voters list
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093

# Controller listener name
KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER

# Fixed cluster identifier for storage formatting
CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk

# Network listeners definition
KAFKA_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://0.0.0.0:9092,CONTROLLER://kafka:9093

# Advertised listeners for inter-container and host routing
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

### Listener Mapping

| Listener | Port | Scope |
|---|---|---|
| `PLAINTEXT` | 29092 | Inter-container communication within Docker bridge network |
| `PLAINTEXT_HOST` | 9092 | External client connections from host machine |
| `CONTROLLER` | 9093 | Raft metadata quorum replication between voters |

---

## Operational CLI Commands

All operational commands run directly against the broker container:

### Topic Management

```bash
# Create the raw trips topic with 3 partitions
docker exec kafka kafka-topics --create \
  --topic nyc.taxi.trips.raw \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# List existing topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topic configuration and partition leadership
docker exec kafka kafka-topics --describe \
  --topic nyc.taxi.trips.raw \
  --bootstrap-server localhost:9092
```

### Consumer Group Inspection

```bash
# List all active consumer groups
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Evaluate consumer lag across partitions
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-streaming-nyc-taxi
```

### Health Check and Cluster Metadata

```bash
# Inspect API versions and broker readiness
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# View active KRaft metadata snapshot
docker exec kafka kafka-metadata \
  --snapshot /var/lib/kafka/data/__cluster_metadata-0/00000000000000000000.log \
  --command describe
```

---

## Troubleshooting Guide

### 1. Cluster ID Mismatch on Startup
- **Root Cause:** A persistent volume exists from a previous initialization formatted with a distinct `CLUSTER_ID`.
- **Resolution:** Reset the data volume to allow automatic re-formatting:
  ```bash
  docker compose down -v
  docker compose up -d
  ```

### 2. External Connection Refused on Port 9092
- **Root Cause:** Inbound client does not resolve the advertised host listener.
- **Resolution:** Ensure `KAFKA_ADVERTISED_LISTENERS` maps `PLAINTEXT_HOST://localhost:9092` and port `9092:9092` is published in `docker-compose.yml`.

### 3. Kafka UI Reports Broker Unavailable
- **Root Cause:** Web UI container reached health timeout before Kafka KRaft initialization finished.
- **Resolution:** Restart the Kafka UI container once the broker health check passes:
  ```bash
  docker compose restart kafka-ui
  ```
