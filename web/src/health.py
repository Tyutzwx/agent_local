#!/usr/bin/env python3
"""
健康检查模块：使用 docker ps 获取当前项目的容器状态
"""
import subprocess
from config_manager import PROJECT_ROOT, PROJECT_NAME


def get_health_status():
    """
    执行健康检查，返回包含 success, overall, containers, running, total 的字典
    """
    project_name = PROJECT_NAME  # 'agent_local'

    try:
        cmd = [
            'docker', 'ps', '-a',
            '--format',
            '{{.Names}}|{{.Status}}|{{.Label "com.docker.compose.project"}}|{{.Label "com.docker.compose.service"}}'
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return {
                "success": False,
                "error": "docker ps 执行失败",
                "detail": result.stderr
            }

        containers = []
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            parts = line.split('|')
            if len(parts) < 4:
                continue
            name, status_raw, proj, service = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
            # 只保留属于当前项目的容器
            # 定义算法组件的目标容器名列表
            target_containers = [
                'agent_websocket_local',
                'planner_release',
                'redis_offline_map',
                'mysql_tars_local',
                'milvus-standalone'
            ]

            # 只保留目标容器
            if name not in target_containers:
                continue

            service_name = service if service else name
            is_up = status_raw.lower().startswith('up')
            containers.append({
                "service": service_name,
                "state": "Up" if is_up else status_raw
            })

        total = len(containers)
        running = sum(1 for c in containers if c["state"].lower().startswith('up'))
        if total == 0:
            overall = "stopped"
        elif running == total:
            overall = "running"
        elif running > 0:
            overall = "partial"
        else:
            overall = "stopped"

        return {
            "success": True,
            "overall": overall,
            "containers": containers,
            "running": running,
            "total": total
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "命令超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}
