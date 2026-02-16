# Kibana Dashboards Setup Guide

## Overview

After running the Ansible playbook, the Kibana index pattern `logs-*` is automatically created. This guide explains how to create the three required dashboards:

1. **System Logs Dashboard** - System logs from all VMs (syslog, auth.log, kern.log)
2. **Application Logs Dashboard** - Application-specific logs (Flask app logs)
3. **Docker Logs Dashboard** - Docker container logs (stdout, stderr)

## Prerequisites

- Kibana is running and accessible at `http://192.168.56.25:5601`
- Index pattern `logs-*` has been created (done automatically by Ansible)
- Logs are being collected and indexed in Elasticsearch

## Creating Dashboards

### Step 1: Access Kibana

1. Open your browser and navigate to `http://192.168.56.25:5601`
2. You should see the Kibana home page

### Step 2: Verify Index Pattern

1. Go to **Stack Management** > **Index Patterns**
2. Verify that `logs-*` index pattern exists
3. If it doesn't exist, create it:
   - Click **Create index pattern**
   - Enter `logs-*` as the pattern
   - Select `@timestamp` as the time field
   - Click **Create index pattern**

### Step 3: Create System Logs Dashboard

1. Go to **Discover**
2. Select the `logs-*` index pattern
3. In the search bar, enter: `fields.log_type: system`
4. Click **Save** and name it "System Logs View"
5. Go to **Dashboard** > **Create Dashboard**
6. Click **Add** > **Add from library**
7. Add visualizations:
   - **Logs Timeline**: Add a "Data Table" visualization showing logs over time
   - **Logs by Host**: Add a "Pie Chart" grouped by `fields.hostname`
   - **Log Level Distribution**: Add a "Bar Chart" if log levels are available
8. Save the dashboard as "System Logs Dashboard"

### Step 4: Create Application Logs Dashboard

1. Go to **Discover**
2. Select the `logs-*` index pattern
3. In the search bar, enter: `fields.log_type: application`
4. Create visualizations:
   - **Application Logs Timeline**: Time series of application logs
   - **Logs by Application**: Group by application name/role
   - **Error Logs**: Filter for error-level logs
5. Save the dashboard as "Application Logs Dashboard"

### Step 5: Create Docker Logs Dashboard

1. Go to **Discover**
2. Select the `logs-*` index pattern
3. In the search bar, enter: `fields.log_type: docker`
4. Create visualizations:
   - **Docker Logs Timeline**: Time series of Docker logs
   - **Logs by Container**: Group by container name
   - **Logs by Host**: Group by hostname
5. Save the dashboard as "Docker Logs Dashboard"

## Quick Filter Reference

Use these KQL (Kibana Query Language) filters in Discover:

- **System logs**: `fields.log_type: system`
- **Application logs**: `fields.log_type: application`
- **Docker logs**: `fields.log_type: docker`
- **Specific host**: `fields.hostname: "web1-server-auto"`
- **Time range**: Use the time picker in the top right

## Automated Dashboard Creation (Future Enhancement)

Full dashboard creation via API is complex due to Kibana's dashboard JSON structure. The current automation:
- ✅ Creates the index pattern automatically
- ⏳ Dashboard creation can be done manually or enhanced later with full JSON exports

## Testing

After creating dashboards:

1. Generate some logs:
   ```bash
   # On any VM, generate system logs
   logger "Test system log message"
   
   # Access Flask app to generate application logs
   curl http://192.168.56.20/
   
   # Check Docker logs
   docker logs <container_name>
   ```

2. Verify logs appear in Kibana:
   - Go to Discover
   - Select `logs-*` index pattern
   - Check that logs appear with appropriate `fields.log_type` values

## Troubleshooting

**No logs appearing:**
- Check Filebeat is running: `sudo systemctl status filebeat`
- Check Logstash is running: `sudo systemctl status logstash`
- Check Elasticsearch has indices: `curl http://192.168.56.25:9200/_cat/indices`

**Index pattern not found:**
- Run the dashboard setup script manually:
  ```bash
  sudo /usr/local/bin/create_kibana_dashboards.py
  ```

**Dashboards not loading:**
- Ensure index pattern `logs-*` exists
- Check that logs are being indexed (use Discover to verify)
- Verify time range is set correctly

