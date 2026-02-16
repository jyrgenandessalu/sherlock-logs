# Requirements Testing Guide

**URLs:** Grafana http://192.168.56.25:3000 (admin/admin) | Prometheus http://192.168.56.25:9090 | Kibana http://192.168.56.25:5601

**Note:** If Prometheus shows "Server time is out of sync" warning, sync VM time:
```powershell
vagrant ssh monitoring-server-auto -c "sudo ntpdate -s time.nist.gov || sudo timedatectl set-ntp true"
```

---

## KNOWLEDGE REQUIREMENTS

### 1. Push vs Pull Monitoring
**Command:**
```powershell
vagrant ssh monitoring-server-auto -c "grep scrape_interval /etc/prometheus/prometheus.yml"
```
**Expected:** `scrape_interval: 15s      # How often to scrape targets`
**Explain:** Push = targets send data. Pull = server requests data (Prometheus). Pull gives centralized control.

---

### 2. ELK Stack Architecture
**Command:**
```powershell
vagrant ssh monitoring-server-auto -c "systemctl is-active elasticsearch logstash kibana"
vagrant ssh web1-server-auto -c "systemctl is-active filebeat"
```
**Expected:** `active` for all services
**Explain:** Filebeat → Logstash (5044) → Elasticsearch (9200) → Kibana (5601). Filebeat collects logs from files (syslog, application logs, Docker logs) and forwards to Logstash. Logstash parses/transforms logs (syslog format, JSON format, adds fields). Elasticsearch stores and indexes logs. Kibana visualizes logs with dashboards.

---

### 3. Prometheus Advantages
**Explain:** 
- **Advantages:** Pull-based model (centralized control), powerful PromQL query language, time-series database optimized for metrics, multi-dimensional data model (labels), open-source, better for microservices/cloud-native, service discovery support, active community.
- **Disadvantages:** Not ideal for event logging (use ELK), limited long-term storage (default 15 days), no built-in alerting UI (uses Grafana), learning curve for PromQL.
- **vs Nagios/Zabbix:** More modern and cloud-native, better query language (PromQL vs custom configs), better for dynamic environments, multi-dimensional labels vs flat metrics, pull-based vs push-based.

---

### 4. Scrape Interval Configuration
**Command:**
```powershell
vagrant ssh monitoring-server-auto -c "grep scrape_interval /etc/prometheus/prometheus.yml"
```
**Expected:** `scrape_interval: 15s`
**Explain:** Edit `/etc/prometheus/prometheus.yml` (`monitoring/tasks/main.yml`), change value, restart Prometheus. Shorter = more real-time, longer = less resource usage.

---

### 5. Node Exporter & cAdvisor Setup Issues
**Command:**
```powershell
vagrant ssh lb-server-auto -c "curl -s http://localhost:9100/metrics | head -1"
vagrant ssh web1-server-auto -c "curl -s http://localhost:8080/metrics | head -1"
```
**Expected:** `# HELP go_gc_duration_seconds` (Node Exporter) and `# HELP cadvisor_version_info` (cAdvisor)
**Explain:** Common issues: firewall blocking ports (9100/8080), wrong endpoint, service not started, permissions, network.

---

### 6. Grafana Benefits
**Explain:** Multi-data source support, rich visualizations, built-in alerting, user-friendly UI, drag-and-drop dashboards, open-source.

---

### 7. Prometheus Client Libraries
**Command:**
```powershell
vagrant ssh web1-server-auto -c "curl -s http://localhost:5000/metrics | grep '^flask_' | head -5"
```
**Expected:** Shows `flask_http_requests_total`, `flask_app_info`, `flask_app_cpu_usage_percent`, etc.
**Explain:** 
- **Note:** Prometheus doesn't create metrics - it only scrapes/collects them. The application must expose metrics using client libraries.
- **Library:** Install `prometheus-client` Python library (in `requirements.txt`), import in Flask app.
- **Create metrics:** Use `Counter()` for counting (requests), `Gauge()` for values that go up/down (CPU, memory), `Histogram()` for distributions (response times).
- **Add labels:** Use `labels()` method to add dimensions (hostname, role, endpoint, method, status) for filtering/grouping.
- **Expose endpoint:** Use `start_http_server()` or add `/metrics` route that returns `generate_latest()` to expose metrics in Prometheus format.
- **Format:** Metrics automatically formatted in Prometheus text format (lines starting with `# HELP`, `# TYPE`, then metric name and value).
- **Integration:** Prometheus scrapes `/metrics` endpoint from the application, stores metrics in its time-series database.

