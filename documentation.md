# 🕵️ Sherlock Logs - Project Documentation

## Overview

This project implements a comprehensive monitoring and logging system for a distributed infrastructure using Prometheus + Grafana for metrics and the ELK stack (Elasticsearch, Logstash, Kibana) for centralized logging.

---

## Phase 1: Infrastructure Setup ✅

### What We Did

We added a new virtual machine dedicated to hosting all monitoring and logging tools. This VM is separate from the application infrastructure to ensure monitoring services don't interfere with application performance.

### Changes Made

#### 1. **Added Monitoring VM to Vagrantfile**

**File:** `Vagrantfile`

**What changed:**
- Added `monitoring-server-auto` to the servers configuration
- Assigned IP address: `192.168.56.25`
- Configured with 1GB RAM and 1 CPU (standard for monitoring VM)
- Updated SSH key distribution to include the new monitoring VM

**Why:**
- Prometheus, Grafana, and ELK stack need their own dedicated server
- Separating monitoring from application servers ensures monitoring continues even if applications have issues
- The IP `192.168.56.25` follows the existing network pattern (20=lb, 21-22=web, 23=app, 24=backup, 25=monitoring)

**Code location:**
```ruby
servers = {
  "web1-server-auto"   => "192.168.56.21",
  "web2-server-auto"   => "192.168.56.22",
  "app-server-auto"    => "192.168.56.23",
  "backup-server-auto" => "192.168.56.24",
  "monitoring-server-auto" => "192.168.56.25"  # ← New addition
}
```

#### 2. **Updated Ansible Inventory**

**File:** `ansible/inventory.ini`

**What changed:**
- Added `[monitoring]` group with IP `192.168.56.25`
- Configured to use `vagrant` user for SSH access

**Why:**
- Ansible needs to know about the new VM to provision it
- Grouping allows us to apply monitoring-specific roles only to this VM
- Consistent with existing inventory structure

**Code location:**
```ini
[monitoring]
192.168.56.25 ansible_user=vagrant
```

#### 3. **Updated Ansible Playbook**

**File:** `ansible/site.yml`

**What changed:**
- Added a new play for the `monitoring` host group
- Configured to run the `monitoring` role

**Why:**
- Ensures the monitoring VM gets provisioned during automated setup
- Follows the same pattern as other VMs (web, app, backup)
- Allows us to apply monitoring-specific configuration

**Code location:**
```yaml
- hosts: monitoring
  become: yes
  roles:
    - monitoring
```

#### 4. **Created Monitoring Ansible Role**

**Files created:**
- `ansible/roles/monitoring/tasks/main.yml`
- `ansible/roles/monitoring/handlers/main.yml`

**What changed:**
- Created basic role structure with placeholder tasks
- Added a debug task to verify the VM is ready

**Why:**
- Establishes the foundation for future monitoring setup (Prometheus, Grafana, ELK)
- Follows Ansible best practices for role organization
- Makes it easy to add monitoring components in subsequent phases

**Code location:**
```yaml
- name: Ensure monitoring VM is ready
  debug:
    msg: "Monitoring VM ({{ ansible_hostname }}) is ready for monitoring/logging setup"
```

#### 5. **Improved SSH Key Distribution**

**File:** `Vagrantfile`

**What changed:**
- Made SSH key distribution more resilient
- Added error handling to skip VMs that don't exist yet
- Added timeout to prevent hanging on missing VMs

**Why:**
- Allows provisioning to continue even if some VMs aren't created yet
- Prevents failures when creating VMs incrementally
- Better user experience during setup

**Code location:**
```ruby
# Try to connect, but don't fail if VM doesn't exist yet
if sshpass -p "vagrant" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 vagrant@$ip "..." 2>/dev/null; then
  echo "Successfully added SSH key to $ip"
else
  echo "Warning: Could not connect to $ip (VM may not exist yet, will retry on next provision)"
fi
```

### Verification

All tests passed successfully:

✅ **VM Creation:** Monitoring VM created and running at 192.168.56.25  
✅ **Network Configuration:** IP address correctly assigned to eth1  
✅ **SSH Connectivity:** Passwordless SSH working from load balancer  
✅ **Ansible Connectivity:** Ansible can connect and run tasks  
✅ **Monitoring Role:** Role executes successfully  
✅ **Playbook Integration:** Monitoring VM included in full playbook  
✅ **Inventory Configuration:** Monitoring group properly configured  


## Phase 2: Prometheus Setup ✅

### What We Did

We set up Prometheus as the central metrics collection system. Prometheus pulls metrics from all infrastructure components (VMs, containers, and applications) and stores them in a time-series database. This provides the foundation for monitoring and alerting.

### Changes Made

#### 1. **Installed Prometheus on Monitoring VM**

**File:** `ansible/roles/monitoring/tasks/main.yml`

**What changed:**
- Created dedicated `prometheus` system user
- Dynamically fetches latest Prometheus version from GitHub
- Downloads and installs Prometheus binary
- Configures Prometheus as a systemd service
- Opens firewall port 9090 for web UI access

**Why:**
- Prometheus is the core of our monitoring stack
- Systemd service ensures it starts automatically on boot
- Latest version ensures we have the newest features and security fixes
- Port 9090 is the standard Prometheus web UI port

