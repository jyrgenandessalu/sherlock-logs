from flask import Flask, jsonify, request
import socket, os, psutil
import logging
import json
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Get hostname and role
hostname = os.getenv("HOST_VM", socket.gethostname())
role = os.getenv("ROLE", "unknown")

# Configure structured JSON logging
log_dir = "/var/log/flask_apps"
os.makedirs(log_dir, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "hostname": hostname,
            "role": role,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Set up logger
logger = logging.getLogger("flask_app")
logger.setLevel(logging.INFO)

# File handler for application logs
log_file = os.path.join(log_dir, f"{role}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

# Also log to console for Docker logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(JSONFormatter())
logger.addHandler(console_handler)

logger.info("Flask application started", extra={"event": "app_start", "hostname": hostname, "role": role})

# Prometheus metrics
http_requests_total = Counter(
    'flask_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

app_info = Gauge(
    'flask_app_info',
    'Application information',
    ['hostname', 'role']
)

app_cpu_usage_percent = Gauge(
    'flask_app_cpu_usage_percent',
    'CPU usage percentage',
    ['hostname', 'role']
)

app_memory_usage_bytes = Gauge(
    'flask_app_memory_usage_bytes',
    'Memory usage in bytes',
    ['hostname', 'role']
)

app_memory_total_bytes = Gauge(
    'flask_app_memory_total_bytes',
    'Total memory in bytes',
    ['hostname', 'role']
)

# Set app info metric
app_info.labels(hostname=hostname, role=role).set(1)

@app.route("/")
def home():
    start_time = datetime.utcnow()
    try:
        http_requests_total.labels(method='GET', endpoint='/', status='200').inc()
        response = f"Hello from {role} on {hostname}! (containerized) ✅ Updated via CI/CD!"
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("HTTP request processed", extra={
            "event": "http_request",
            "method": "GET",
            "endpoint": "/",
            "status": 200,
            "duration_seconds": duration,
            "remote_addr": request.remote_addr
        })
        return response
    except Exception as e:
        logger.error("Error processing request", extra={
            "event": "http_error",
            "method": "GET",
            "endpoint": "/",
            "error": str(e)
        }, exc_info=True)
        raise

@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    start_time = datetime.utcnow()
    try:
        # Update metrics
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.2)
        
        app_cpu_usage_percent.labels(hostname=hostname, role=role).set(cpu)
        app_memory_usage_bytes.labels(hostname=hostname, role=role).set(mem.used)
        app_memory_total_bytes.labels(hostname=hostname, role=role).set(mem.total)
        
        http_requests_total.labels(method='GET', endpoint='/metrics', status='200').inc()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.debug("Metrics endpoint accessed", extra={
            "event": "metrics_request",
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "duration_seconds": duration
        })
        
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as e:
        logger.error("Error generating metrics", extra={
            "event": "metrics_error",
            "error": str(e)
        }, exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Starting Flask application server", extra={
        "event": "server_start",
        "host": "0.0.0.0",
        "port": 5000
    })
    app.run(host="0.0.0.0", port=5000)
