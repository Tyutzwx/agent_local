#!/usr/bin/env python3
"""
Agent Deploy Web 后端 - 720 版本（适配 734 前端逻辑）
"""
import shutil
import subprocess
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS

from config_manager import (
    read_compose_env, read_config_cfg,
    write_compose_env, write_config_cfg,
    DEPLOY_LOG, COMPOSE_FILE, CONFIG_FILE, TOOLS_DIR
)
from docker_manager import load_images, start_service, backup_config
from health import get_health_status
from deploy import generate_deploy_stream, generate_restart_stream

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state')
def get_state():
    is_first = not DEPLOY_LOG.exists() or DEPLOY_LOG.stat().st_size == 0
    compose_env = read_compose_env()
    cfg_env = read_config_cfg()

    state = {
        "is_first_time": is_first,
        # 从 docker-compose.yaml 读取（720 版本键名）
        "dify_url": compose_env.get("LOCAL_DIFY_URL", ""),
        "llm_url": compose_env.get("LOCAL_LLM_URL", ""),
        "llm_uid": compose_env.get("LOCAL_LLM_UID", ""),
        "llm_key": compose_env.get("LOCAL_LLM_KEY", ""),
        "emb_url": compose_env.get("LOCAL_EMB_URL", ""),
        "emb_uid": compose_env.get("LOCAL_EMB_UID", ""),
        "mysql_host": compose_env.get("MYSQL_HOST", ""),
        "mysql_port": compose_env.get("MYSQL_PORT", ""),
        "db_db": compose_env.get("DB_DB", ""),
        "db_user": compose_env.get("DB_USER", ""),
        "db_password": compose_env.get("DB_PASSWORD", ""),
        "db_type": compose_env.get("DB_TYPE", ""),
        "db_schema": compose_env.get("DB_SCHEMA", ""),
        # 从 config.cfg 读取（720 版本键名）
        "cfg_llm_url": cfg_env.get("LLM_MODEL_URL", ""),
        "cfg_llm_id": cfg_env.get("LLM_MODEL_ID", ""),
        "cfg_llm_key": cfg_env.get("LLM_MODEL_KEY", ""),
        "cfg_emb_url": cfg_env.get("EMBEDDING_MODEL_URL", ""),
        "cfg_emb_id": cfg_env.get("EMBEDDING_MODEL_ID", ""),
    }
    return jsonify(state)


@app.route('/api/modify', methods=['POST'])
def modify_config():
    data = request.json
    module = data.get('module')
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
                "LOCAL_LLM_KEY": llm_key if llm_key else "xxx"
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


@app.route('/api/deploy/load_images', methods=['POST'])
def load_images_route():
    success, msg = load_images()
    return jsonify({"success": success, "message": msg})


@app.route('/api/deploy/backup', methods=['POST'])
def backup_config_route():
    success, msg = backup_config()
    return jsonify({"success": success, "message": msg})


@app.route('/api/deploy/start_service', methods=['POST'])
def start_service_route():
    success, msg = start_service()
    return jsonify({"success": success, "message": msg})


@app.route('/api/deploy/stream', methods=['POST'])
def deploy_stream():
    return Response(stream_with_context(generate_deploy_stream()), mimetype='text/plain')


@app.route('/api/service/restart/stream', methods=['POST'])
def restart_service_stream():
    return Response(stream_with_context(generate_restart_stream()), mimetype='text/plain')


@app.route('/api/health')
def health_check():
    return jsonify(get_health_status())


@app.route('/api/test/run', methods=['POST'])
def run_test_simple():
    msg = (
        "测试功能请回到终端手动操作，步骤如下：\n"
        "  cd ~/agent_local/algorithm/test\n"
        "  ./main.sh\n"
        "  根据提示选择 1（模型测试）或 2（业务流程测试）"
    )
    return jsonify({"success": True, "message": msg})


@app.route('/api/reset', methods=['POST'])
def reset_config():
    confirm = request.json.get('confirm', False)
    if not confirm:
        return jsonify({"success": False, "error": "未确认操作"})
    try:
        # 处理 deploy.log
        if DEPLOY_LOG.exists():
            try:
                DEPLOY_LOG.unlink()
            except Exception:
                # 删除失败则清空内容
                with open(DEPLOY_LOG, 'w') as f:
                    f.write('')
        # 恢复备份配置
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
    app.run(host='127.0.0.1', port=5002, debug=False)