**Key configuration:**
- **Scrape interval:** 15 seconds (how often Prometheus collects metrics)
- **Evaluation interval:** 15 seconds (how often alert rules are evaluated)
- **Storage path:** `/var/lib/prometheus/data`
- **Web UI:** Accessible at `http://192.168.56.25:9090`

#### 2. **Installed Node Exporter on All VMs**

**File:** `ansible/roles/node_exporter/tasks/main.yml`

**What changed:**
- Created Ansible role for Node Exporter
- Installed Node Exporter on all 6 VMs (lb, web1, web2, app, backup, monitoring)
- Configured as systemd service on each VM
- Opened firewall port 9100 on all VMs
- Updated Prometheus config to scrape all Node Exporter targets

**Why:**
- Node Exporter provides system-level metrics (CPU, memory, disk, network)
- Needed on every VM to monitor infrastructure health
- Port 9100 is the standard Node Exporter port
- Systemd ensures it runs automatically

**Metrics collected:**
- CPU usage and load average
- Memory utilization (RAM and swap)
- Disk I/O and space usage
- Network traffic and errors
- System uptime and process counts

#### 3. **Installed cAdvisor on Docker-Enabled VMs**

**File:** `ansible/roles/cadvisor/tasks/main.yml`

**What changed:**
- Installed cAdvisor as Docker container on web1, web2, and app VMs
- Configured with necessary volume mounts for container metrics
- Opened firewall port 8080
- Updated Prometheus config to scrape cAdvisor targets

**Why:**
- cAdvisor provides container-level metrics (CPU, memory, network per container)
- Only needed on VMs running Docker containers
- Docker container approach is simpler than installing binaries
- Port 8080 is the standard cAdvisor port

**Metrics collected:**
- Container CPU usage
- Container memory usage and limits
- Container network I/O
- Container filesystem usage
- Container restart counts

#### 4. **Converted Application Metrics to Prometheus Format**

**Files changed:**
- `ansible/roles/frontend_container/files/app/app.py`
- `ansible/roles/backend_container/files/app/app.py`
- `ansible/roles/app_deploy/files/flask_app/app.py`
- `ansible/roles/frontend_container/files/app/requirements.txt`
- `ansible/roles/backend_container/files/app/requirements.txt`

**What changed:**
- Added `prometheus_client` Python library to all Flask apps
- Rewrote `/metrics` endpoint to return Prometheus format (instead of JSON)
- Added custom application metrics:
  - `flask_http_requests_total` - Total HTTP requests (counter)
  - `flask_http_request_duration_seconds` - Request latency (histogram)
  - `flask_app_info` - Application metadata (info metric)
  - `flask_app_cpu_usage_percent` - CPU usage (gauge)
  - `flask_app_memory_usage_bytes` - Memory usage (gauge)
  - `flask_app_disk_usage_bytes` - Disk usage (gauge, frontend only)
- Updated Prometheus config to scrape application metrics
- Updated firewall rules to allow monitoring server access to port 5000

**Why:**
- Prometheus format is standard and widely supported
- Custom metrics provide application-specific insights
- Histograms allow us to calculate percentiles (P50, P95, P99)
- Gauges show current state (CPU, memory, disk)
- Counters track cumulative values (total requests)

**Metrics exposed:**
- Request count and rate
- Request latency (response times)
- Application health and metadata
- Resource usage (CPU, memory, disk)

### Verification

All tests passed successfully:

✅ **Prometheus:** Running and accessible at http://192.168.56.25:9090  
✅ **Node Exporter:** Installed on all 6 VMs, all targets UP in Prometheus  
✅ **cAdvisor:** Running on web1, web2, and app VMs, all containers healthy  
✅ **Application Metrics:** All Flask apps exposing Prometheus metrics  
✅ **Scrape Configuration:** All targets being scraped every 15 seconds  
✅ **Firewall Rules:** All necessary ports opened correctly  

### Testing

Comprehensive testing guides are available:
- `PHASE1_TESTING.md` - Infrastructure setup testing
- `PHASE2_STEP23_TESTING.md` - cAdvisor testing guide
- `PHASE2_STEP24_TESTING.md` - Application metrics testing guide

### What's Next

With Phase 2 complete, we now have:
- Prometheus collecting metrics from all sources
- System metrics from all VMs (Node Exporter)
- Container metrics from Docker hosts (cAdvisor)
- Application metrics from Flask apps
- Foundation for Phase 3: Grafana Visualization

---

## Phase 3: Grafana Setup (In Progress)

### Phase 3, Step 3.1: Install and Configure Grafana ✅

### What We Did

We installed Grafana, a powerful visualization tool that connects to Prometheus and allows us to create beautiful dashboards for monitoring our infrastructure. Grafana provides a user-friendly web interface for exploring metrics and creating custom visualizations.

### Changes Made

#### 1. **Installed Grafana from .deb Package**

**File:** `ansible/roles/monitoring/tasks/main.yml`

**What changed:**
- Removed any existing Grafana repository files (to avoid conflicts)
- Fetches latest Grafana version from GitHub API
- Downloads Grafana .deb package directly from Grafana CDN
- Installs Grafana using `apt` with the `deb` parameter
- Configures Grafana as systemd service
- Opens firewall port 3000 for web UI access

