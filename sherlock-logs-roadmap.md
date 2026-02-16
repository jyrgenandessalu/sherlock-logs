# 🕵️ Sherlock Logs - Implementation Roadmap

## Project Overview
Implement a comprehensive monitoring and logging system using Prometheus + Grafana for metrics and ELK stack for logs. This roadmap focuses on **mandatory requirements only**, broken down into manageable steps.

---

## 📋 Current Infrastructure
- **VMs**: lb (192.168.56.20), web1/web2 (192.168.56.21-22), app (192.168.56.23), backup (192.168.56.24)
- **New VM needed**: monitoring (192.168.56.25)
- **Current apps**: Flask apps with `/metrics` endpoint (JSON format - needs conversion to Prometheus)
- **Automation**: Ansible playbooks, Jenkins CI/CD

---

## 🗺️ Implementation Phases

### **Phase 1: Infrastructure Setup** ⚙️
**Goal**: Create the monitoring/logging VM and basic infrastructure

#### Step 1.1: Add Monitoring VM to Infrastructure ✅ COMPLETE
- [x] Update `Vagrantfile` to add `monitoring-server-auto` (192.168.56.25)
- [x] Update `ansible/inventory.ini` to add `[monitoring]` group
- [x] Update `ansible/site.yml` to include monitoring role
- [x] Create basic Ansible role structure: `ansible/roles/monitoring/`
- [x] Test VM creation: `vagrant up monitoring-server-auto`

**Estimated Time**: 30-45 minutes  
**Difficulty**: Easy  
**Status**: ✅ Complete - All tests passed. See `DOCUMENTATION.md` for details.

---

### **Phase 2: Prometheus Setup** 📊
**Goal**: Set up Prometheus to collect metrics from all sources

#### Step 2.1: Install Prometheus on Monitoring VM ✅ COMPLETE
- [x] Create Ansible tasks to install Prometheus
- [x] Configure Prometheus as systemd service
- [x] Set up basic Prometheus configuration file
- [x] Open firewall port 9090
- [x] Verify Prometheus is accessible at http://192.168.56.25:9090

**Estimated Time**: 1-2 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - Prometheus installed and running. Web UI accessible at http://192.168.56.25:9090

#### Step 2.2: Install Node Exporter on All VMs ✅ COMPLETE
- [x] Create Ansible role/tasks for Node Exporter
- [x] Install Node Exporter on all VMs (lb, web1, web2, app, backup, monitoring)
- [x] Configure Node Exporter as systemd service
- [x] Open firewall port 9100 on all VMs
- [x] Update Prometheus config to scrape Node Exporter from all VMs
- [x] Verify metrics are being collected

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - Node Exporter installed on all 6 VMs. All targets UP in Prometheus. System metrics (CPU, memory, disk, network) successfully being collected and queryable.

#### Step 2.3: Install cAdvisor on All VMs ✅ COMPLETE
- [x] Create Ansible tasks to install cAdvisor (Docker container)
- [x] Configure cAdvisor on all VMs with Docker
- [x] Open firewall port 8080 (or custom port) for cAdvisor
- [x] Update Prometheus config to scrape cAdvisor from all VMs
- [x] Verify container metrics are being collected

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - cAdvisor installed on web1, web2, and app VMs. All containers healthy. Prometheus successfully scraping container metrics (CPU, memory, network, filesystem) for Flask containers and system containers.-Hard (Docker integration)

#### Step 2.4: Convert Application Metrics to Prometheus Format
- [x] Install `prometheus_client` Python library in app requirements
- [x] Rewrite frontend app `/metrics` endpoint to Prometheus format
- [x] Rewrite backend app `/metrics` endpoint to Prometheus format
- [x] Add at least 1 custom application metric (e.g., request count, response time)
- [x] Update Prometheus config to scrape application metrics
- [x] Verify application metrics appear in Prometheus

**Estimated Time**: 3-4 hours  
**Difficulty**: Medium (requires understanding Prometheus format)

---

### **Phase 3: Grafana Setup** 📈
**Goal**: Visualize metrics from Prometheus

#### Step 3.1: Install and Configure Grafana ✅ COMPLETE
- [x] Create Ansible tasks to install Grafana
- [x] Configure Grafana as systemd service
- [x] Open firewall port 3000
- [x] Set up initial admin credentials
- [x] Configure Prometheus as data source in Grafana
- [x] Verify Grafana is accessible at http://192.168.56.25:3000

