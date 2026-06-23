#!/usr/bin/env python3
"""
部署流程生成器：备份 → 加载镜像 → 启动服务，流式输出日志
"""
import json
import shutil
import subprocess
import time
from config_manager import COMPOSE_FILE, CONFIG_FILE, TOOLS_DIR, IMAGES_DIR, DEPLOY_LOG, PROJECT_ROOT
from docker_manager import get_docker_compose_cmd


def generate_deploy_stream():
    """生成器：完整部署流程（备份 → 加载镜像 → 启动服务）"""
    # 1. 备份
    yield json.dumps({"step": "正在备份配置文件...", "status": "info"}) + "\n"
    try:
        shutil.copy2(COMPOSE_FILE, TOOLS_DIR / "docker-compose.yaml.bak")
        if CONFIG_FILE.exists():
            shutil.copy2(CONFIG_FILE, TOOLS_DIR / "config.cfg.bak")
        yield json.dumps({"step": "备份完成", "status": "success"}) + "\n"
    except Exception as e:
        yield json.dumps({"step": f"备份失败: {str(e)}", "status": "error"}) + "\n"
        return

    # 2. 加载镜像
    yield json.dumps({"step": "开始加载 Docker 镜像...", "status": "info"}) + "\n"
    if IMAGES_DIR.exists():
        image_files = list(IMAGES_DIR.glob("*"))
        if image_files:
            for img in image_files:
                result = subprocess.run(["docker", "load", "-i", str(img)], capture_output=True, text=True)
                if result.returncode == 0:
                    yield json.dumps({"step": f"成功加载 {img.name}", "status": "success"}) + "\n"
                else:
                    yield json.dumps({"step": f"加载 {img.name} 失败: {result.stderr}", "status": "error"}) + "\n"
                    return
        else:
            yield json.dumps({"step": "images 目录为空，跳过镜像加载", "status": "warning"}) + "\n"
    else:
        yield json.dumps({"step": "images 目录不存在，跳过镜像加载", "status": "warning"}) + "\n"

    # 3. 启动服务
    yield json.dumps({"step": "正在启动服务 (docker-compose up -d)...", "status": "info"}) + "\n"
    cmd = get_docker_compose_cmd()
    if cmd is None:
        yield json.dumps({"step": "未找到 docker-compose", "status": "error"}) + "\n"
        return

    process = subprocess.Popen(
        [cmd, "up", "-d"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in iter(process.stdout.readline, ''):
        if line.strip():
            yield json.dumps({"step": line.strip(), "status": "log"}) + "\n"
    process.wait()
    if process.returncode == 0:
        with open(DEPLOY_LOG, 'a') as f:
            f.write(f"服务启动完成 at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        yield json.dumps({"step": "🎉 服务启动成功！", "status": "success"}) + "\n"
    else:
        yield json.dumps({"step": "❌ 服务启动失败，请检查日志", "status": "error"}) + "\n"


def generate_restart_stream():
    """生成器：仅重启服务（docker-compose up -d）"""
    yield json.dumps({"step": "正在重启服务...", "status": "info"}) + "\n"
    cmd = get_docker_compose_cmd()
    if cmd is None:
        yield json.dumps({"step": "未找到 docker-compose", "status": "error"}) + "\n"
        return

    process = subprocess.Popen(
        [cmd, "up", "-d"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in iter(process.stdout.readline, ''):
        if line.strip():
            yield json.dumps({"step": line.strip(), "status": "log"}) + "\n"
    process.wait()
    if process.returncode == 0:
        with open(DEPLOY_LOG, 'a') as f:
            f.write(f"服务重启完成 at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        yield json.dumps({"step": "✅ 服务重启成功", "status": "success"}) + "\n"
    else:
        yield json.dumps({"step": "❌ 服务重启失败", "status": "error"}) + "\n"