**Why:**
- .deb package installation avoids GPG keyring issues
- Direct download from Grafana CDN is more reliable
- Systemd service ensures automatic startup
- Port 3000 is the standard Grafana web UI port

**Installation details:**
- **Version:** 12.3.0 (latest stable)
- **Service:** `grafana-server`
- **Config:** `/etc/grafana/grafana.ini`
- **Data:** `/var/lib/grafana`
- **Web UI:** Accessible at `http://192.168.56.25:3000`

#### 2. **Configured Prometheus as Data Source**

**File:** `ansible/roles/monitoring/tasks/main.yml`

**What changed:**
- Created Grafana provisioning directory: `/etc/grafana/provisioning/datasources`
- Created Prometheus data source configuration file
- Configured Prometheus URL: `http://localhost:9090`
- Set as default data source
- Configured scrape interval: 15 seconds

**Why:**
- Provisioning allows automatic data source setup (no manual configuration)
- Localhost connection is secure (Prometheus on same VM)
- Default data source means it's selected automatically in queries
- Matches Prometheus scrape interval for consistency

**Configuration file:**
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
```

#### 3. **Configured Admin Credentials**

**File:** `ansible/roles/monitoring/tasks/main.yml`

**What changed:**
- Set admin username: `admin`
- Set admin password: `admin`
- Configured Grafana to listen on all interfaces (0.0.0.0)
- Set port to 3000

**Why:**
- Default credentials for initial setup (should be changed in production)
- Listening on all interfaces allows access from host machine
- Standard port 3000 for Grafana

**Security note:**
- Default credentials (`admin/admin`) are for development/testing
- In production, change these immediately after first login
- Consider using environment variables or secrets management

#### 4. **Added Grafana Restart Handler**

**File:** `ansible/roles/monitoring/handlers/main.yml`

**What changed:**
- Added `restart grafana` handler
- Triggers when Grafana configuration changes

**Why:**
- Ensures configuration changes take effect
- Follows Ansible best practices for service management
- Prevents manual restart steps

### Verification

All tests passed successfully:

✅ **Grafana Installation:** Version 12.3.0 installed and running  
✅ **Service Status:** `grafana-server` active and enabled  
✅ **Port Access:** Listening on 0.0.0.0:3000  
✅ **Health Check:** API returns `{"database": "ok", "version": "12.3.0"}`  
✅ **Prometheus Data Source:** Configured and showing "Health: OK"  
✅ **Web UI:** Accessible at http://192.168.56.25:3000 (or via SSH port forwarding)  
✅ **Login:** Works with admin/admin credentials  
✅ **Query Testing:** Can query Prometheus metrics (e.g., `up` query works)  
✅ **Dashboards Provisioned:** All three dashboards automatically loaded:
   - VM Performance Dashboard (uid: `vm-performance`)
   - Docker Container Dashboard (uid: `docker-containers`)
   - Application Performance Dashboard (uid: `application-performance`)  

### Testing

A comprehensive testing guide is available in `PHASE3_STEP31_TESTING.md` with step-by-step instructions to verify Grafana installation and configuration.

### What's Next

With Phase 3, Step 3.1 complete, we now have:
- Grafana installed and running
- Prometheus data source automatically configured
- Web UI accessible and functional
- Foundation for creating dashboards (Steps 3.2, 3.3, 3.4)

**Next Steps:**
- **Step 3.2:** Create VM Performance Dashboard
- **Step 3.3:** Create Docker Container Dashboard
- **Step 3.4:** Create Application Performance Dashboard

---

## Phase 4: ELK Stack Setup ✅

### Phase 4.6: Kibana Dashboards Creation ✅

### What We Did

We created three comprehensive Kibana dashboards for log analysis and visualization. These dashboards provide insights into system logs, application logs, and Docker container logs, enabling efficient troubleshooting and monitoring of the entire infrastructure.

### Changes Made

#### 1. **Created System Logs Dashboard**

**What changed:**
- Created three visualizations using Kibana Lens:
  - **System Logs Count by Type:** Bar chart showing count of system logs
  - **System Logs Timeline:** Time-series chart showing log volume over time
  - **System Logs by Hostname:** Pie chart showing distribution of logs across servers
- Combined all three visualizations into a single dashboard
- Applied filter: `fields.log_type: system`

**Why:**
- System logs (syslog, auth.log, kern.log) are critical for infrastructure monitoring
- Timeline visualization helps identify patterns and spikes in log activity
- Hostname distribution shows which servers are generating the most logs
- Centralized view makes troubleshooting easier

**Dashboard details:**
- **Name:** "System Logs Dashboard"
- **Data view:** `logs-*`
- **Filter:** `fields.log_type: system`
- **Access:** http://192.168.56.25:5601/app/dashboards

#### 2. **Created Application Logs Dashboard**

**What changed:**
- Created three visualizations:
  - **Application Logs Count by Type:** Bar chart showing count of application logs
  - **Application Logs Timeline:** Time-series chart showing application log activity over time
  - **Application Logs by Hostname:** Pie chart showing which servers generate application logs
- Combined all three visualizations into a single dashboard
- Applied filter: `fields.log_type: application`

**Why:**
- Application logs provide insights into application behavior and errors
- Timeline helps identify when application issues occur
- Hostname distribution shows which application servers are most active
- Essential for debugging application-specific problems

**Dashboard details:**
- **Name:** "Application Logs Dashboard"
- **Data view:** `logs-*`
- **Filter:** `fields.log_type: application`
- **Access:** http://192.168.56.25:5601/app/dashboards

#### 3. **Created Docker Logs Dashboard**

**What changed:**
- Created three visualizations:
  - **Docker Logs Count by Type:** Bar chart showing count of Docker container logs
  - **Docker Logs Timeline:** Time-series chart showing Docker log activity over time
  - **Docker Logs by Hostname:** Pie chart showing distribution of Docker logs across servers
- Combined all three visualizations into a single dashboard
- Applied filter: `fields.log_type: docker`

**Why:**
- Docker logs (stdout/stderr from containers) are crucial for containerized application monitoring
- Timeline helps identify container restart patterns and activity spikes
- Hostname distribution shows which Docker hosts are generating the most logs
- Critical for debugging container-specific issues

**Dashboard details:**
- **Name:** "Docker Logs Dashboard"
- **Data view:** `logs-*`
- **Filter:** `fields.log_type: docker`
- **Access:** http://192.168.56.25:5601/app/dashboards

#### 4. **Automated Index Pattern Creation**

**File:** `ansible/roles/monitoring/files/create_kibana_dashboards.py`

**What changed:**
- Created Python script to automatically create `logs-*` index pattern in Kibana
- Script waits for Kibana to be ready before creating index pattern
- Handles Kibana interactive setup completion programmatically
- Converts Windows line endings to Unix for Linux execution

**Why:**
- Index pattern is required before creating dashboards
- Automation ensures consistent setup across environments
- Reduces manual configuration steps
- Handles Kibana 8.19+ interactive setup requirements

**Script features:**
- Waits for Kibana API to be ready (up to 30 retries)
- Completes Kibana interactive setup if needed
- Creates `logs-*` index pattern with `@timestamp` as time field
- Provides clear error messages and status updates

### Verification

All tests passed successfully:

✅ **System Logs Dashboard:** Created with 3 visualizations, showing system log data  
✅ **Application Logs Dashboard:** Created with 3 visualizations, showing application log data  
✅ **Docker Logs Dashboard:** Created with 3 visualizations, showing Docker log data  
✅ **Index Pattern:** `logs-*` automatically created and configured  
✅ **Data Visualization:** All dashboards display real-time log data  
✅ **Filters:** All dashboards correctly filter by log type  
✅ **Time Range:** Dashboards support time range selection (Last 15 minutes, 24 hours, 7 days, etc.)  
✅ **Hostname Distribution:** Pie charts correctly show log distribution across servers  

### Testing

A comprehensive testing guide is available in `PHASE4_TESTING.md` with detailed steps for verifying:
- Kibana installation and configuration
- Index pattern creation
- Dashboard creation and functionality
- Log filtering and visualization

### What's Next

With Phase 4.6 complete, we now have:
- Three comprehensive Kibana dashboards for log analysis
- Automated index pattern creation
- Real-time log visualization and filtering
- Foundation for log-based troubleshooting

**Next Steps:**
- **Phase 5:** Configure Grafana Alerts for proactive monitoring ✅ (Complete)
- **Phase 6:** Automation Integration
- **Phase 7:** Testing & Documentation

---

## Phase 5: Alerting Configuration ✅

### Phase 5.1: Grafana Alerts ✅

### What We Did

We configured 6 comprehensive Grafana alert rules for proactive monitoring of infrastructure, containers, and applications. These alerts notify administrators when critical thresholds are exceeded, enabling rapid response to issues.

### Changes Made

#### 1. **VM CPU High Alert**

**Configuration:**
- **Query:** `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **Condition:** `> 80` (CPU usage above 80%)
- **Duration:** 5 minutes
- **Labels:** `severity: warning`, `alertname: VM_CPU_High`
- **Folder:** Infrastructure Alerts