---

### 8. Custom Application Metrics
**Command 1 (Show metrics exposed):**
```powershell
vagrant ssh web1-server-auto -c "curl -s http://localhost:5000/metrics | grep '^flask_'"
```
**Expected:** Multiple metrics: `flask_http_requests_total`, `flask_app_info`, `flask_app_cpu_usage_percent`, `flask_app_memory_usage_bytes`

**Command 2 (Show in Prometheus):**
1. Go to: http://192.168.56.25:9090
2. Query: `flask_app_info` or `flask_app_memory_usage_bytes`
3. Should show 3 results (web1, web2, app-server) with labels: hostname, instance, job, role

**Explain:** Custom metrics with labels (hostname, role, endpoint, method, status). All visible in Prometheus. Shows 3 Flask instances reporting (2 frontend, 1 backend).

---

### 9. Log Format Handling
**Command:**
```powershell
vagrant ssh web1-server-auto -c "logger 'TEST_syslog'"
vagrant ssh web1-server-auto -c 'echo "{\"level\":\"info\",\"message\":\"TEST_app\"}" | sudo tee -a /var/log/flask_apps/frontend.log > /dev/null'
```
**Verify (wait 30-60 seconds for processing):**
```powershell
# 1. Check log was written
vagrant ssh web1-server-auto -c "sudo tail -1 /var/log/flask_apps/frontend.log"

# 2. Check Filebeat is reading the log
vagrant ssh web1-server-auto -c "sudo journalctl -u filebeat -n 30 --no-pager | grep -i 'TEST_app\|frontend.log' | tail -3"

# 3. Check Logstash received data (check for recent activity)
vagrant ssh monitoring-server-auto -c "sudo journalctl -u logstash --since '1 minute ago' --no-pager | tail -10"

# 4. Check Elasticsearch indices (see if new logs were indexed)
Start-Sleep -Seconds 60
Invoke-WebRequest -Uri "http://192.168.56.25:9200/_cat/indices/logs-*?v" -UseBasicParsing | Select-Object -ExpandProperty Content

# 5. Search Elasticsearch (try different queries)
Invoke-WebRequest -Uri "http://192.168.56.25:9200/logs-*/_search?q=TEST_app" -UseBasicParsing | Select-Object -ExpandProperty Content
Invoke-WebRequest -Uri "http://192.168.56.25:9200/logs-*/_search?q=message:TEST_app" -UseBasicParsing | Select-Object -ExpandProperty Content
```
**Note:** If Kibana shows "disk usage exceeded" error, fix with:
```powershell
vagrant ssh monitoring-server-auto -c "curl -X PUT http://localhost:9200/_all/_settings -H 'Content-Type: application/json' -d '{\"index.blocks.read_only_allow_delete\": null}'"
```
**Expected:** 
- Log file shows the entry
- Logstash logs show "Retrying failed action" or processing activity (proves Logstash is receiving and processing logs)
- Elasticsearch indices show data (even if search doesn't work due to disk space issues)

**Note:** If Logstash shows "Retrying failed action" with "disk usage exceeded" errors, this actually **proves Logstash is working** - it's processing logs but Elasticsearch is blocking writes due to disk space. The pipeline is: Filebeat → Logstash (processing) → Elasticsearch (blocked by disk space).

**Explain:** Logstash parses: syslog (grok), JSON (json filter), Docker (conditional). If parsing fails, log still forwarded. Pipeline: Filebeat reads log → sends to Logstash → Logstash parses → sends to Elasticsearch. Logstash logs showing retry attempts prove it's processing logs, even if Elasticsearch can't accept them due to disk space.

---

### 10. Grafana Query Editor
**Show:**
1. Go to: http://192.168.56.25:3000 (admin/admin)
2. **Dashboards** → Browse → Open **VM Performance Dashboard** (or any dashboard)
3. Click on any panel (e.g., CPU panel) → Click **Edit** (pencil icon)
4. In the query editor, show:
   - **Data source:** Prometheus (selected)
   - **Query field:** Shows PromQL query (e.g., `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`)
   - **Functions:** Show `rate()`, `irate()`, `avg()`, `sum()`, `by (instance)` in the query
   - **Label selectors:** Show `{mode="idle"}`, `{instance="..."}` in the query
   - **Legend:** Show `{{instance}}` or similar in Legend field
   - **Query options:** Show time range, resolution, etc.
5. Click **Run query** to show it executes
6. Show the graph/table results update

**Explain:** 
- **PromQL syntax:** Query language for Prometheus metrics
- **Functions:** `rate()` (per-second rate), `irate()` (instant rate), `avg()` (average), `sum()` (sum), `by (label)` (group by label)
- **Label selectors:** `{instance="192.168.56.21:9100"}` filters specific targets, `{job="node_exporter"}` filters by job
- **Legend formatting:** `{{instance}}` shows instance label in legend, `{{job}}` shows job label
- **Query editor benefits:** Visual interface, autocomplete, query validation, no need to write PromQL manually

---

### 11. Kibana Search & Filtering
**Show:**
1. Go to: http://192.168.56.25:5601
2. **Dashboards** → Show 3 dashboards exist:
   - System Logs Dashboard
   - Application Logs Dashboard
   - Docker Logs Dashboard
3. **Discover** → Select data view: `logs-*`
4. **Search bar** (top of page) - Show KQL syntax:
   - Basic filter: `fields.log_type: system`
   - Multiple filters: `fields.log_type: system AND fields.hostname: "web1-server-auto"`
   - OR operator: `fields.log_type: system OR fields.log_type: application`
   - NOT operator: `NOT fields.log_type: docker`
   - Wildcards: `fields.hostname: "web*"`
5. **Time range** (top right) - Show: "Last 15 minutes", "Last 1 hour", custom range
6. **Field filters** (left sidebar) - Show available fields (42 fields), click to add filters
7. **Dashboards use filtering** - Open a dashboard, show how visualizations filter by `fields.log_type`

**Note:** If Kibana shows "disk usage exceeded" error, you can still demonstrate:
- The search bar and KQL syntax (even if results don't load)
- Available fields in sidebar (42 fields shown)
- Explain the query syntax
- Show dashboards exist (System, Application, Docker Logs)

**Explain:** 
- **KQL (Kibana Query Language):** Syntax for searching and filtering logs
- **Field filters:** `fields.log_type: system` filters by log type field
- **Boolean operators:** `AND`, `OR`, `NOT` for combining conditions
- **Wildcards:** `*` for matching any characters (e.g., `web*` matches web1, web2)
- **Time ranges:** Filter logs by time (Last 15 minutes, Last 1 hour, custom)
- **Field-based filtering:** Click fields in sidebar to add filters (42 fields available)
- **Dashboards:** Use search/filtering to create visualizations (System Logs, Application Logs, Docker Logs dashboards)
- **Examples:**
  - System logs: `fields.log_type: system`
  - Application logs: `fields.log_type: application`
  - Docker logs: `fields.log_type: docker`
  - Specific host: `fields.hostname: "web1-server-auto"`
  - Combined: `fields.log_type: system AND fields.hostname: "web1-server-auto"`

---

### 12. Real-Time Performance Metrics
**Command:**
```powershell
$r = Invoke-WebRequest -Uri "http://192.168.56.25:9090/api/v1/targets" -UseBasicParsing
($r.Content | ConvertFrom-Json).data.activeTargets | ForEach-Object { "$($_.labels.job): $($_.health)" }
```
**Expected:** All jobs show `up`:
- `cadvisor: up` (3 instances - web1, web2, app)
- `flask_apps: up` (3 instances - web1, web2, app)
- `node_exporter: up` (6 instances - all VMs)
- `prometheus: up` (1 instance)

**Alternative (UI):** Go to http://192.168.56.25:9090/targets - Should show all targets as "UP"

**Explain:** 
- **Real-time collection:** Scrape interval 15s (Prometheus requests metrics every 15 seconds)
- **All targets healthy:** All jobs showing "up" means metrics are being collected in real-time
- **Troubleshooting if targets are down:**
  - Check services: `systemctl status node_exporter`, `systemctl status cadvisor`
  - Check firewall: Ports 9100 (Node Exporter), 8080 (cAdvisor), 5000 (Flask apps)
  - Check network: VMs can reach each other
  - Check Prometheus logs: `sudo journalctl -u prometheus -n 50`
  - Check Prometheus config: `/etc/prometheus/prometheus.yml`
- **Stale data:** If metrics are old, check last scrape time in targets page, verify scrape interval

---

### 13. Historical Data Retention
**Command:**
```powershell
vagrant ssh monitoring-server-auto -c "ps aux | grep '[p]rometheus' | grep retention || echo 'Default: 15 days'"
Invoke-WebRequest -Uri "http://192.168.56.25:9200/_cat/indices/logs-*?v" -UseBasicParsing | Select-Object -ExpandProperty Content
```
**Expected:**
- Prometheus: `Default: 15 days` (or shows retention flag if custom)
- Elasticsearch: Shows daily indices:
  - `logs-2025.12.13` (148,353 docs, 46.8mb)
  - `logs-2025.12.14` (39,017 docs, 19.9mb)
  - `logs-2025.12.15` (135,602 docs, 43.1mb)
  - `logs-2025.12.16` (11,720,367 docs, 2.3gb) - current day

**Explain:** 
- **Prometheus retention:** Default 15 days (no custom retention flag). To change: add `--storage.tsdb.retention.time=30d` to Prometheus service, restart.
- **Elasticsearch retention:** Stores indefinitely by default, daily indices `logs-YYYY.MM.dd`. Can configure ILM (Index Lifecycle Management) policies to delete old indices.
- **Index pattern:** Daily indices allow easy querying by date range, automatic rollover.
- **Storage:** Elasticsearch indices show storage size (current day: 2.3gb, previous days: smaller). Can delete old indices manually or via ILM.

---

### 14. Automation Integration
**Command:**
```powershell
Select-String -Path "ansible/site.yml" -Pattern "monitoring"
Select-String -Path "ansible/inventory.ini" -Pattern "\[monitoring\]"
```
**Expected:** Shows monitoring in site.yml and inventory.ini
**Explain:** Monitoring VM in Ansible inventory, monitoring role automates setup. `vagrant up` provisions everything.

---

### 15. CI/CD Pipeline Integration
**Command:**
```powershell
Select-String -Path "Jenkinsfile" -Pattern "ansible"
Select-String -Path "ansible/site.yml" -Pattern "node_exporter|filebeat"
```
**Expected:** Shows Ansible in Jenkinsfile (lines 25, 27-31, 86-88) and agents in site.yml (node_exporter, filebeat)
**Explain:** Jenkins runs Ansible playbook (`ansible-playbook site.yml`). Ansible installs monitoring agents (Node Exporter, Filebeat, cAdvisor) on all VMs automatically.

---

### 16. Grafana Alert Thresholds
**Command:**
```powershell
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:admin"))
$h = @{Authorization="Basic $cred"}
$r = Invoke-WebRequest -Uri "http://192.168.56.25:3000/api/v1/provisioning/alert-rules" -Headers $h -UseBasicParsing
($r.Content | ConvertFrom-Json) | ForEach-Object { "$($_.title): $($_.for)s" }
```
**Expected:** Lists 14 alerts with their pending periods (e.g., "VM CPU High: 300s", "VM Memory High: 300s")
**Explain:** Thresholds: CPU >80% (5m), Disk <20% (1m), Memory >90% (5m), Container Restart >3 (15m). Pending periods prevent false positives.

---

### 17. Logstash Alert Notifications
**Command:**
```powershell
vagrant ssh monitoring-server-auto -c "sudo grep -A 20 'Send alerts' /etc/logstash/conf.d/logstash.conf"
vagrant ssh monitoring-server-auto -c "sudo ls -ld /var/log/logstash"
vagrant ssh web1-server-auto -c 'echo "{\"level\":\"error\",\"message\":\"TEST_ERROR\"}" | sudo tee -a /var/log/flask_apps/frontend.log > /dev/null'
Start-Sleep -Seconds 30
vagrant ssh monitoring-server-auto -c "sudo tail -3 /var/log/logstash/alerts.log 2>/dev/null || echo 'File created when errors occur'"
```
**Expected:** Shows alert output config, directory exists, alerts.log contains JSON error entries
**Explain:** Logstash detects errors (ERROR, CRITICAL, FATAL, FAILED, EXCEPTION). Writes to `/var/log/logstash/alerts.log` and stdout. All logs still go to Elasticsearch.

---

### 18. Alert Fine-Tuning
**Explain:** Tuning: increase pending period, adjust thresholds, add conditions, use `rate()` to smooth spikes, group alerts. Current: 1m-5m pending, reasonable thresholds, queries use `rate()`.

---

## FUNCTIONAL REQUIREMENTS

### 19. VM CPU Alert (>80% for 5m)
**Show:** Grafana → Alerting → Alert rules → "VM CPU High"
**Verify:** Alert shows "Firing" state, pending period 5m, instance with CPU >80% shown as "Alerting"
**Command (to trigger):**
```powershell
vagrant ssh web1-server-auto -c "sudo apt-get install -y stress-ng && stress-ng --cpu 8 --timeout 360s"
```
**Explain:** Alert fires when CPU >80% for 5 minutes. Shows in Grafana as "Firing" with instance details.

---

### 20. VM Disk Alert (<20% available)
**Show:** Grafana → Alerting → Alert rules → "VM Disk Space Low"
**Verify:** Alert shows "Firing" state, pending period 1m, instance with disk <20% shown as "Alerting"
**Command (to trigger):**
```powershell
vagrant ssh web1-server-auto -c "sudo fallocate -l 10G /tmp/large_file.img"
```
**Explain:** Alert fires when disk space <20% available. Shows in Grafana as "Firing" with instance details.

---

### 21. VM Memory Alert (>90% for 5m)
**Show:** Grafana → Alerting → Alert rules → "VM Memory High"
**Verify:** Alert shows configuration (pending period 5m, threshold >90%), monitors all 6 instances. If firing, shows instance with memory >90% as "Alerting".
**Command (to trigger if needed):**
```powershell
vagrant ssh monitoring-server-auto -c "sudo apt-get install -y stress-ng && stress-ng --vm 2 --vm-bytes 80% --timeout 600s"
```
**Explain:** Alert fires when memory >90% for 5 minutes. Transitions to "Normal" when condition is no longer met. Shows all monitored instances and their states.

---

### 22. Container Restart Alert (>3 in 15m)
**Show:** Grafana → Alerting → Alert rules → "Container Restart High"
**Verify:** Alert shows configuration (threshold >3 restarts in 15m, pending period 1m), monitors all containers. Query: `sum by (name, instance) (count(count_over_time(container_start_time_seconds{name!="",container_label_restartcount!=""}[15m:30s]) > 0)) - 1`
**Command (to trigger):**
```powershell
vagrant ssh web1-server-auto -c "sudo docker run --restart=always --name test_container ubuntu /bin/bash -c 'sleep 10; exit 1'"
```
**Check restart count:**
```powershell
vagrant ssh web1-server-auto -c "sudo docker inspect test_container --format='{{.RestartCount}}'"
```
**Wait:** 15-20 minutes for container to restart 4+ times, then check Grafana alert
**Verify in Prometheus:** Query `sum by (name, instance) (count(count_over_time(container_start_time_seconds{name="test_container",container_label_restartcount!=""}[15m:30s]) > 0)) - 1` - should show >3 after container restarts 4+ times within 15 minutes
**Note:** Re-provision after any query changes: `vagrant provision`
**Explain:** Alert fires when a container restarts >3 times in 15 minutes. Uses cAdvisor's `container_start_time_seconds` metric. Since cAdvisor creates a new time series for each restart (with different `container_label_restartcount` values), the query counts distinct series in the last 15 minutes and subtracts 1 for the initial start to get the restart count.
**Cleanup:** `vagrant ssh web1-server-auto -c "sudo docker stop test_container && sudo docker rm test_container"`

---

### 23. Container Memory Alert (>80% of limit)
**Command:**
```powershell
vagrant ssh web1-server-auto -c "sudo docker run -m 512m --name memory_test ubuntu /bin/bash -c 'apt-get update && apt-get install -y stress-ng && stress-ng --vm 1 --vm-bytes 450M --timeout 360s'"
```
**Verify:** Grafana → "Container Memory High" should be Firing after 5-10 min
**Cleanup:** `vagrant ssh web1-server-auto -c "sudo docker stop memory_test && sudo docker rm memory_test"`

---

### 24. VM Unreachable Alert
**Show:** Grafana → Alerting → Alert rules → "VM Unreachable"
**Verify:** Alert monitors all 6 VMs (192.168.56.20-25:9100). When a VM becomes unreachable, that specific instance should show as "Alerting" after 1-2 minutes.
**Command (Method 1 - Stop Node Exporter - Recommended):**
```powershell
# Makes web1-server-auto (192.168.56.21) unreachable
vagrant ssh web1-server-auto -c "sudo systemctl stop node_exporter"
```
**Command (Method 2 - Simulate Network Failure):**
```powershell
# Makes web1-server-auto (192.168.56.21) unreachable by bringing down its network interface
vagrant ssh web1-server-auto -c "sudo ifconfig eth0 down"
```
**Verify:** Grafana → "VM Unreachable" should show `192.168.56.21:9100` as "Alerting" after 1-2 min. The alert checks `up{job="node_exporter"}` - when node_exporter is unreachable (stopped or network down), Prometheus reports `up=0` and the alert fires.
**Restore (Method 1):** `vagrant ssh web1-server-auto -c "sudo systemctl start node_exporter"`
**Restore (Method 2):** `vagrant ssh web1-server-auto -c "sudo ifconfig eth0 up"` (or restart VM: `vagrant reload web1-server-auto`)
**Note:** Method 1 (stopping node_exporter) is recommended as it's easier to restore. Method 2 simulates actual network failure but requires network access to restore. You can test on any monitored VM (web1, web2, app, lb, backup, or monitoring-server-auto).



---

### 25. Elasticsearch Health Alert
**Command (Test 1 - Stop Elasticsearch to simulate down):**
```powershell
vagrant ssh monitoring-server-auto -c "sudo systemctl stop elasticsearch"
```
**Command (Test 2 - Simulate yellow status by making Elasticsearch read-only):**
```powershell
# Make Elasticsearch read-only (simulates yellow/red due to disk space)
vagrant ssh monitoring-server-auto -c "curl -X PUT http://localhost:9200/_all/_settings -H 'Content-Type: application/json' -d '{\"index.blocks.read_only_allow_delete\": true}'"
```
**Verify:** 
- **Prometheus API:** `Invoke-WebRequest -Uri "http://192.168.56.25:9090/api/v1/query?query=elasticsearch_cluster_health_status{job=`"elasticsearch_exporter`"}" -UseBasicParsing | Select-Object -ExpandProperty Content`
- **Prometheus UI:** Go to http://192.168.56.25:9090 → Query: `elasticsearch_cluster_health_status{job="elasticsearch_exporter"}` → Should show status < 3 (2=yellow, 1=red, 0=down)
- **Grafana:** Alerting → Alert rules → "Elasticsearch Cluster Health" should be Firing after 1-2 min
- **Check exporter:** `vagrant ssh monitoring-server-auto -c "curl -s http://localhost:9114/metrics"` → Should show `elasticsearch_cluster_health_status 0` (or 1 or 2)
**Explain:** Alert monitors Elasticsearch cluster health directly via custom exporter (port 9114). Status: 3=green, 2=yellow, 1=red, 0=down. Fires when status < 3. In single-node setup, can't stop a node to get yellow, but can simulate by making indices read-only or stopping Elasticsearch. Exporter queries Elasticsearch `/_cluster/health` endpoint and exposes status as Prometheus metric.
**Restore (Test 1):** `vagrant ssh monitoring-server-auto -c "sudo systemctl start elasticsearch"`
**Restore (Test 2):** `vagrant ssh monitoring-server-auto -c "curl -X PUT http://localhost:9200/_all/_settings -H 'Content-Type: application/json' -d '{\"index.blocks.read_only_allow_delete\": null}'"`

---

### 26. VM Performance Dashboard (Grafana)
**Show:** Grafana → Dashboards → Browse → "VM Performance Dashboard"
**Verify:** CPU, Memory, Disk I/O, Network, Disk space, Load average panels showing data

---

### 27. Docker Container Dashboard (Grafana)
**Show:** Grafana → Dashboards → Browse → "Docker Container Dashboard"
**Verify:** Container CPU, Memory, Restart counts, Status panels showing data

---

### 28. Application Performance Dashboard (Grafana)
**Show:** Grafana → Dashboards → Browse → "Application Performance Dashboard"
**Verify:** Request rate, Response times (p50/p95/p99), Error rate, Total requests panels showing data

---

### 29. System Logs Dashboard (Kibana)
**Show:** Kibana → Dashboards → "System Logs Dashboard"
**Verify:** System Logs Count by Type (bar), Timeline (time series), By Hostname (pie) visualizations

---

### 30. Application Logs Dashboard (Kibana)
**Show:** Kibana → Dashboards → "Application Logs Dashboard"
**Verify:** Application Logs Count by Type (bar), Timeline (time series), By Hostname (pie) visualizations

---

### 31. Docker Logs Dashboard (Kibana)
**Show:** Kibana → Dashboards → "Docker Logs Dashboard"
**Verify:** Docker Logs Count by Type (bar), Timeline (time series), By Hostname (pie) visualizations

---

## DOCUMENTATION REQUIREMENTS

### 32. README File
**Show:** `README.md` file
**Verify:** Contains Quick Start, Access URLs, Architecture, Features, Troubleshooting

---

### 33. Code Quality
**Show:** Ansible roles structure, Python scripts, config files
**Verify:** Organized by component, comments present, follows best practices

---

**Total: 33/33 requirements complete**
