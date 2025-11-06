import multiprocessing

# ----------------------------
# Basic Server Settings
# ----------------------------
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = "gthread"  # Better for Django APIs than sync
threads = 4

# ----------------------------
# Performance & Reliability
# ----------------------------
timeout = 120              # Worker timeout
graceful_timeout = 30      # Graceful shutdown time
keepalive = 5              # Keep connections open for reuse
preload_app = True         # Load Django app once, then fork workers

# ----------------------------
# Logging (Docker Friendly)
# ----------------------------
loglevel = "debug"
accesslog = "-"
errorlog = "-"

# ----------------------------
# Worker Connections (if using async classes)
# ----------------------------
# worker_connections = 1000   # Only needed for gevent/eventlet

# ----------------------------
# Security Headers (Recommended)
# ----------------------------
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
