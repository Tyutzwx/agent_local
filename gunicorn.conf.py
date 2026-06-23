# Gunicorn 配置文件
# 启动方式：gunicorn -c gunicorn.conf.py app:app

# 监听地址和端口（与当前使用的 9002 一致）
bind = "0.0.0.0:9002"

# 工作进程数（建议按 CPU 核数 * 2 + 1，此处设为 4）
workers = 4

# 工作模式（sync 适合 CPU 密集型，稳定可靠）
worker_class = "sync"

# 每个 worker 处理 N 个请求后自动重启（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 100

# 请求超时（秒）
timeout = 120

# 日志文件路径
errorlog = "/data/tuoni/agent_local/gunicorn_error.log"
accesslog = "/data/tuoni/agent_local/gunicorn_access.log"
loglevel = "info"

# 进程 ID 文件（方便管理）
pidfile = "/data/tuoni/agent_local/gunicorn.pid"

# 优雅重启超时
graceful_timeout = 60
