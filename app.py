#!/usr/bin/env python3
"""
Agent Deploy Web 后端
- 场景1：首次/非首次部署（配置修改、加载镜像、启动服务）
- 场景2：测试提示（引导回终端操作）
- 场景3：配置重置
"""
import os
import re
import shutil
import subprocess
import json
import time
from pathlib import Path

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
import yaml

app = Flask(__name__)
CORS(app)

# 项目根目录（与 docker-compose.yaml 同级）
PROJECT_ROOT = Path(os.getcwd())
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yaml"
CONFIG_FILE = PROJECT_ROOT / "test" / "config.cfg"
DEPLOY_LOG = PROJECT_ROOT / "deploy.log"
TOOLS_DIR = PROJECT_ROOT / "tools"
IMAGES_DIR = PROJECT_ROOT / "images"

# 确保目录存在
TOOLS_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "test").mkdir(parents=True, exist_ok=True)


def read_compose_env():
    """读取 docker-compose.yaml 中 services 下的环境变量（列表形式）"""
    if not COMPOSE_FILE.exists():
        return {}
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


# ---------- 页面 ----------
@app.route('/')
def index():
    return render_template('index.html')


# ---------- 状态接口 ----------
@app.route('/api/state')
def get_state():
    is_first = not DEPLOY_LOG.exists()
    compose_env = read_compose_env()
    cfg_env = read_config_cfg()

    state = {
        "is_first_time": is_first,
        "dify_url": compose_env.get("LOCAL_DIFY_URL", ""),
        "llm_url": compose_env.get("LOCAL_LLM_URL", ""),
        "llm_uid": compose_env.get("LOCAL_LLM_UID", ""),
        "llm_key": compose_env.get("API_KEY", ""),
        "emb_url": compose_env.get("LOCAL_EMB_URL", ""),
        "emb_uid": compose_env.get("LOCAL_EMB_UID", ""),
        "mysql_host": compose_env.get("MYSQL_HOST", ""),
        "mysql_port": compose_env.get("MYSQL_PORT", ""),
        "db_db": compose_env.get("DB_DB", ""),
        "db_user": compose_env.get("DB_USER", ""),
        "db_password": compose_env.get("DB_PASSWORD", ""),
        "db_type": compose_env.get("DB_TYPE", ""),
        "db_schema": compose_env.get("DB_SCHEMA", ""),
        "cfg_llm_url": cfg_env.get("LLM_MODEL_URL", ""),
        "cfg_llm_id": cfg_env.get("LLM_MODEL_ID", ""),
        "cfg_llm_key": cfg_env.get("LLM_MODEL_KEY", ""),
        "cfg_emb_url": cfg_env.get("EMBEDDING_MODEL_URL", ""),
        "cfg_emb_id": cfg_env.get("EMBEDDING_MODEL_ID", ""),
    }
    return jsonify(state)