**Why:**
- High CPU usage can indicate performance issues or resource exhaustion
- 5-minute duration prevents false positives from temporary spikes
- Enables proactive capacity planning

#### 2. **VM Disk Space Low Alert**

**Configuration:**
- **Query:** `(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100`
- **Condition:** `< 20` (less than 20% disk space available)
- **Duration:** 1 minute (immediate)
- **Labels:** `severity: critical`, `alertname: VM_Disk_Low`
- **Folder:** Infrastructure Alerts

**Why:**
- Low disk space can cause application failures and data loss
- Immediate alerting prevents disk-full scenarios
- Critical severity ensures urgent attention

#### 3. **VM Memory High Alert**

**Configuration:**
- **Query:** `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **Condition:** `> 90` (memory usage above 90%)
- **Duration:** 5 minutes
- **Labels:** `severity: warning`, `alertname: VM_Memory_High`
- **Folder:** Infrastructure Alerts

**Why:**
- High memory usage can lead to OOM (Out of Memory) kills
- 5-minute duration accounts for memory spikes
- Helps identify memory leaks or insufficient resources

#### 4. **Container Restart High Alert**

**Configuration:**
- **Query:** `increase(container_start_time_seconds{name!=""}[15m])`
- **Condition:** `> 3` (more than 3 restarts in 15 minutes)
- **Duration:** 1 minute
- **Labels:** `severity: warning`, `alertname: Container_Restart_High`
- **Folder:** Infrastructure Alerts

**Why:**
- Frequent container restarts indicate application instability
- Helps identify crash loops or configuration issues
- Critical for containerized application reliability

#### 5. **Container Memory High Alert**

**Configuration:**
- **Query:** `(container_memory_usage_bytes{name!=""} / container_memory_working_set_bytes{name!=""}) * 100`
- **Condition:** `> 80` (memory usage above 80% of working set)
- **Duration:** 5 minutes
- **Labels:** `severity: warning`, `alertname: Container_Memory_High`
- **Folder:** Infrastructure Alerts

**Why:**
- High container memory usage can lead to OOM kills
- Uses working set to avoid division by zero errors
- Helps optimize container resource limits

#### 6. **VM Unreachable Alert**

**Configuration:**
- **Query:** `up{job="node_exporter"} == 0`
- **Condition:** `IS ABOVE 0` (any Node Exporter is down)
- **Duration:** 1 minute
- **Labels:** `severity: critical`, `alertname: VM_Unreachable`
- **Folder:** Infrastructure Alerts

**Why:**
- Detects when VMs are completely unreachable
- Critical for infrastructure availability monitoring
- Immediate alerting for network or VM failures

### Phase 5.2: Elasticsearch Health Alert ✅

### What We Did

We created an Elasticsearch health monitoring alert that indirectly monitors Elasticsearch availability by checking the monitoring server's Node Exporter status.

### Changes Made

#### 1. **Elasticsearch Cluster Health Alert**

**Configuration:**
- **Query:** `1 - up{job="node_exporter", instance=~".*192.168.56.25.*"}`
- **Condition:** `IS ABOVE 0` (monitoring server's Node Exporter is down)
- **Duration:** 5 minutes (pending period)
- **Labels:** `severity: critical`, `alertname: Elasticsearch_Health`
- **Folder:** Infrastructure Alerts
- **Evaluation:** Every 5 minutes

**Why:**
- Elasticsearch runs on the monitoring server (192.168.56.25)
- If the monitoring server's Node Exporter is down, Elasticsearch is likely down too
- Provides indirect but effective health monitoring
- Critical severity ensures immediate attention

**Note:** This is a temporary solution. For production environments, consider:
- Installing an Elasticsearch exporter for direct health metrics
- Using Elasticsearch's native metrics endpoint
- Configuring a blackbox exporter for HTTP health checks

#### Automation of Alert Creation

**File:** `ansible/roles/monitoring/files/create_grafana_alerts.py`

**What changed:**
- Created Python script to automatically create all 7 Grafana alert rules via Unified Alerting API
- Script waits for Grafana to be ready before creating alerts
- Handles existing alerts gracefully (skips if already exists)
- Converts Windows line endings to Unix for Linux execution

**Why:**
- Fully automated setup - no manual intervention required
- Ensures consistent alert configuration across environments
- Aligns with requirement: "Setup of the new monitoring and logging VM is incorporated into the existing automation flow"
- Reduces human error in alert configuration
- Makes provisioning reproducible

**Script features:**
- Waits for Grafana API to be ready (up to 30 retries)
- Gets Prometheus datasource UID automatically
- Creates all 7 alerts using Grafana's Unified Alerting API
- Provides clear success/failure messages for each alert
- Returns summary of alerts created/failed

**Ansible integration:**
- Script is copied to `/usr/local/bin/create_grafana_alerts.py` during provisioning
- Line endings are automatically converted (Windows to Unix)
- Script is executed automatically after Grafana is ready
- All alerts are created in "Infrastructure Alerts" folder

### Verification

All tests passed successfully:

✅ **Grafana Alerts:** All 7 alert rules automatically created and configured  
✅ **Alert Automation:** Python script successfully creates all alerts via API  
✅ **Alert Queries:** All PromQL queries return correct data  
✅ **Alert Conditions:** All conditions properly configured  
✅ **Alert Labels:** All labels correctly set  
✅ **Evaluation Behavior:** All alerts use correct evaluation groups and intervals  
✅ **Elasticsearch Alert:** Created and monitoring monitoring server health  
✅ **Alert Status:** All alerts show "Normal" when conditions are not met  
✅ **Reproducibility:** Alerts are automatically recreated on `vagrant provision`  

### Testing

A comprehensive testing guide is available in `PHASE5_TESTING.md` with detailed steps for:
- Verifying alert rule configuration
- Testing each alert by simulating conditions
- Verifying alert firing and resolution
- Testing alert history and evaluation

### What's Next

With Phase 5 complete, we now have:
- 6 Grafana alerts for infrastructure monitoring
- 1 Elasticsearch health alert
- Proactive alerting for critical issues
- Foundation for notification channels (email, webhooks, etc.)

**Next Steps:**
- **Phase 6:** Automation Integration
- **Phase 7:** Testing & Documentation

---

## Architecture Overview

### Current Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    Network: 192.168.56.0/24                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  192.168.56.20  ──  lb-server-auto      (Load Balancer)     │
│  192.168.56.21  ──  web1-server-auto    (Web Server 1)       │
│  192.168.56.22  ──  web2-server-auto    (Web Server 2)       │
│  192.168.56.23  ──  app-server-auto     (Application Server) │
│  192.168.56.24  ──  backup-server-auto  (Jenkins CI/CD)     │
│  192.168.56.25  ──  monitoring-server-auto (NEW - Monitoring)│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Current Architecture (Phase 2 & 3.1 Complete)

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring & Logging Stack                │
│  192.168.56.25 - monitoring-server-auto                     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ Prometheus   │  │  Grafana     │  │  ELK Stack   │      │
│  │ (Port 9090)  │◄─┤ (Port 3000)  │  │ (Ports 9200, │      │
│  │              │  │              │  │  5044, 5601) │      │
│  │ Scrapes:     │  │ Visualizes:  │  │  (Pending)   │      │
│  │ - Node Exp.  │  │ - Metrics    │  │              │      │
│  │ - cAdvisor   │  │ - Dashboards │  │              │      │
│  │ - Flask Apps │  │ - Alerts     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             │ Pulls metrics every 15s
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                    Application Infrastructure                │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Web1   │  │   Web2   │  │   App    │  │  Jenkins │   │
│  │ 192.56.21│  │ 192.56.22│  │192.56.23 │  │192.56.24 │   │
│  │          │  │          │  │          │  │          │   │
│  │ Node     │  │ Node     │  │ Node     │  │  Node    │   │
│  │ Exporter │  │ Exporter │  │ Exporter │  │ Exporter │   │
│  │ :9100    │  │ :9100    │  │ :9100    │  │ :9100    │   │
│  │          │  │          │  │          │  │          │   │
│  │ cAdvisor │  │ cAdvisor │  │ cAdvisor │  │          │   │
│  │ :8080    │  │ :8080    │  │ :8080    │  │          │   │
│  │          │  │          │  │          │  │          │   │
│  │ Flask    │  │ Flask    │  │ Flask    │  │          │   │
│  │ App      │  │ App      │  │ App      │  │          │   │
│  │ :5000    │  │ :5000    │  │ :5000    │  │          │   │
│  │          │  │          │  │          │  │          │   │
│  │ Filebeat │  │ Filebeat │  │ Filebeat │  │ Filebeat │   │
│  │ (Pending)│  │(Pending) │  │(Pending) │  │(Pending) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Legend:**
- ✅ **Implemented:** Prometheus, Grafana, Node Exporter, cAdvisor, Application Metrics
- ⏳ **Pending:** ELK Stack (Elasticsearch, Logstash, Kibana), Filebeat, Dashboards, Alerts

---

## Key Concepts

### Why Separate Monitoring VM?

**Separation of Concerns:**
- Monitoring tools can be resource-intensive
- Keeps application servers focused on serving applications
- If applications crash, monitoring still works (critical for troubleshooting)

**Scalability:**
- Easy to add more monitoring tools without affecting applications
- Can scale monitoring independently from applications
- Centralized location for all observability tools

### Why IP 192.168.56.25?

**Network Organization:**
- Follows logical numbering scheme (20-24 already used)
- Easy to remember and document
- Consistent with existing infrastructure pattern

### Why Ansible Roles?

**Modularity:**
- Each component (Prometheus, Grafana, ELK) can be its own role
- Easy to enable/disable specific monitoring tools
- Reusable across different environments
- Follows infrastructure-as-code best practices

### Prometheus Pull Model

**How It Works:**
- Prometheus **pulls** metrics from targets (opposite of push)
- Targets expose metrics on HTTP endpoints (e.g., `/metrics`)
- Prometheus scrapes these endpoints at regular intervals (15 seconds)
- Metrics are stored in Prometheus's time-series database

**Benefits:**
- Centralized control (Prometheus decides when to collect)
- No need to configure each target to push metrics
- Easy to add/remove targets by updating Prometheus config
- Built-in service discovery support

### Prometheus Metrics Format

**Types of Metrics:**
- **Counter:** Monotonically increasing value (e.g., total requests)
- **Gauge:** Value that can go up or down (e.g., CPU usage)
- **Histogram:** Distribution of values (e.g., request latency)
- **Summary:** Similar to histogram, with quantiles

**Example:**
```
# Counter
flask_http_requests_total{method="GET",status="200"} 154.0

