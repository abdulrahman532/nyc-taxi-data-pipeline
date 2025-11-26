# Kafka KRaft Mode Documentation

## 📋 Overview

This project uses **Apache Kafka 4.1.1 in KRaft mode** (Kafka Raft) - the new consensus protocol that replaces Zookeeper. This provides a simpler, more efficient architecture.

## 🚀 Latest Versions (November 2025)

| Technology | Version | Release Date | Notes |
|------------|---------|--------------|-------|
| **Apache Kafka** | 4.1.1 | Nov 12, 2025 | KRaft only (No Zookeeper!) |
| **Apache Spark** | 4.0.1 | Sep 06, 2025 | Scala 2.13, Java 17 |
| **Redis** | 7.x | - | Alpine image |
| **Python** | 3.12 | - | For FastAPI & Streamlit |

## 🆚 Zookeeper vs KRaft

| Feature | Zookeeper Mode | KRaft Mode |
|---------|----------------|------------|
| Architecture | Kafka + Zookeeper | Kafka only |
| Services | 2 containers | 1 container |
| Memory Usage | Higher | Lower |
| Complexity | More complex | Simpler |
| Maintenance | 2 systems | 1 system |
| Startup Time | Slower | Faster |
| Kafka Version | 3.x and below | 3.3+ (required in 4.x) |

## 🏗️ Full Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     NYC Taxi Streaming Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │  ngrok   │───▶│ FastAPI  │───▶│  Kafka   │───▶│  Spark   │           │
│  │ (Public) │    │  :8000   │    │  :9092   │    │ Streaming│           │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘           │
│                                                        │                 │
│                                                        ▼                 │
│                                  ┌──────────┐    ┌──────────┐           │
│                                  │  Redis   │◀───│  Metrics │           │
│                                  │  :6379   │    │  + Fraud │           │
│                                  └────┬─────┘    └──────────┘           │
│                                       │                                  │
│                                       ▼                                  │
│                                  ┌──────────┐                            │
│                                  │Streamlit │                            │
│                                  │  :8501   │                            │
│                                  └──────────┘                            │
│                                                                          │
│  UIs: Kafka UI :8080 | Spark Master :8081 | Spark Worker :8082          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Explained

### Key Environment Variables

```yaml
# Node identification
KAFKA_NODE_ID: 1                    # Unique ID for this node

# KRaft roles - this node acts as both broker and controller
KAFKA_PROCESS_ROLES: broker,controller

# Controller quorum - list of controller voters
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093

# Controller listener name
KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER

# Cluster ID - MUST be consistent across restarts
CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
```

### Listeners Configuration

```yaml
KAFKA_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://0.0.0.0:9092,CONTROLLER://kafka:9093
```

| Listener | Port | Purpose |
|----------|------|---------|
| PLAINTEXT | 29092 | Internal Docker communication |
| PLAINTEXT_HOST | 9092 | External access from host |
| CONTROLLER | 9093 | Controller communication (KRaft) |

## 🚀 Quick Start

### Start the Services

```bash
cd streaming/docker
docker-compose up -d
```

### Verify Kafka is Running

```bash
# Check container status
docker-compose ps

# Check Kafka logs
docker-compose logs kafka

# Verify broker is ready
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Access Kafka UI

Open http://localhost:8080 in your browser.

## 📝 Common Operations

### Create a Topic

```bash
docker exec kafka kafka-topics --create \
  --topic nyc-taxi-trips \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### List Topics

```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Produce Messages

```bash
docker exec -it kafka kafka-console-producer \
  --topic nyc-taxi-trips \
  --bootstrap-server localhost:9092
```

### Consume Messages

```bash
docker exec -it kafka kafka-console-consumer \
  --topic nyc-taxi-trips \
  --bootstrap-server localhost:9092 \
  --from-beginning
```

### Describe Topic

```bash
docker exec kafka kafka-topics --describe \
  --topic nyc-taxi-trips \
  --bootstrap-server localhost:9092
