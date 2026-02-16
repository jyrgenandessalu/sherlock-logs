#!/usr/bin/env python3
"""
Script to create Grafana alert rules via Unified Alerting API
Creates all required alerts for Phase 5.1 and 5.2
"""

import json
import time
import requests
import sys

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"

def wait_for_grafana(max_retries=30, delay=10):
    """Wait for Grafana to be ready"""
    print("Waiting for Grafana to be ready...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                print("Grafana is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Attempt {i+1}/{max_retries}: Grafana not ready yet, waiting...")
        time.sleep(delay)
    return False

def get_auth_headers():
    """Get authentication headers"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Grafana-Org-Id": "1"  # Default org ID
    }, (GRAFANA_USER, GRAFANA_PASSWORD)

def create_alert_folder(folder_title):
    """Create an alert folder if it doesn't exist"""
    headers, auth = get_auth_headers()
    try:
        # Check if folder exists
        response = requests.get(
            f"{GRAFANA_URL}/api/folders",
            headers=headers,
            auth=auth,
            timeout=10
        )
        if response.status_code == 200:
            folders = response.json()
            for folder in folders:
                if folder.get("title") == folder_title:
                    print(f"Folder '{folder_title}' already exists (UID: {folder.get('uid')})")
                    return folder.get("uid")
        
        # Create folder if it doesn't exist
        response = requests.post(
            f"{GRAFANA_URL}/api/folders",
            headers=headers,
            auth=auth,
            json={"title": folder_title},
            timeout=10
        )
        if response.status_code in [200, 201]:
            folder = response.json()
            print(f"Folder '{folder_title}' created successfully (UID: {folder.get('uid')})")
            return folder.get("uid")
        else:
            print(f"Warning: Could not create folder '{folder_title}': {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Warning: Error creating folder: {e}")
        return None

def get_prometheus_datasource_uid():
    """Get Prometheus datasource UID"""
    headers, auth = get_auth_headers()
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources/name/Prometheus",
            headers=headers,
            auth=auth,
            timeout=10
        )
        if response.status_code == 200:
            datasource = response.json()
            return datasource.get("uid", "prometheus")
        else:
            print(f"Warning: Could not find Prometheus datasource, using default UID")
            return "prometheus"
    except requests.exceptions.RequestException as e:
        print(f"Warning: Error getting datasource UID: {e}, using default")
        return "prometheus"

def parse_duration_to_seconds(duration_str):
    """Convert duration string like '5m' to seconds"""
    if not duration_str:
        return 0
    duration_str = duration_str.strip().lower()
    if duration_str.endswith('s'):
        return int(duration_str[:-1])
    elif duration_str.endswith('m'):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 86400
    return 0

def create_alert_rule(alert_config, datasource_uid, folder_uid):
    """Create an alert rule in Grafana using Provisioning API"""
    headers, auth = get_auth_headers()
    
    # Replace datasource UID placeholder in queries
    alert_json = json.dumps(alert_config)
    alert_json = alert_json.replace("${DATASOURCE_UID}", datasource_uid)
    alert_config = json.loads(alert_json)
    
    # Extract rule data
    rule_data = alert_config.get("rules", [{}])[0].get("grafana_alert", {})
    
    # Parse interval from config (default to 30s if not specified)
    interval_str = alert_config.get("interval", "30s")
    interval_seconds = parse_duration_to_seconds(interval_str)
    
    # Parse 'for' duration
    for_duration = rule_data.get("for", "5m")
    for_seconds = parse_duration_to_seconds(for_duration)
    
    # Ensure data array has proper structure
    data = rule_data.get("data", [])
    # Ensure each data item has required fields
    for item in data:
        if "datasourceUid" not in item:
            item["datasourceUid"] = datasource_uid
        if "model" not in item:
            item["model"] = {}
    
    # Build payload for provisioning API with all required fields
    rule_payload = {
        "folderUID": folder_uid or "",
        "ruleGroup": alert_config.get("name", "infrastructure_alerts"),
        "title": rule_data.get("title", "Unknown"),
        "condition": rule_data.get("condition", "C"),
        "data": data,
        "noDataState": rule_data.get("noDataState", "NoData"),
        "execErrState": rule_data.get("execErrState", "Alerting"),
        "for": f"{for_seconds}s",  # Convert to seconds format
        "intervalSeconds": interval_seconds,  # Add interval in seconds
        "annotations": rule_data.get("annotations", {}),
        "labels": rule_data.get("labels", {})
    }
    
    # Add UID if present (for idempotency)
    if rule_data.get("uid"):
        rule_payload["uid"] = rule_data.get("uid")
    
    try:
        # Use provisioning API endpoint (designed for automated setup)
        response = requests.post(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
            headers=headers,
            auth=auth,
            json=rule_payload,
            timeout=30
        )
        if response.status_code in [200, 201]:
            print(f"✓ Alert rule '{rule_data.get('title', 'Unknown')}' created successfully")
            return True
        elif response.status_code == 409:
            print(f"✓ Alert rule '{rule_data.get('title', 'Unknown')}' already exists")
            return True
        else:
            print(f"✗ Failed to create alert rule '{rule_data.get('title', 'Unknown')}': {response.status_code} - {response.text}")
            # Try to get more details about the error
            if response.status_code == 403:
                print(f"  Note: 403 error usually means authentication/permission issue. Check Grafana admin user has alerting permissions.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error creating alert rule: {e}")
        return False

