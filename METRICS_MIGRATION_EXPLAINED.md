# How We Rewrote Infrastructure Metrics

## Overview

We migrated from a basic JSON-based metrics system to a **Prometheus-based monitoring architecture** with three layers of metrics collection:

1. **System-level metrics** (Node Exporter)
2. **Container-level metrics** (cAdvisor)
3. **Application-level metrics** (Prometheus client library)

---

## What Changed?

### Before (Old System)
- Applications exposed metrics as **JSON** at `/metrics` endpoint
- No standardized format
- Manual collection and aggregation
- Limited querying capabilities
- No infrastructure-level metrics (CPU, memory, disk)

### After (New System)
- **Prometheus** as central metrics collection system
- **Standardized Prometheus format** (text-based, time-series)
- **Pull-based model** (Prometheus scrapes targets every 15 seconds)
- **Multi-dimensional data model** (labels for filtering/grouping)
- **Three-layer architecture** covering system, container, and application metrics

---

## Architecture: Three Layers of Metrics

### Layer 1: System Metrics (Node Exporter)

**What it does:**
- Collects **VM-level** infrastructure metrics (CPU, memory, disk, network)
- Runs as a systemd service on every VM

**Implementation:**
```yaml
# Installed on all 6 VMs:
- lb-server-auto (192.168.56.20:9100)
- web1-server-auto (192.168.56.21:9100)
- web2-server-auto (192.168.56.22:9100)
- app-server-auto (192.168.56.23:9100)
- backup-server-auto (192.168.56.24:9100)
- monitoring-server-auto (192.168.56.25:9100)
```

**Metrics collected:**
- `node_cpu_seconds_total` - CPU usage per core
- `node_memory_MemTotal_bytes` - Total memory
- `node_memory_MemAvailable_bytes` - Available memory
- `node_filesystem_size_bytes` - Disk space
- `node_network_receive_bytes_total` - Network traffic
- `node_load1`, `node_load5`, `node_load15` - Load averages

**Why Node Exporter:**
- Standard Prometheus exporter for system metrics
- Lightweight, runs as a single binary
- Provides comprehensive OS-level visibility

---

### Layer 2: Container Metrics (cAdvisor)

**What it does:**
- Collects **Docker container-level** metrics (CPU, memory, network per container)
- Runs as a Docker container itself
- Only deployed on VMs that run Docker containers

**Implementation:**
```yaml
# Deployed on Docker-enabled VMs:
- web1-server-auto (192.168.56.21:8080)
- web2-server-auto (192.168.56.22:8080)
- app-server-auto (192.168.56.23:8080)
```

**Metrics collected:**
- `container_cpu_usage_seconds_total` - Container CPU usage
- `container_memory_usage_bytes` - Container memory usage
- `container_network_receive_bytes_total` - Container network I/O
- `container_start_time_seconds` - Container start time (for restart detection)
- `container_spec_memory_limit_bytes` - Memory limits

**Why cAdvisor:**
- Google's container advisor tool
- Automatically discovers all containers on a host
- Provides detailed per-container resource usage
- Essential for container restart detection and resource monitoring

---

### Layer 3: Application Metrics (Prometheus Client)

**What it does:**
- Collects **application-specific** metrics from Flask apps
- Custom business logic metrics (request counts, response times)
- Application resource usage (CPU, memory, disk from app perspective)

**Implementation:**

**Before (JSON format):**
```python
@app.route("/metrics")
def metrics():
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "requests_total": request_count
    })
```