# ---------- 配置修改 ----------
@app.route('/api/modify', methods=['POST'])
def modify_config():
    data = request.json
    module = data.get('module')  # dify / llm / embedding / db
    values = data.get('values', {})

    compose_updates = {}
    cfg_updates = {}

    try:
        if module == 'dify':
            new_ip_port = values.get('ip_port', '')
            if not new_ip_port:
                return jsonify({"success": False, "error": "IP:端口不能为空"})
            base_url = f"http://{new_ip_port}"
            compose_updates.update({
                "LOCAL_DIFY_URL": f"{base_url}/frameWorkPortal/agent",
                "FILE_UPLOAD_URL": f"{base_url}/agent_proxy",
                "ADMIN_URL": f"{base_url}/agent_proxy",
                "MINIO_INTERNAL_URL": f"{base_url}/szzn-minio",
                "MINIO_EXTERNAL_URL": f"{base_url}/szzn-minio",
            })

        elif module == 'llm':
            llm_url = values.get('url', '')
            llm_uid = values.get('uid', '')
            llm_key = values.get('key', '')
            if not llm_url or not llm_uid:
                return jsonify({"success": False, "error": "LLM URL 和 UID 不能为空"})
            compose_updates.update({
                "LOCAL_LLM_URL": llm_url,
                "LOCAL_LLM_UID": llm_uid,
                "API_KEY": llm_key if llm_key else "xxx"
            })
            cfg_updates.update({
                "LLM_MODEL_URL": f"{llm_url}/chat/completions",
                "LLM_MODEL_ID": llm_uid,
                "LLM_MODEL_KEY": llm_key if llm_key else ""
            })

        elif module == 'embedding':
            emb_url = values.get('url', '')
            emb_uid = values.get('uid', '')
            if not emb_url or not emb_uid:
                return jsonify({"success": False, "error": "Embedding URL 和 UID 不能为空"})
            compose_updates.update({
                "LOCAL_EMB_URL": emb_url,
                "LOCAL_EMB_UID": emb_uid
            })
            cfg_updates.update({
                "EMBEDDING_MODEL_URL": emb_url,
                "EMBEDDING_MODEL_ID": emb_uid
            })

        elif module == 'db':
            host = values.get('host', '')
            port = values.get('port', '')
            if host:
                compose_updates["MYSQL_HOST"] = host
            if port:
                compose_updates["MYSQL_PORT"] = port
            if values.get('db_db'):
                compose_updates["DB_DB"] = values['db_db']
            if values.get('db_user'):
                compose_updates["DB_USER"] = values['db_user']
            if values.get('db_password'):
                compose_updates["DB_PASSWORD"] = values['db_password']
            if values.get('db_type'):
                compose_updates["DB_TYPE"] = values['db_type']
            if values.get('db_schema'):
                compose_updates["DB_SCHEMA"] = values['db_schema']
        else:
            return jsonify({"success": False, "error": f"未知模块: {module}"})

        if compose_updates:
            write_compose_env(compose_updates)
        if cfg_updates:
            write_config_cfg(cfg_updates)

        return jsonify({"success": True, "message": f"模块 {module} 配置已更新"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------- 部署流程 ----------
@app.route('/api/deploy/load_images', methods=['POST'])
def load_images():
    if not IMAGES_DIR.exists():
        return jsonify({"success": False, "error": "images 目录不存在"})
    image_files = list(IMAGES_DIR.glob("*"))
    if not image_files:
        return jsonify({"success": True, "message": "无镜像文件"})
    results = []
    for img in image_files:
        res = execute_command(f"docker load -i {img}")
        results.append(f"{img.name}: {'成功' if res['success'] else '失败 - ' + res['stderr']}")
    with open(DEPLOY_LOG, 'w') as f:
        f.write(f"load images success at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    return jsonify({"success": True, "message": "\n".join(results)})


@app.route('/api/deploy/backup', methods=['POST'])
def backup_config():
    try:
        shutil.copy2(COMPOSE_FILE, TOOLS_DIR / "docker-compose.yaml.bak")
        if CONFIG_FILE.exists():
            shutil.copy2(CONFIG_FILE, TOOLS_DIR / "config.cfg.bak")
        return jsonify({"success": True, "message": "配置文件备份完成"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/deploy/start_service', methods=['POST'])
def start_service():
    docker_compose_cmd = "docker-compose"
    if shutil.which("docker-compose") is None:
        local_dc = TOOLS_DIR / "docker-compose-Linux-x86_64"
        if local_dc.exists():
            try:
                shutil.copy2(local_dc, "/usr/local/bin/docker-compose")
                os.chmod("/usr/local/bin/docker-compose", 0o755)
            except PermissionError:
                return jsonify({"success": False, "error": "无权复制 docker-compose，请手动执行"})
        else:
            return jsonify({"success": False, "error": "未找到 docker-compose"})

    res = execute_command(f"{docker_compose_cmd} up -d")
    if res["success"]:
        with open(DEPLOY_LOG, 'a') as f:
            f.write(f"服务启动完成 at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        return jsonify({"success": True, "message": "服务启动成功"})
    else:
        return jsonify({"success": False, "error": res["stderr"] or "启动失败"})


# ---------- 测试提示（简化） ----------
@app.route('/api/test/run', methods=['POST'])
def run_test_simple():
    msg = (
        "测试功能请回到终端手动操作，步骤如下：\n"
        "  cd ~/agent_local/test\n"
        "  ./main.sh\n"
        "  根据提示选择 1（模型测试）或 2（业务流程测试）"
    )
    return jsonify({"success": True, "message": msg})


# ---------- 重置 ----------
@app.route('/api/reset', methods=['POST'])
def reset_config():
    confirm = request.json.get('confirm', False)
    if not confirm:
        return jsonify({"success": False, "error": "未确认操作"})
    try:
        if DEPLOY_LOG.exists():
            DEPLOY_LOG.unlink()
        bak_compose = TOOLS_DIR / "docker-compose.yaml.bak"
        bak_cfg = TOOLS_DIR / "config.cfg.bak"
        if bak_compose.exists():
            shutil.copy2(bak_compose, COMPOSE_FILE)
        else:
            return jsonify({"success": False, "error": "未找到 docker-compose.yaml.bak"})
        if bak_cfg.exists():
            shutil.copy2(bak_cfg, CONFIG_FILE)
        return jsonify({"success": True, "message": "服务配置已重置为初始状态"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
