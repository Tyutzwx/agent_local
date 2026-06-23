#!/usr/bin/env python3
"""
配置管理模块：负责读写 docker-compose.yaml 和 test/config.cfg，
并定义项目路径常量。
"""
import re
from pathlib import Path

# 项目根目录（与 docker-compose.yaml 同级）
PROJECT_ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yaml"
CONFIG_FILE = PROJECT_ROOT / "test" / "config.cfg"
DEPLOY_LOG = PROJECT_ROOT / "deploy.log"
TOOLS_DIR = PROJECT_ROOT / "tools"
IMAGES_DIR = PROJECT_ROOT / "images"


def read_compose_env():
    """读取 docker-compose.yaml 中 services 下的环境变量（列表形式）"""
    if not COMPOSE_FILE.exists():
        return {}
    import yaml
    with open(COMPOSE_FILE, 'r') as f:
        data = yaml.safe_load(f) or {}
    services = data.get('services', {})
    env_dict = {}
    for svc in services.values():
        if 'environment' in svc:
            for item in svc['environment']:
                if '=' in str(item):
                    k, v = item.split('=', 1)
                    env_dict[k.strip()] = v.strip()
    return env_dict


def write_compose_env(env_updates: dict):
    """修改 docker-compose.yaml 中已存在的环境变量（不新增）"""
    if not COMPOSE_FILE.exists():
        raise FileNotFoundError("docker-compose.yaml not found")
    with open(COMPOSE_FILE, 'r') as f:
        content = f.read()
    for key, value in env_updates.items():
        pattern = re.compile(rf'^(\s*-?\s*{re.escape(key)}=)(.*?)(\s*)$', re.MULTILINE)
        if pattern.search(content):
            content = pattern.sub(rf'\g<1>{value}\g<3>', content)
    with open(COMPOSE_FILE, 'w') as f:
        f.write(content)


def read_config_cfg():
    """读取 test/config.cfg 中的键值对"""
    cfg = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    cfg[k.strip()] = v.strip()
    return cfg


def write_config_cfg(updates: dict):
    """覆盖或追加更新 test/config.cfg"""
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={v}\n" for k, v in updates.items()]
        with open(CONFIG_FILE, 'w') as f:
            f.writelines(lines)
        return

    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()

    new_lines = []
    updated_keys = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(CONFIG_FILE, 'w') as f:
        f.writelines(new_lines)