# Gauge
node_memory_MemAvailable_bytes 2147483648

# Histogram
flask_http_request_duration_seconds_bucket{le="0.1"} 120
```

### Grafana Dashboards

**Purpose:**
- Visual representation of metrics from Prometheus
- Customizable panels (graphs, tables, gauges, etc.)
- Time range selection and refresh controls
- Can combine multiple metrics in one view

**Benefits:**
- User-friendly interface (no need to write PromQL queries)
- Shareable dashboards (export/import JSON)
- Alerting integration
- Multiple data source support

---

## File Structure

```
sherlock-logs/
├── Vagrantfile                    # VM definitions
├── ansible/
│   ├── inventory.ini              # Ansible hosts
│   ├── site.yml                   # Main playbook
│   └── roles/
│       ├── monitoring/            # Monitoring role (Prometheus, Grafana)
│       │   ├── tasks/
│       │   │   └── main.yml       # Prometheus & Grafana installation
│       │   └── handlers/
│       │       └── main.yml       # Service restart handlers
│       ├── node_exporter/         # Node Exporter role
│       │   ├── tasks/
│       │   │   └── main.yml       # Node Exporter installation
│       │   └── handlers/
│       │       └── main.yml       # Service restart handlers
│       ├── cadvisor/              # cAdvisor role
│       │   ├── tasks/
│       │   │   └── main.yml       # cAdvisor Docker container setup
│       │   └── handlers/
│       │       └── main.yml       # Handlers (if needed)
│       ├── frontend_container/    # Frontend Flask app
│       │   └── files/app/
│       │       ├── app.py          # Flask app with Prometheus metrics
│       │       └── requirements.txt # Includes prometheus_client
│       ├── backend_container/     # Backend Flask app
│       │   └── files/app/
│       │       ├── app.py          # Flask app with Prometheus metrics
│       │       └── requirements.txt # Includes prometheus_client
│       └── app_deploy/            # Systemd-deployed Flask app
│           └── files/flask_app/
│               ├── app.py          # Flask app with Prometheus metrics
│               └── requirements.txt # Includes prometheus_client
├── PHASE1_TESTING.md              # Phase 1 testing guide
├── PHASE2_STEP23_TESTING.md      # cAdvisor testing guide
├── PHASE2_STEP24_TESTING.md      # Application metrics testing guide
├── PHASE3_STEP31_TESTING.md      # Grafana installation testing guide
├── DOCUMENTATION.md               # This file
└── sherlock-logs-roadmap.md      # Complete implementation roadmap
```

---

## Commands Reference

### VM Management
```bash
# Create all VMs
vagrant up

