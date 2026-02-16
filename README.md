# 🕵️ Sherlock Logs - Monitoring & Logging Infrastructure

Comprehensive monitoring and logging system using **Prometheus + Grafana** for metrics and **ELK Stack** (Elasticsearch, Logstash, Kibana) for centralized logging.

## 🚀 Quick Start

```bash
# Start all VMs and provision automatically
vagrant up

# Re-run provisioning (if needed)
vagrant provision
```

**First-time setup:** ~15-20 minutes (downloads and installs all components)

## 📊 Access URLs

- **Grafana:** http://192.168.56.25:3000 (admin/admin)
- **Prometheus:** http://192.168.56.25:9090
- **Kibana:** http://192.168.56.25:5601
- **Elasticsearch:** http://192.168.56.25:9200
- **Jenkins:** http://192.168.56.24:8080

## 🏗️ Architecture

**6 VMs:**
- `lb-server-auto` (192.168.56.20) - Load Balancer (NGINX)
- `web1-server-auto` (192.168.56.21) - Web Server 1 (Flask frontend)
- `web2-server-auto` (192.168.56.22) - Web Server 2 (Flask frontend)
- `app-server-auto` (192.168.56.23) - App Server (Flask backend)
- `backup-server-auto` (192.168.56.24) - CI/CD (Jenkins)
- `monitoring-server-auto` (192.168.56.25) - **Monitoring & Logging**

**Monitoring Stack:**
- **Prometheus** - Metrics collection (scrape interval: 15s)
- **Grafana** - Dashboards & alerts (7 alerts configured)
- **Node Exporter** - System metrics (all VMs)
- **cAdvisor** - Container metrics (Docker VMs)

**Logging Stack:**
- **Elasticsearch** - Log storage
- **Logstash** - Log processing (with alert notifications)
- **Kibana** - Log visualization
- **Filebeat** - Log collection (all VMs)

## 📋 Features

- ✅ Real-time metrics (CPU, memory, disk, network)
- ✅ Container monitoring (Docker metrics via cAdvisor)
- ✅ Application metrics (Flask apps with Prometheus client)
- ✅ Centralized logging (syslog, application, Docker logs)
- ✅ Automated alerting (7 Grafana alerts)
- ✅ Log-based alerts (Logstash error detection)
- ✅ Pre-configured dashboards (3 Grafana, 3 Kibana)

## 🛠️ VM Management

```bash
vagrant suspend    # Pause VMs (saves state)
vagrant resume    # Resume paused VMs
vagrant halt      # Shut down VMs (data preserved)
vagrant up        # Start VMs
vagrant destroy   # ⚠️ Delete VMs and all data
```

## 📚 Documentation

- **Requirements Testing:** `REQUIREMENTS_TESTING.md` - Complete testing guide
- **Full Documentation:** `DOCUMENTATION.md` - Detailed setup and architecture
- **Verification Script:** `verify-requirements.ps1` - Automated testing

## 🔧 Troubleshooting

**Services not starting?**
```bash
vagrant ssh monitoring-server-auto -c "sudo systemctl status prometheus grafana elasticsearch logstash kibana"
```

**Check Prometheus targets:**
- Visit: http://192.168.56.25:9090/targets
- All should show "UP"

**Check Grafana alerts:**
- Visit: http://192.168.56.25:3000/alerting/list
- Should show 7 configured alerts

**View logs:**
```bash
vagrant ssh monitoring-server-auto -c "sudo journalctl -u logstash -n 50"
```

---

**Automation:** Fully automated via Ansible - `vagrant up` sets up everything.