**Estimated Time**: 1-2 hours  
**Difficulty**: Easy-Medium  
**Status**: ✅ Complete - Grafana 12.3.0 installed and running. Prometheus data source configured. Web UI accessible at http://192.168.56.25:3000 (admin/admin)

#### Step 3.2: Create VM Performance Dashboard ✅ COMPLETE
- [x] Create dashboard with panels for:
  - CPU usage (from Node Exporter)
  - Memory utilization (from Node Exporter)
  - Disk I/O (from Node Exporter)
  - Network traffic (from Node Exporter)
- [x] Add labels/filters by hostname
- [x] Export dashboard JSON for version control

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium (learning Grafana query editor)  
**Status**: ✅ Complete - VM Performance Dashboard created with 8 panels (CPU, Memory, Disk I/O, Network, Disk Space, Load Average). Dashboard automatically provisioned and accessible in Grafana.

#### Step 3.3: Create Docker Container Dashboard ✅ COMPLETE
- [x] Create dashboard with panels for:
  - Container health status
  - CPU usage per container (from cAdvisor)
  - Memory usage per container (from cAdvisor)
  - Restart counts (from cAdvisor)
- [x] Add labels/filters by container name and host
- [x] Export dashboard JSON

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - Docker Container Dashboard created with 7 panels (CPU, Memory, Memory %, Network, Restart Count, Status Table). Dashboard automatically provisioned and accessible in Grafana.

#### Step 3.4: Create Application Performance Dashboard ✅ COMPLETE
- [x] Create dashboard with panels for:
  - Response times (from application metrics)
  - Error rates (from application metrics)
  - 1 custom application metric (e.g., request count)
- [x] Add labels/filters by application/role
- [x] Export dashboard JSON

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - Application Performance Dashboard created with 8 panels (Request Rate, Response Times p50/p95/p99, Error Rate, Total Requests, CPU/Memory Usage, Status Distribution, Request Rate by Endpoint). Dashboard automatically provisioned and accessible in Grafana.

---

### **Phase 4: ELK Stack Setup** 📝
**Goal**: Set up centralized logging

#### Step 4.1: Install Elasticsearch ✅ COMPLETE
- [x] Create Ansible tasks to install Elasticsearch
- [x] Configure Elasticsearch (heap size, network settings)
- [x] Configure Elasticsearch as systemd service
- [x] Open firewall port 9200
- [x] Verify Elasticsearch is running and accessible

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium (configuration can be tricky)  
**Status**: ✅ Complete - Elasticsearch 8.19.8 installed and running. Cluster status: green. Single-node mode configured. Accessible at http://192.168.56.25:9200

#### Step 4.2: Install Logstash
- [ ] Create Ansible tasks to install Logstash
- [ ] Create Logstash configuration for:
  - Receiving logs from Filebeat
  - Parsing different log formats
  - Outputting to Elasticsearch
- [ ] Configure Logstash as systemd service
- [ ] Open firewall port 5044 (Beats input)
- [ ] Verify Logstash is processing logs

**Estimated Time**: 3-4 hours  
**Difficulty**: Medium-Hard (log parsing can be complex)

#### Step 4.3: Install Filebeat on All VMs ✅ COMPLETE
- [x] Create Ansible role/tasks for Filebeat
- [x] Install Filebeat on all VMs
- [x] Configure Filebeat to collect:
  - System logs (syslog, auth.log, kern.log)
  - Application logs (Flask app logs - paths configured)
  - Docker container logs (stdout/stderr)
- [x] Configure Filebeat to send to Logstash (192.168.56.25:5044)
- [x] Add log type fields (system/application/docker) for filtering
- [x] Configure multiline parsing for structured logs

**Estimated Time**: 3-4 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - Filebeat installed on all 6 VMs. System logs are being collected and forwarded to Logstash. Application and Docker log paths are configured and will collect logs once applications start writing to those locations.

#### Step 4.4: Configure Application Logging ✅ COMPLETE
- [x] Add logging framework to Flask apps (Python logging)
- [x] Configure apps to write structured JSON logs to files
- [x] Add structured logging with appropriate log levels (INFO, ERROR, DEBUG)
- [x] Configure log file paths that Filebeat monitors
- [x] Add volume mounts for containerized apps to write logs to host
- [x] Log important events: HTTP requests, errors, metrics access, server start

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium  
**Status**: ✅ Complete - All Flask apps (frontend, backend, app_deploy) now write structured JSON logs. Logs are written to `/var/log/flask_apps/{role}.log` for containers and `/home/devops/flask_app/app.log` for systemd service. Filebeat is configured to collect these logs.