def delete_existing_alerts_in_group(folder_uid, rule_group):
    """Delete existing alerts in a rule group to avoid conflicts"""
    headers, auth = get_auth_headers()
    try:
        # Get all alert rules
        response = requests.get(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
            headers=headers,
            auth=auth,
            timeout=10
        )
        if response.status_code == 200:
            rules = response.json()
            deleted = 0
            for rule in rules:
                # Check if rule is in the same folder and group
                if rule.get("folderUID") == folder_uid and rule.get("ruleGroup") == rule_group:
                    rule_uid = rule.get("uid")
                    if rule_uid:
                        delete_response = requests.delete(
                            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}",
                            headers=headers,
                            auth=auth,
                            timeout=10
                        )
                        if delete_response.status_code in [200, 204]:
                            deleted += 1
            if deleted > 0:
                print(f"Deleted {deleted} existing alert(s) in group '{rule_group}'")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not check/delete existing alerts: {e}")
    return False

def create_all_alerts(datasource_uid):
    """Create all required alert rules"""
    # Create alert folder first
    folder_uid = create_alert_folder("Infrastructure Alerts")
    if not folder_uid:
        print("Warning: Could not create alert folder, continuing anyway...")
        folder_uid = ""
    
    # Clean up existing alerts in the infrastructure_alerts group
    print("\nCleaning up existing alerts in 'infrastructure_alerts' group...")
    delete_existing_alerts_in_group(folder_uid, "infrastructure_alerts")
    
    alerts_created = 0
    alerts_failed = 0
    
    # Alert 1: VM CPU High
    print("\nCreating Alert 1: VM CPU High...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "vm_cpu_high",
                "title": "VM CPU High",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 300, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [80], "type": "gt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "5m",
                "annotations": {
                    "description": "VM {{ $labels.instance }} CPU usage is above 80% (current: {{ $value }}%)",
                    "summary": "High CPU usage on {{ $labels.instance }}"
                },
                "labels": {
                    "severity": "warning",
                    "alertname": "VM_CPU_High"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 2: VM Disk Space Low
    print("\nCreating Alert 2: VM Disk Space Low...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "vm_disk_low",
                "title": "VM Disk Space Low",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 60, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": '(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [20], "type": "lt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "1m",
                "annotations": {
                    "description": "VM {{ $labels.instance }} disk space is below 20% (current: {{ $value }}% available)",
                    "summary": "Low disk space on {{ $labels.instance }}"
                },
                "labels": {
                    "severity": "critical",
                    "alertname": "VM_Disk_Low"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 3: VM Memory High
    print("\nCreating Alert 3: VM Memory High...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "vm_memory_high",
                "title": "VM Memory High",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 300, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [90], "type": "gt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "5m",
                "annotations": {
                    "description": "VM {{ $labels.instance }} memory usage is above 90% (current: {{ $value }}%)",
                    "summary": "High memory usage on {{ $labels.instance }}"
                },
                "labels": {
                    "severity": "warning",
                    "alertname": "VM_Memory_High"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 4: Container Restart High
    print("\nCreating Alert 4: Container Restart High...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "1m",
        "rules": [{
            "grafana_alert": {
                "uid": "container_restart_high",
                "title": "Container Restart High",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 900, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": 'sum by (name, instance) (count(count_over_time(container_start_time_seconds{name!="",container_label_restartcount!=""}[15m:30s]) > 0)) - 1',
                            "refId": "A",
                            "intervalMs": 30000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [3], "type": "gt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "1m",
                "annotations": {
                    "description": "Container {{ $labels.name }} on {{ $labels.instance }} has restarted more than 3 times in 15 minutes (restarts: {{ $value }})",
                    "summary": "High container restart rate for {{ $labels.name }}"
                },
                "labels": {
                    "severity": "warning",
                    "alertname": "Container_Restart_High"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 5: Container Memory High
    print("\nCreating Alert 5: Container Memory High...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "container_memory_high",
                "title": "Container Memory High",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 300, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": '(container_memory_usage_bytes{name!=""} / container_memory_working_set_bytes{name!=""}) * 100',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [80], "type": "gt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "NoData",
                "execErrState": "Alerting",
                "for": "5m",
                "annotations": {
                    "description": "Container {{ $labels.name }} on {{ $labels.instance }} memory usage is above 80% (current: {{ $value }}%)",
                    "summary": "High container memory usage for {{ $labels.name }}"
                },
                "labels": {
                    "severity": "warning",
                    "alertname": "Container_Memory_High"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 6: VM Unreachable
    print("\nCreating Alert 6: VM Unreachable...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "vm_unreachable",
                "title": "VM Unreachable",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 60, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": 'up{job="node_exporter"}',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [1], "type": "lt"},
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "Alerting",
                "execErrState": "Alerting",
                "for": "1m",
                "annotations": {
                    "description": "VM {{ $labels.instance }} is unreachable (Node Exporter is down)",
                    "summary": "VM {{ $labels.instance }} unreachable"
                },
                "labels": {
                    "severity": "critical",
                    "alertname": "VM_Unreachable"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    # Alert 7: Elasticsearch Health
    print("\nCreating Alert 7: Elasticsearch Cluster Health...")
    alert_config = {
        "name": "infrastructure_alerts",
        "interval": "30s",
        "rules": [{
            "grafana_alert": {
                "uid": "elasticsearch_health",
                "title": "Elasticsearch Cluster Health",
                "condition": "C",
                "data": [
                    {
                        "refId": "A",
                        "relativeTimeRange": {"from": 300, "to": 0},
                        "datasourceUid": datasource_uid,
                        "model": {
                            "expr": 'elasticsearch_cluster_health_status{job="elasticsearch_exporter"}',
                            "refId": "A",
                            "intervalMs": 15000,
                            "maxDataPoints": 43200
                        }
                    },
                    {
                        "refId": "B",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "reduce",
                            "expression": "A",
                            "reducer": "last",
                            "refId": "B"
                        }
                    },
                    {
                        "refId": "C",
                        "datasourceUid": "__expr__",
                        "model": {
                            "type": "threshold",
                            "expression": "B",
                            "conditions": [{
                                "evaluator": {"params": [3], "type": "lt"},  # Less than 3 (green=3, yellow=2, red=1, down=0)
                                "operator": {"type": "and"},
                                "query": {"model": "B"},
                                "reducer": {"type": "last", "params": []},
                                "type": "query"
                            }],
                            "refId": "C"
                        }
                    }
                ],
                "noDataState": "Alerting",
                "execErrState": "Alerting",
                "for": "1m",
                "annotations": {
                    "description": "Elasticsearch cluster health is yellow or red. Status: {{ $value }} (3=green, 2=yellow, 1=red, 0=down)",
                    "summary": "Elasticsearch cluster health is not green (yellow/red/down)"
                },
                "labels": {
                    "severity": "critical",
                    "alertname": "Elasticsearch_Health"
                }
            }
        }]
    }
    if create_alert_rule(alert_config, datasource_uid, folder_uid):
        alerts_created += 1
    else:
        alerts_failed += 1
    
    return alerts_created, alerts_failed

def verify_admin_permissions():
    """Verify admin user has necessary permissions"""
    headers, auth = get_auth_headers()
    try:
        # Check if we can access the alerting API
        response = requests.get(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
            headers=headers,
            auth=auth,
            timeout=10
        )
        if response.status_code in [200, 403]:
            # 200 = has access, 403 = no access (but endpoint exists)
            if response.status_code == 403:
                print("⚠ Warning: Admin user may not have alerting permissions")
                print("  This could be due to Grafana configuration or permissions.")
                print("  Alerts will need to be created manually via Grafana UI.")
                return False
            return True
        return True
    except requests.exceptions.RequestException:
        return True  # Assume OK if we can't check

def main():
    """Main function"""
    print("=" * 60)
    print("Grafana Alert Rules Automation Script")
    print("=" * 60)
    
    if not wait_for_grafana():
        print("\nERROR: Grafana is not ready after waiting")
        sys.exit(1)
    
    # Verify permissions
    if not verify_admin_permissions():
        print("\n" + "=" * 60)
        print("⚠ Alert Creation Skipped - Manual Setup Required")
        print("=" * 60)
        print("\nDue to permission issues, alerts need to be created manually.")
        print("See GRAFANA_ALERTS_SETUP.md for step-by-step instructions.")
        print(f"\nAccess Grafana at {GRAFANA_URL} (admin/admin)")
        print("Go to Alerting > Alert rules > New alert rule")
        sys.exit(0)
    
    datasource_uid = get_prometheus_datasource_uid()
    print(f"\nUsing Prometheus datasource UID: {datasource_uid}")
    
    alerts_created, alerts_failed = create_all_alerts(datasource_uid)
    
    print("\n" + "=" * 60)
    print("Alert Creation Summary")
    print("=" * 60)
    print(f"✓ Alerts created/skipped: {alerts_created}")
    if alerts_failed > 0:
        print(f"✗ Alerts failed: {alerts_failed}")
    print(f"\nTotal alerts: {alerts_created + alerts_failed}")
    
    if alerts_failed == 0:
        print("\n✓ All alerts created successfully!")
        print(f"\nAccess Grafana at {GRAFANA_URL}")
        print("Go to Alerting > Alert rules to view all alerts")
        sys.exit(0)
    else:
        print(f"\n⚠ Some alerts failed to create (likely permission issue).")
        print("\nAlerts can be created manually:")
        print("1. Go to Grafana > Alerting > Alert rules > New alert rule")
        print("2. Follow instructions in GRAFANA_ALERTS_SETUP.md")
        print(f"3. Access Grafana at {GRAFANA_URL} (admin/admin)")
        sys.exit(0)  # Exit with 0 to not fail Ansible task

if __name__ == "__main__":
    main()
