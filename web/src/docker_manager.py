#!/usr/bin/env python3
"""
Docker 操作模块：执行命令、加载镜像、启动服务、备份配置等
"""
import os
import shutil
import subprocess
import time
from config_manager import PROJECT_ROOT, TOOLS_DIR, IMAGES_DIR, DEPLOY_LOG


def execute_command(cmd, cwd=None, timeout=300):
    """执行 shell 命令，返回结果字典"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "命令执行超时", "code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "code": -1}


def get_docker_compose_cmd():
    """返回可用的 docker-compose 命令路径（系统或本地）"""
    if shutil.which("docker-compose") is not None:
        return "docker-compose"
    local_dc = TOOLS_DIR / "docker-compose-Linux-x86_64"
    if local_dc.exists():
        # 尝试复制到系统路径（有权限时）
        try:
            shutil.copy2(local_dc, "/usr/local/bin/docker-compose")
            os.chmod("/usr/local/bin/docker-compose", 0o755)
            return "docker-compose"
        except PermissionError:
            # 无权限则使用本地路径
            return str(local_dc)
    return None


def load_images():
    """加载 images 目录下的所有 Docker 镜像，返回 (success, message)"""
    if not IMAGES_DIR.exists():
        return False, "images 目录不存在"
    image_files = list(IMAGES_DIR.glob("*"))
    if not image_files:
        return True, "无镜像文件"
    results = []
    for img in image_files:
        res = execute_command(f"docker load -i {img}")
        results.append(f"{img.name}: {'成功' if res['success'] else '失败 - ' + res['stderr']}")
    with open(DEPLOY_LOG, 'w') as f:
        f.write(f"load images success at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    return True, "\n".join(results)


def start_service():
    """启动服务（docker-compose up -d），返回 (success, message)"""
    cmd = get_docker_compose_cmd()
    if cmd is None:
        return False, "未找到 docker-compose"
    res = execute_command(f"{cmd} up -d")
    if res["success"]:
        with open(DEPLOY_LOG, 'a') as f:
            f.write(f"服务启动完成 at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        return True, "服务启动成功"
    else:
        return False, res["stderr"] or "启动失败"


def backup_config():
    """备份当前配置文件到 tools/ 目录"""
    from config_manager import COMPOSE_FILE, CONFIG_FILE
    try:
        shutil.copy2(COMPOSE_FILE, TOOLS_DIR / "docker-compose.yaml.bak")
        if CONFIG_FILE.exists():
            shutil.copy2(CONFIG_FILE, TOOLS_DIR / "config.cfg.bak")
        return True, "配置文件备份完成"
    except Exception as e:
        return False, str(e)
