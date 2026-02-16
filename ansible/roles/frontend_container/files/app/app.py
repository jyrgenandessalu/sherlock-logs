from flask import Flask, jsonify, render_template_string, request
import socket, os, psutil
import logging
import json
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

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

app_disk_usage_bytes = Gauge(
    'flask_app_disk_usage_bytes',
    'Disk usage in bytes',
    ['hostname', 'role']
)

app_disk_total_bytes = Gauge(
    'flask_app_disk_total_bytes',
    'Total disk space in bytes',
    ['hostname', 'role']
)

# Set app info metric
app_info.labels(hostname=hostname, role=role).set(1)

@app.route("/")
def home():
    start_time = datetime.utcnow()
    try:
        http_requests_total.labels(method='GET', endpoint='/', status='200').inc()
        response = f"Hello from {role} on {hostname}! (containerized) ✅ Updated via CI/CD! TEREKEST, SIIN MA OLEN!!!"
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
        disk = psutil.disk_usage('/')
        
        app_cpu_usage_percent.labels(hostname=hostname, role=role).set(cpu)
        app_memory_usage_bytes.labels(hostname=hostname, role=role).set(mem.used)
        app_memory_total_bytes.labels(hostname=hostname, role=role).set(mem.total)
        app_disk_usage_bytes.labels(hostname=hostname, role=role).set(disk.used)
        app_disk_total_bytes.labels(hostname=hostname, role=role).set(disk.total)
        
        http_requests_total.labels(method='GET', endpoint='/metrics', status='200').inc()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.debug("Metrics endpoint accessed", extra={
            "event": "metrics_request",
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "disk_percent": disk.percent,
            "duration_seconds": duration
        })
        
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as e:
        logger.error("Error generating metrics", extra={
            "event": "metrics_error",
            "error": str(e)
        }, exc_info=True)
        raise

@app.route("/dashboard")
def dashboard():
    """HTML dashboard displaying infrastructure metrics"""
    start_time = datetime.utcnow()
    try:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.2)
        disk = psutil.disk_usage('/')
        
        http_requests_total.labels(method='GET', endpoint='/dashboard', status='200').inc()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("Dashboard accessed", extra={
            "event": "dashboard_request",
            "method": "GET",
            "endpoint": "/dashboard",
            "status": 200,
            "duration_seconds": duration
        })
        
        html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Infrastructure Metrics - {{ hostname }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .metric { margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }
            .metric-label { font-weight: bold; color: #666; }
            .metric-value { font-size: 24px; color: #333; margin-top: 5px; }
            .bar { background: #e0e0e0; height: 30px; border-radius: 15px; margin-top: 10px; overflow: hidden; }
            .bar-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); transition: width 0.3s; }
            .warning { border-left-color: #ff9800; }
            .critical { border-left-color: #f44336; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖥️ Infrastructure Metrics Dashboard</h1>
            <div class="metric">
                <div class="metric-label">Server Hostname</div>
                <div class="metric-value">{{ hostname }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Server Role</div>
                <div class="metric-value">{{ role }}</div>
            </div>
            <div class="metric {{ 'warning' if cpu > 70 else '' }} {{ 'critical' if cpu > 90 else '' }}">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-value">{{ cpu }}%</div>
                <div class="bar">
                    <div class="bar-fill" style="width: {{ cpu }}%"></div>
                </div>
            </div>
            <div class="metric {{ 'warning' if mem.percent > 70 else '' }} {{ 'critical' if mem.percent > 90 else '' }}">
                <div class="metric-label">Memory Usage</div>
                <div class="metric-value">{{ mem.percent }}% ({{ mem.used_gb }} GB / {{ mem.total_gb }} GB)</div>
                <div class="bar">
                    <div class="bar-fill" style="width: {{ mem.percent }}%"></div>
                </div>
            </div>
            <div class="metric {{ 'warning' if disk.percent > 70 else '' }} {{ 'critical' if disk.percent > 90 else '' }}">
                <div class="metric-label">Disk Usage</div>
                <div class="metric-value">{{ disk.percent }}% ({{ disk.used_gb }} GB / {{ disk.total_gb }} GB)</div>
                <div class="bar">
                    <div class="bar-fill" style="width: {{ disk.percent }}%"></div>
                </div>
            </div>
            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                <strong>Significance:</strong> These metrics help monitor server health, resource utilization, 
                and capacity planning. CPU and memory usage indicate current load, while disk usage helps 
                prevent storage issues. Monitoring these metrics is essential for maintaining infrastructure 
                reliability and performance.
            </p>
        </div>
    </body>
    </html>
    """
        
        return render_template_string(html_template,
            hostname=hostname,
            role=role,
            cpu=round(cpu, 2),
            mem={
                'percent': round(mem.percent, 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'total_gb': round(mem.total / (1024**3), 2)
            },
            disk={
                'percent': round(disk.percent, 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'total_gb': round(disk.total / (1024**3), 2)
            }
        )
    except Exception as e:
        logger.error("Error processing dashboard request", extra={
            "event": "dashboard_error",
            "method": "GET",
            "endpoint": "/dashboard",
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