# Create specific VM
vagrant up monitoring-server-auto

# Provision all VMs
vagrant provision

# Provision specific VM
vagrant provision monitoring-server-auto

# Check VM status
vagrant status

# SSH into VM
vagrant ssh monitoring-server-auto
```

### Accessing Services

**Prometheus:**
- URL: http://192.168.56.25:9090
- Status: `curl http://192.168.56.25:9090/-/ready`
- Targets: http://192.168.56.25:9090/targets

**Grafana:**
- URL: http://192.168.56.25:3000
- Login: admin / admin
- Health: `curl http://192.168.56.25:3000/api/health`
- Data Sources: http://192.168.56.25:3000/connections/datasources

**Node Exporter (on any VM):**
- Metrics: `curl http://192.168.56.XX:9100/metrics`

**cAdvisor (on web/app VMs):**
- Metrics: `curl http://192.168.56.XX:8080/metrics`

**Flask Apps (on web/app VMs):**
- Metrics: `curl http://192.168.56.XX:5000/metrics`
- App: `curl http://192.168.56.XX:5000/`

### Testing Prometheus Queries

**From Grafana Explore:**
1. Go to http://192.168.56.25:3000
2. Click "Explore" (compass icon)
3. Select "Prometheus" data source
4. Switch to "Code" tab
5. Enter query: `up`
6. Click "Run query"

