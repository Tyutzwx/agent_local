#!/usr/bin/env python3
"""
部署流程生成器：备份 → 加载镜像 → 启动服务，流式输出日志

本模块负责 Agent 算法组件部署的核心流程编排，包括：
- 配置备份
- Docker 镜像加载
- docker-compose 服务启动

所有函数均为生成器（Generator），配合 Flask 的 stream_with_context 实现
实时日志推送。关键特性：无论前端是否断开连接，子进程都会被正确回收，
避免孤儿进程导致的系统资源泄漏。
"""
import json
import shutil
import subprocess
import time
from config_manager import COMPOSE_FILE, CONFIG_FILE, TOOLS_DIR, IMAGES_DIR, DEPLOY_LOG, PROJECT_ROOT
from docker_manager import get_docker_compose_cmd


def generate_deploy_stream():
    """
    完整部署流程生成器
    
    步骤：
    1. 备份当前 docker-compose.yaml 和 config.cfg
    2. 加载 images/ 目录下所有 Docker 镜像
    3. 执行 docker-compose up -d 启动服务
    
    Yields:
        每行一个 JSON 格式的日志消息：{"step": "...", "status": "info|success|error|warning|log"}
    
    异常处理：
        - GeneratorExit: 前端断开连接时触发，自动清理子进程
        - finally: 确保无论发生什么，子进程都被回收
    """
    process = None  # 提前定义，确保 finally 块能访问
    
    try:
        # ==================== 1. 备份配置 ====================
        yield json.dumps({"step": "正在备份配置文件...", "status": "info"}) + "\n"
        try:
            shutil.copy2(COMPOSE_FILE, TOOLS_DIR / "docker-compose.yaml.bak")
            if CONFIG_FILE.exists():
                shutil.copy2(CONFIG_FILE, TOOLS_DIR / "config.cfg.bak")
            yield json.dumps({"step": "备份完成", "status": "success"}) + "\n"
        except Exception as e:
            yield json.dumps({"step": f"备份失败: {str(e)}", "status": "error"}) + "\n"
            return

        # ==================== 2. 加载镜像 ====================
        yield json.dumps({"step": "开始加载 Docker 镜像...", "status": "info"}) + "\n"
        
        if not IMAGES_DIR.exists():
            yield json.dumps({"step": "images 目录不存在，跳过镜像加载", "status": "warning"}) + "\n"
        else:
            image_files = list(IMAGES_DIR.glob("*"))
            if not image_files:
                yield json.dumps({"step": "images 目录为空，跳过镜像加载", "status": "warning"}) + "\n"
            else:
                for img in image_files:
                    result = subprocess.run(
                        ["docker", "load", "-i", str(img)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        yield json.dumps({"step": f"成功加载 {img.name}", "status": "success"}) + "\n"
                    else:
                        yield json.dumps({"step": f"加载 {img.name} 失败: {result.stderr}", "status": "error"}) + "\n"
                        return

        # ==================== 3. 启动服务 ====================
        yield json.dumps({"step": "正在启动服务 (docker-compose up -d)...", "status": "info"}) + "\n"
        
        cmd = get_docker_compose_cmd()
        if cmd is None:
            yield json.dumps({"step": "未找到 docker-compose", "status": "error"}) + "\n"
            return

        # 启动子进程，实时捕获输出
        process = subprocess.Popen(
            [cmd, "up", "-d"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # 行缓冲，确保每行输出立即读取
        )

        # 逐行读取并推送
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

    except GeneratorExit:
        # ==================== 前端断开连接，清理子进程 ====================
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise  # 重新抛出，让 Flask 正常处理连接断开

    finally:
        # ==================== 双重保险：无论如何都清理 ====================
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def generate_restart_stream():
    """
    仅重启服务（不执行备份和加载镜像）
    
    适用场景：
    - 配置修改后需要重启服务生效
    - 非首次部署时快速重启
    
    Yields:
        每行一个 JSON 格式的日志消息
    
    异常处理：
        - GeneratorExit: 前端断开连接时触发，自动清理子进程
        - finally: 确保无论发生什么，子进程都被回收
    """
    process = None

    try:
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

    except GeneratorExit:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise

    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
