# Grafana Alerts Setup Guide

## Overview
This guide provides step-by-step instructions for creating all required Grafana alerts via the Grafana UI.

---

## Prerequisites
- Grafana is accessible at `http://192.168.56.25:3000`
- Prometheus data source is configured
- You're logged in as admin/admin

---

## Alert 1: VM CPU High (>80% for 5 minutes)

### Step 1: Enter Alert Rule Name
- **Name:** `VM CPU High`

### Step 2: Define Query and Alert Condition

1. Click **"Add query"** or use the existing query section
2. **Data source:** Select `Prometheus`
3. **Query A:** Enter this PromQL query:
   ```
   100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
   ```
4. **Legend:** `{{instance}} - CPU Usage`
5. **Format:** Time series

6. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS ABOVE:** `80`
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** Create new folder: `Infrastructure Alerts` (or use existing)
- **Labels:**
  - `severity` = `warning`
  - `alertname` = `VM_CPU_High`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** Create new: `infrastructure` (or use existing)
- **Evaluation interval:** `30s` (default)
- **Pending period:** `5m` (5 minutes)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure notification policy if needed

### Step 6: Save
- Click **"Save"** or **"Save and exit"**

---

## Alert 2: VM Disk Space Low (<20% available)

### Step 1: Enter Alert Rule Name
- **Name:** `VM Disk Space Low`

### Step 2: Define Query and Alert Condition

1. **Query A:** Enter this PromQL query:
   ```
   (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
   ```
2. **Legend:** `{{instance}} - Disk Available %`
3. **Format:** Time series

4. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS BELOW:** `20`
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts`
- **Labels:**
  - `severity` = `critical`
  - `alertname` = `VM_Disk_Low`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure`
- **Pending period:** `1m` (1 minute - immediate alert)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Alert 3: VM Memory High (>90% for 5 minutes)

### Step 1: Enter Alert Rule Name
- **Name:** `VM Memory High`

### Step 2: Define Query and Alert Condition

1. **Query A:** Enter this PromQL query:
   ```
   (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
   ```
2. **Legend:** `{{instance}} - Memory Usage %`
3. **Format:** Time series

4. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS ABOVE:** `90`
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts`
- **Labels:**
  - `severity` = `warning`
  - `alertname` = `VM_Memory_High`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure`
- **Pending period:** `5m` (5 minutes)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Alert 4: Container Restart High (>3 restarts in 15 minutes)

### Step 1: Enter Alert Rule Name
- **Name:** `Container Restart High`

### Step 2: Define Query and Alert Condition

1. **Query A:** Enter this PromQL query:
   ```
   increase(container_start_time_seconds{name!=""}[15m])
   ```
2. **Legend:** `{{name}} on {{instance}} - Restarts`
3. **Format:** Time series

4. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS ABOVE:** `3`
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts` (or create `Container Alerts`)
- **Labels:**
  - `severity` = `warning`
  - `alertname` = `Container_Restart_High`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure` (or `containers`)
- **Pending period:** `1m` (1 minute)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Alert 5: Container Memory High (>80% of limit)

### Step 1: Enter Alert Rule Name
- **Name:** `Container Memory High`

### Step 2: Define Query and Alert Condition

1. **Query A:** Enter this PromQL query:
   ```
   (container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) * 100
   ```
2. **Legend:** `{{name}} on {{instance}} - Memory %`
3. **Format:** Time series

   **Note:** This query only works for containers with memory limits set. You may need to filter:
   ```
   (container_memory_usage_bytes{name!="",container_spec_memory_limit_bytes>0} / container_spec_memory_limit_bytes{name!="",container_spec_memory_limit_bytes>0}) * 100
   ```

4. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS ABOVE:** `80`
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts` (or `Container Alerts`)
- **Labels:**
  - `severity` = `warning`
  - `alertname` = `Container_Memory_High`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure` (or `containers`)
- **Pending period:** `5m` (5 minutes)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Alert 6: VM Unreachable (Node Exporter down)

### Step 1: Enter Alert Rule Name
- **Name:** `VM Unreachable`

### Step 2: Define Query and Alert Condition

1. **Query A:** Enter this PromQL query:
   ```
   up{job="node_exporter"}
   ```
2. **Legend:** `{{instance}} - Node Exporter Status`
3. **Format:** Time series

4. **Alert condition:**
   - **WHEN:** `last()`
   - **OF:** `A`
   - **IS BELOW:** `1`
   - (Or use **IS EQUAL TO:** `0`)
   - Click **"Preview alert rule condition"** to verify

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts`
- **Labels:**
  - `severity` = `critical`
  - `alertname` = `VM_Unreachable`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure`
- **Pending period:** `1m` (1 minute - immediate alert)
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Alert 7: Elasticsearch Health Alert (Phase 5.2)

### Step 1: Enter Alert Rule Name
- **Name:** `Elasticsearch Cluster Health`

### Step 2: Define Query and Alert Condition

**Note:** This requires a custom Prometheus exporter for Elasticsearch or using Elasticsearch's metrics endpoint.

**Option 1: If you have Elasticsearch exporter:**
1. **Query A:** 
   ```
   elasticsearch_cluster_health_status{color="yellow"} or elasticsearch_cluster_health_status{color="red"}
   ```

**Option 2: Using HTTP probe (if configured):**
1. **Query A:**
   ```
   probe_http_status_code{instance="localhost:9200"} != 200
   ```

**Option 3: Manual check via script (simpler for now):**
- This alert may need to be created differently or skipped if Elasticsearch exporter is not set up
- You can create a simple alert that checks if Elasticsearch is responding on port 9200

### Step 3: Add Folder and Labels
- **Folder:** `Infrastructure Alerts` (or create `Elasticsearch Alerts`)
- **Labels:**
  - `severity` = `critical`
  - `alertname` = `Elasticsearch_Health`

### Step 4: Set Evaluation Behavior
- **Evaluation group:** `infrastructure`
- **Pending period:** `1m`
- **Keep firing for:** `None` or `1m`

### Step 5: Configure Notifications
- Leave default or configure as needed

### Step 6: Save
- Click **"Save"**

---

## Verification

After creating all alerts:

1. Go to **Alerting** > **Alert rules**
2. Verify all 6 (or 7) alerts are listed
3. Check each alert shows:
   - Correct query
   - Correct condition
   - Correct labels
   - Correct evaluation settings

## Testing

See `PHASE5_TESTING.md` for detailed testing procedures for each alert.

---

## Quick Reference: PromQL Queries

| Alert | PromQL Query |
|-------|-------------|
| VM CPU High | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` |
| VM Disk Low | `(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100` |
| VM Memory High | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` |
| Container Restart High | `increase(container_start_time_seconds{name!=""}[15m])` |
| Container Memory High | `(container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""}) * 100` |
| VM Unreachable | `up{job="node_exporter"}` |

---

## Troubleshooting

### Query returns no data
- Check Prometheus is collecting the metric: Go to Prometheus > Graph and test the query
- Verify the metric name is correct
- Check time range (some metrics may not have historical data)

### Alert condition not working
- Use "Preview alert rule condition" to test
- Verify the condition logic (ABOVE/BELOW/EQUAL TO)
- Check the threshold value is correct

### Alert not firing
- Check evaluation interval (should be 30s or less)
- Verify pending period is appropriate
- Check if condition is actually met (view query results)

---

**Next Steps:** After creating alerts, test them using the procedures in `PHASE5_TESTING.md`