**From Prometheus UI:**
1. Go to http://192.168.56.25:9090
2. Click "Graph" tab
3. Enter query in the query box
4. Click "Execute"

**Example Queries:**
```promql
# Check if all targets are up
up

# CPU usage percentage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage percentage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Total HTTP requests
sum(flask_http_requests_total)

# Request rate (requests per second)
rate(flask_http_requests_total[5m])
```

### Manual Ansible Testing
```bash
# From lb-server-auto
vagrant ssh lb-server-auto
cd /vagrant/ansible

# Test specific role
ansible-playbook -i inventory.ini site.yml --limit monitoring \
  -e ansible_ssh_private_key_file=/home/vagrant/.ssh/id_ed25519

# Test connectivity
ansible monitoring -i inventory.ini -m ping \
  -e ansible_ssh_private_key_file=/home/vagrant/.ssh/id_ed25519
```

---

## Troubleshooting

### Monitoring VM Not Created
**Problem:** `vagrant up monitoring-server-auto` fails  
**Solution:** 
- Check VirtualBox is running
- Verify no other Vagrant process is running: `tasklist | findstr ruby`
- Try: `vagrant destroy monitoring-server-auto && vagrant up monitoring-server-auto`

### SSH Connection Fails
**Problem:** Can't SSH to monitoring VM  
**Solution:** 
- Run `vagrant provision lb-server-auto` to copy SSH keys
- Check VM is running: `vagrant status`
- Verify network: `vagrant ssh monitoring-server-auto` then `ip a`

### Ansible Can't Connect
**Problem:** Ansible fails with "UNREACHABLE"  
**Solution:** 
- Use explicit key override: `-e ansible_ssh_private_key_file=/home/vagrant/.ssh/id_ed25519`
- Check SSH from lb-server-auto: `ssh vagrant@192.168.56.25`
- Verify inventory.ini has correct IP and user

### Prometheus Not Scraping Targets
**Problem:** Targets show as DOWN in Prometheus UI  
**Solution:**
- Check target is accessible: `curl http://TARGET_IP:PORT/metrics`
- Verify firewall allows monitoring server: `sudo ufw status`
- Check Prometheus config: `cat /etc/prometheus/prometheus.yml`
- Restart Prometheus: `sudo systemctl restart prometheus`