```

## ⚠️ Common Issues & Solutions

### 1. Kafka Container Keeps Restarting

**Symptoms:**
- Container exits immediately after starting
- Logs show "Node ID does not match"

**Solution:**
```bash
# Remove old data
docker-compose down -v
docker volume rm docker_kafka_data

# Start fresh
docker-compose up -d
```

### 2. "CLUSTER_ID doesn't match stored value"

**Cause:** You changed the CLUSTER_ID after Kafka stored data.

**Solution:**
```bash
# Option 1: Reset everything
docker-compose down -v
docker-compose up -d

# Option 2: Use the original CLUSTER_ID from logs
docker logs kafka | grep "CLUSTER_ID"
```

### 3. Cannot Connect from Host Machine

**Symptoms:**
- Connection refused on localhost:9092

**Check:**
```bash
# Verify port mapping
docker port kafka

# Check if Kafka is listening
docker exec kafka netstat -tlnp | grep 9092
```

**Solution:** Ensure `KAFKA_ADVERTISED_LISTENERS` includes `PLAINTEXT_HOST://localhost:9092`

### 4. Kafka UI Shows "Cluster is not available"

**Cause:** Kafka-UI started before Kafka was ready.

**Solution:**
```bash
# Restart kafka-ui after Kafka is healthy
docker-compose restart kafka-ui
```

### 5. Topics Not Being Created Automatically

**Check:**
```yaml
KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"  # Must be string "true"
```

### 6. Consumer Lag Issues

**Symptoms:**
- Messages not being consumed
- High consumer lag

**Debug:**
```bash
# Check consumer groups
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Describe specific group
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group your-consumer-group
```

## 🔄 Migration from Zookeeper Mode

If you previously used Zookeeper mode, follow these steps:

### 1. Backup Important Data (if any)

```bash
# Export topic configurations
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 > topics_backup.txt
```

### 2. Stop Old Containers

```bash
docker-compose down -v
```

### 3. Update docker-compose.yml

Replace Zookeeper configuration with KRaft configuration (already done in this project).

### 4. Start New Setup

```bash
docker-compose up -d
```

### 5. Recreate Topics

```bash
# Recreate your topics
docker exec kafka kafka-topics --create \
  --topic nyc-taxi-trips \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

## 🛠️ Troubleshooting Commands

### Check Kafka Logs
```bash
docker-compose logs -f kafka
```

### Check Controller Status
```bash
docker exec kafka kafka-metadata --snapshot /var/lib/kafka/data/__cluster_metadata-0/00000000000000000000.log --command "describe"
```

### Check Broker Configuration
```bash
docker exec kafka kafka-configs \
  --bootstrap-server localhost:9092 \
  --entity-type brokers \
  --entity-name 1 \
  --describe --all
```

### Force Delete a Topic
```bash
docker exec kafka kafka-topics --delete \
  --topic topic-name \
  --bootstrap-server localhost:9092
```

## 📊 Monitoring

### JMX Metrics (Optional)

Add to docker-compose.yml for metrics:

```yaml
environment:
  KAFKA_JMX_PORT: 9999
  KAFKA_JMX_HOSTNAME: localhost
ports:
  - "9999:9999"
```

### Health Check

The docker-compose includes a health check:

```yaml
healthcheck:
  test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 30s
```

## 📚 References

- [KIP-500: Replace ZooKeeper with Self-Managed Metadata Quorum](https://cwiki.apache.org/confluence/display/KAFKA/KIP-500%3A+Replace+ZooKeeper+with+a+Self-Managed+Metadata+Quorum)
- [Confluent KRaft Documentation](https://docs.confluent.io/platform/current/kafka-metadata/kraft.html)
- [Apache Kafka KRaft Documentation](https://kafka.apache.org/documentation/#kraft)

## 📅 Version History

| Date | Change |
|------|--------|
| Nov 2025 | Migrated from Zookeeper to KRaft mode |

---

**Note:** This documentation is specific to the NYC Taxi Data Pipeline project. Adjust configurations as needed for your use case.
