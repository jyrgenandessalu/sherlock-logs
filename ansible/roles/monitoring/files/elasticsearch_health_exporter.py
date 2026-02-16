#!/usr/bin/env python3
"""Minimal Elasticsearch health status exporter for Prometheus."""
import http.server
import socketserver
import urllib.request
import json
from urllib.error import URLError

PORT = 9114

def get_health():
    """Get Elasticsearch cluster health status."""
    try:
        with urllib.request.urlopen("http://localhost:9200/_cluster/health", timeout=5) as r:
            data = json.loads(r.read().decode())
            status = data.get("status", "unknown")
            # Map: green=3, yellow=2, red=1, unknown/down=0
            return {"green": 3, "yellow": 2, "red": 1}.get(status, 0)
    except:
        return 0  # Down/unreachable

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"elasticsearch_cluster_health_status {get_health()}\n".encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args): pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

