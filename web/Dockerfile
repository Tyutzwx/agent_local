FROM python:3.10-slim

WORKDIR /app
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

# 替换为清华镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update --option Acquire::Retries=10 && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 复制配置文件
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制源码
COPY src/ /app/src/
COPY static/ /app/static/
COPY templates/ /app/templates/

# 复制 Gunicorn 配置
COPY config/gunicorn.conf.py /app/gunicorn.conf.py

# 设置 PYTHONPATH 让 Python 能找到 src 目录
ENV PYTHONPATH=/app/src:$PYTHONPATH

RUN useradd -m -u 1000 tuoni && chown -R tuoni:tuoni /app
USER tuoni

EXPOSE 9002

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9002/api/health || exit 1

# 启动命令：入口变为 src.app:app
CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.app:app"]