#### Step 4.5: Install and Configure Kibana
- [ ] Create Ansible tasks to install Kibana
- [ ] Configure Kibana to connect to Elasticsearch
- [ ] Configure Kibana as systemd service
- [ ] Open firewall port 5601
- [ ] Verify Kibana is accessible at http://192.168.56.25:5601

**Estimated Time**: 1-2 hours  
**Difficulty**: Easy

#### Step 4.6: Create Kibana Dashboards
- [ ] Create System Logs Dashboard:
  - System logs from all VMs (syslog, dmesg)
  - Filters by hostname, log level, timestamp
- [ ] Create Application Logs Dashboard:
  - Application-specific logs (error logs, access logs)
  - Filters by application, log level
- [ ] Create Docker Logs Dashboard:
  - Docker container logs (stdout, stderr)
  - Filters by container name, host
- [ ] Export dashboard configurations

**Estimated Time**: 4-5 hours  
**Difficulty**: Medium (learning Kibana query syntax)

---

### **Phase 5: Alerting** 🚨
**Goal**: Set up alerts for critical issues

#### Step 5.1: Configure Grafana Alerts
- [ ] Set up alerting in Grafana (configure notification channels)
- [ ] Create VM CPU alert: >80% for 5 minutes
- [ ] Create VM Disk alert: <20% available
- [ ] Create VM Memory alert: >90% for 5 minutes
- [ ] Create Container Restart alert: >3 restarts in 15 minutes
- [ ] Create Container Memory alert: >80% of limit
- [ ] Create VM Unreachable alert (using Prometheus up metric)
- [ ] Test each alert with simulation commands

**Estimated Time**: 4-5 hours  
**Difficulty**: Medium (alert configuration and testing)

#### Step 5.2: Configure Elasticsearch Health Alert
- [ ] Create alert for Elasticsearch cluster status (yellow/red)
- [ ] Configure alert to trigger on cluster health changes
- [ ] Test alert by stopping Elasticsearch node

**Estimated Time**: 1-2 hours  
**Difficulty**: Medium

---

### **Phase 6: Automation Integration** 🤖
**Goal**: Integrate monitoring/logging into existing automation

#### Step 6.1: Update Ansible Playbooks
- [ ] Ensure all monitoring/logging setup is in Ansible roles
- [ ] Test full provisioning: `vagrant destroy -f && vagrant up`
- [ ] Verify all services start automatically
- [ ] Document any manual steps (if any)

**Estimated Time**: 2-3 hours  
**Difficulty**: Easy-Medium

#### Step 6.2: Update CI/CD Pipeline
- [ ] Update Jenkinsfile to deploy monitoring/logging agents
- [ ] Ensure Filebeat/Node Exporter are installed on new instances
- [ ] Test CI/CD pipeline end-to-end
- [ ] Verify metrics and logs appear after deployment

**Estimated Time**: 2-3 hours  
**Difficulty**: Medium

---

### **Phase 7: Testing & Documentation** 📚
**Goal**: Verify everything works and document it

#### Step 7.1: End-to-End Testing
- [ ] Test all dashboards display data correctly
- [ ] Test all alerts trigger appropriately
- [ ] Test log collection from all sources
- [ ] Test metric collection from all sources
- [ ] Verify historical data retention

**Estimated Time**: 3-4 hours  
**Difficulty**: Medium

#### Step 7.2: Create README
- [ ] Project overview
- [ ] Architecture diagram (text or ASCII)
- [ ] Setup and installation instructions
- [ ] Usage guide (how to access dashboards, view logs)
- [ ] Alert configuration details
- [ ] Troubleshooting section

**Estimated Time**: 2-3 hours  
**Difficulty**: Easy

---


### Critical Path:
1. Infrastructure Setup (Phase 1)
2. Prometheus + Node Exporter (Phase 2.1-2.2)
3. Application Metrics Conversion (Phase 2.4)
4. Grafana + Dashboards (Phase 3)
5. ELK Stack (Phase 4)
6. Alerting (Phase 5)
7. Automation (Phase 6)

---


- **Extras** (advanced alerting, external notifications) can be estimated after mandatory requirements are complete
- Each step should be tested before moving to the next
- Keep all configuration files in version control
- Document any issues encountered and solutions

---

## 🔗 Useful Resources

- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- ELK Stack: https://www.elastic.co/guide/
- Prometheus Client Libraries: https://prometheus.io/docs/instrumenting/clientlibs/
- Node Exporter: https://github.com/prometheus/node_exporter
- cAdvisor: https://github.com/google/cadvisor