### Grafana Can't Connect to Prometheus
**Problem:** Data source shows "Health: Error"  
**Solution:**
- Verify Prometheus is running: `sudo systemctl status prometheus`
- Test from Grafana VM: `curl http://localhost:9090/api/v1/status/config`
- Check data source config: `cat /etc/grafana/provisioning/datasources/prometheus.yml`
- Restart Grafana: `sudo systemctl restart grafana-server`

### Grafana Installation Fails (GPG Key Error)
**Problem:** `NO_PUBKEY 963FA27710458545` error  
**Solution:**
- This is now fixed by using .deb package installation
- If it still occurs, manually remove: `sudo rm /etc/apt/sources.list.d/grafana.list`
- Then re-run: `vagrant provision monitoring-server-auto`

### Network Issues
**Problem:** Can't access services from host machine  
**Solution:** 
- Verify IP in `Vagrantfile` matches `inventory.ini` (should be 192.168.56.25)
- Check firewall: `sudo ufw status` on monitoring VM
- Test from within VM first: `curl http://localhost:3000/api/health`
- Verify port forwarding in VirtualBox (if needed)

---

## Next Steps

With Phase 2 and Phase 3.1 complete, proceed to:

**Phase 3: Grafana Dashboards (Remaining Steps)**
- **Step 3.2:** Create VM Performance Dashboard
  - CPU usage, Memory utilization, Disk I/O, Network traffic
  - Filters by hostname
- **Step 3.3:** Create Docker Container Dashboard
  - Container health, CPU/memory usage, Restart counts
  - Filters by container name and host
- **Step 3.4:** Create Application Performance Dashboard
  - Response times, Error rates, Custom metrics
  - Filters by application/role

**Phase 4: ELK Stack Setup**
- Install Elasticsearch for log storage
- Install Logstash for log processing
- Install Filebeat on all VMs for log collection
- Install Kibana for log visualization
- Create Kibana dashboards

**Phase 5: Alerting**
- Configure Grafana alerts
- Set up VM, Docker, and application alerts
- Configure Elasticsearch health alerts

See `sherlock-logs-roadmap.md` for the complete implementation plan.

---

## Summary of Completed Work

### ✅ Phase 1: Infrastructure Setup
- Created monitoring VM (192.168.56.25)
- Configured network and SSH access
- Set up Ansible automation

### ✅ Phase 2: Prometheus Setup
- Installed Prometheus on monitoring VM
- Installed Node Exporter on all 6 VMs
- Installed cAdvisor on Docker-enabled VMs
- Converted Flask apps to Prometheus metrics format
- Configured Prometheus to scrape all targets

### ✅ Phase 3, Step 3.1: Grafana Installation
- Installed Grafana 12.3.0
- Configured Prometheus as data source
- Set up admin credentials
- Verified web UI and query functionality

### ✅ Phase 4, Step 4.6: Kibana Dashboards
- Created System Logs Dashboard (3 visualizations)
- Created Application Logs Dashboard (3 visualizations)
- Created Docker Logs Dashboard (3 visualizations)
- Automated index pattern creation

### ✅ Phase 5: Alerting Configuration

#### Phase 5.1: Grafana Alerts ✅
- Created 6 Grafana alert rules:
  - VM CPU High Alert (>80% for 5 minutes)
  - VM Disk Space Low Alert (<20% available)
  - VM Memory High Alert (>90% for 5 minutes)
  - Container Restart High Alert (>3 restarts in 15 minutes)
  - Container Memory High Alert (>80% of limit)
  - VM Unreachable Alert (Node Exporter down)
- All alerts configured with proper PromQL queries, conditions, labels, and evaluation behavior
- Alerts organized in "Infrastructure Alerts" folder
- Evaluation groups configured for proper alert timing

#### Phase 5.2: Elasticsearch Health Alert ✅
- Created Elasticsearch Cluster Health Alert
- Uses indirect monitoring via Node Exporter on monitoring server
- Query: `1 - up{job="node_exporter", instance=~".*192.168.56.25.*"}`
- Condition: Fires when monitoring server's Node Exporter is down (indicating Elasticsearch is likely down)
- Labels: `severity: critical`, `alertname: Elasticsearch_Health`
- Evaluation: Every 5 minutes, pending period 5 minutes

**Note:** This is a temporary solution. For production, consider adding an Elasticsearch exporter for direct health monitoring.

#### Automation ✅
- All 7 alerts are automatically created via Python script during Ansible provisioning
- Script uses Grafana's Provisioning API (`/api/v1/provisioning/alert-rules`) for automated setup
- Alerts are created in the "Infrastructure Alerts" folder (created automatically if needed)
- Script handles existing alerts gracefully (skips if already exists)
- **Tested and confirmed working** - All alerts created successfully during provisioning
- No manual intervention required - fully automated setup

### ⏳ Remaining Work
- Phase 3: Dashboard creation (Steps 3.2-3.4)
- Phase 4: ELK Stack setup (Steps 4.1-4.5 complete, 4.6 complete)
- Phase 5: Alerting configuration (5.1 and 5.2 complete)
- Phase 6: Automation integration
- Phase 7: Testing & documentation

---

*Last Updated: Phase 5 Complete - All 7 Grafana Alerts Automated and Tested Successfully*

