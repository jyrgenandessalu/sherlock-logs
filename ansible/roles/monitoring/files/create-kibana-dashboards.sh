#!/bin/bash
# Script to create Kibana index patterns and dashboards
# This script uses the Kibana Saved Objects API

KIBANA_URL="http://localhost:5601"
INDEX_PATTERN="logs-*"

# Wait for Kibana to be ready
echo "Waiting for Kibana to be ready..."
for i in {1..30}; do
    if curl -s -f "${KIBANA_URL}/api/status" > /dev/null 2>&1; then
        echo "Kibana is ready!"
        break
    fi
    echo "Attempt $i/30: Kibana not ready yet, waiting..."
    sleep 10
done

# Create index pattern
echo "Creating index pattern: ${INDEX_PATTERN}"
curl -X POST "${KIBANA_URL}/api/saved_objects/index-pattern/${INDEX_PATTERN}" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d "{
    \"attributes\": {
      \"title\": \"${INDEX_PATTERN}\",
      \"timeFieldName\": \"@timestamp\"
    }
  }" 2>/dev/null | grep -q "created_at\|updated_at" && echo "Index pattern created/updated" || echo "Index pattern may already exist"

echo "Kibana setup complete!"
echo "Access Kibana at ${KIBANA_URL} to create dashboards manually or import dashboard JSON files"

