#!/usr/bin/env python3
"""
Script to create Kibana index patterns and basic dashboards
Uses Kibana Saved Objects API
"""

import json
import time
import requests
import sys

KIBANA_URL = "http://localhost:5601"
INDEX_PATTERN = "logs-*"

def complete_kibana_setup():
    """Complete Kibana interactive setup if needed"""
    print("Attempting to complete Kibana interactive setup...")
    url = f"{KIBANA_URL}/internal/interactive_setup/complete"
    headers = {
        "kbn-xsrf": "true",
        "Content-Type": "application/json"
    }
    data = {
        "host": "http://localhost:9200"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 204]:
            print("Kibana setup completed successfully")
            return True
        elif response.status_code in [400, 404]:
            # Setup already completed or not needed
            print("Kibana setup already completed or not required")
            return True
        else:
            print(f"Setup completion returned status {response.status_code}, continuing anyway...")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Could not complete setup (may already be done): {e}")
        return False

def wait_for_kibana(max_retries=30, delay=10):
    """Wait for Kibana to be ready"""
    print("Waiting for Kibana to be ready...")
    
    # Try to complete setup first
    complete_kibana_setup()
    time.sleep(5)
    
    for i in range(max_retries):
        try:
            # Try the status endpoint
            response = requests.get(f"{KIBANA_URL}/api/status", timeout=5)
            if response.status_code == 200:
                print("Kibana is ready!")
                return True
            # If we get 503, try completing setup again
            elif response.status_code == 503 and i % 5 == 0:
                print("Kibana in setup mode, attempting to complete setup...")
                complete_kibana_setup()
                time.sleep(5)
        except requests.exceptions.RequestException:
            pass
        print(f"Attempt {i+1}/{max_retries}: Kibana not ready yet, waiting...")
        time.sleep(delay)
    return False

def create_index_pattern():
    """Create index pattern for logs"""
    print(f"Creating index pattern: {INDEX_PATTERN}")
    url = f"{KIBANA_URL}/api/saved_objects/index-pattern/{INDEX_PATTERN.replace('*', 'star')}"
    headers = {
        "kbn-xsrf": "true",
        "Content-Type": "application/json"
    }
    data = {
        "attributes": {
            "title": INDEX_PATTERN,
            "timeFieldName": "@timestamp"
        }
    }
    
    try:
        # Try to create
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 201]:
            print("Index pattern created successfully")
            return True
        elif response.status_code == 409:
            print("Index pattern already exists")
            return True
        else:
            print(f"Failed to create index pattern: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error creating index pattern: {e}")
        return False

def main():
    """Main function"""
    if not wait_for_kibana():
        print("ERROR: Kibana is not ready after waiting")
        sys.exit(1)
    
    if create_index_pattern():
        print("\nKibana setup complete!")
        print(f"Access Kibana at {KIBANA_URL}")
        print("\nTo create dashboards:")
        print("1. Go to Kibana > Discover")
        print("2. Select 'logs-*' index pattern")
        print("3. Use filters: fields.log_type: system, application, or docker")
        print("4. Create visualizations and save as dashboards")
        sys.exit(0)
    else:
        print("ERROR: Failed to create index pattern")
        sys.exit(1)

if __name__ == "__main__":
    main()