**After (Prometheus format):**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Define metrics
http_requests_total = Counter(
    'flask_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

app_cpu_usage_percent = Gauge(
    'flask_app_cpu_usage_percent',
    'Application CPU usage percentage',
    ['hostname', 'role']
)

@app.route("/metrics")
def metrics():
    # Update metrics
    cpu = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    
    app_cpu_usage_percent.labels(hostname=hostname, role=role).set(cpu)
    app_memory_usage_bytes.labels(hostname=hostname, role=role).set(mem.used)
    
    # Return Prometheus format
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

**Metrics exposed:**
- `flask_http_requests_total` - Total HTTP requests (counter)
- `flask_http_request_duration_seconds` - Request latency (histogram)
- `flask_app_cpu_usage_percent` - CPU usage (gauge)
- `flask_app_memory_usage_bytes` - Memory usage (gauge)
- `flask_app_disk_usage_bytes` - Disk usage (gauge, frontend only)

**Why Prometheus format:**
- Standard time-series format
- Multi-dimensional labels (hostname, role, method, endpoint, status)
- Supports different metric types (Counter, Gauge, Histogram)
- Enables powerful querying with PromQL

---

## Prometheus Configuration

**Centralized scraping configuration:**
```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  # System metrics from all VMs
  - job_name: 'node_exporter'
    static_configs:
      - targets:
          - '192.168.56.20:9100'  # lb
          - '192.168.56.21:9100'  # web1
          - '192.168.56.22:9100'  # web2
          - '192.168.56.23:9100'  # app
          - '192.168.56.24:9100'  # backup
          - '192.168.56.25:9100'  # monitoring
  
  # Container metrics from Docker VMs
  - job_name: 'cadvisor'
    static_configs:
      - targets:
          - '192.168.56.21:8080'  # web1
          - '192.168.56.22:8080'  # web2
          - '192.168.56.23:8080'  # app
  
  # Application metrics from Flask apps
  - job_name: 'flask_apps'
    static_configs:
      - targets:
          - '192.168.56.21:5000'  # web1 (frontend)
          - '192.168.56.22:5000'  # web2 (frontend)
          - '192.168.56.23:5000'  # app (backend)
    metrics_path: '/metrics'
```

**Scrape interval:** 15 seconds (configurable)

---

## Key Benefits of This Approach

### 1. **Pull-Based Model**
- Prometheus **pulls** metrics from targets (vs. push)
- Centralized control over collection frequency
- Targets don't need to know about Prometheus
- Easier to add/remove targets

### 2. **Standardized Format**
- All metrics in Prometheus format
- Consistent across system, container, and application layers
- Easy to query and aggregate

### 3. **Multi-Dimensional Data Model**
- Labels allow filtering and grouping:
  ```promql
  # CPU usage by hostname
  node_cpu_seconds_total{instance="192.168.56.21:9100"}
  
  # Request count by endpoint
  flask_http_requests_total{endpoint="/dashboard"}
  
  # Container memory by container name
  container_memory_usage_bytes{name="flask_backend"}
  ```

### 4. **Comprehensive Coverage**
- **System layer:** VM health (CPU, memory, disk, network)
- **Container layer:** Container resource usage and restarts
- **Application layer:** Business metrics (requests, latency, errors)

### 5. **Powerful Querying (PromQL)**
- Calculate rates: `rate(http_requests_total[5m])`
- Aggregations: `sum(node_memory_MemTotal_bytes)`
- Percentiles: `histogram_quantile(0.95, http_request_duration_seconds)`
- Alerts: `node_memory_MemAvailable_bytes < 1GB`

---

## Example Queries

**System CPU usage:**
```promql
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**Container restart count (last 15 minutes):**
```promql
sum by (name, instance) (
  count(count_over_time(
    container_start_time_seconds{name!="",container_label_restartcount!=""}[15m:30s]
  ) > 0)
) - 1
```

**Application request rate:**
```promql
rate(flask_http_requests_total[5m])
```

**Memory usage percentage:**
```promql
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) 
/ node_memory_MemTotal_bytes * 100
```

---

## Files Changed

### Ansible Roles:
- `ansible/roles/node_exporter/` - Node Exporter installation
- `ansible/roles/cadvisor/` - cAdvisor container deployment
- `ansible/roles/monitoring/tasks/main.yml` - Prometheus configuration

### Application Code:
- `ansible/roles/backend_container/files/app/app.py` - Prometheus metrics
- `ansible/roles/frontend_container/files/app/app.py` - Prometheus metrics
- `ansible/roles/app_deploy/files/flask_app/app.py` - Prometheus metrics
- `ansible/roles/*/files/app/requirements.txt` - Added `prometheus-client`

---

## Summary

**We rewrote infrastructure metrics by:**

1. ✅ **Adding Node Exporter** to all VMs for system-level metrics
2. ✅ **Adding cAdvisor** to Docker VMs for container-level metrics
3. ✅ **Converting application metrics** from JSON to Prometheus format
4. ✅ **Configuring Prometheus** to scrape all three layers
5. ✅ **Standardizing on Prometheus** format across all metrics sources

**Result:** A unified, queryable, time-series metrics system that provides complete visibility into system, container, and application health.

