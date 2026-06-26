# Agent 算法组件自动化部署控制台

> 将企业大脑 Agent 算法组件的部署从手动 Shell 脚本操作升级为 Web 可视化工具，实现配置管理、镜像加载、服务启停、健康检查的一站式自动化运维。


## 📌 项目背景

在企业大脑私有化交付过程中，Agent 算法组件（包含 Xinference 模型服务、MySQL、Redis、Milvus、Planner、Agent WebSocket 等 5 个微服务）的部署长期依赖手动操作：

- 登录服务器 → 编辑 `docker-compose.yaml` → 逐条 `docker load -i` 加载镜像 → 手动启动容器 → 导入 SQL 和向量数据
- 每次部署耗时约 30 分钟，且容易因配置错误导致失败

**本项目将整个流程 Web 化**，用户通过浏览器即可完成部署，部署时间压缩至 10 分钟以内。


## 🎯 核心功能

| 功能 | 说明 |
| :--- | :--- |
| **配置管理** | Web 表单填写 Dify/LLM/Embedding/数据库配置，自动生成配置文件 |
| **镜像加载** | 一键加载 `algorithm/images/` 目录下所有 Docker 镜像 |
| **服务启停** | 一键执行 `docker-compose up -d`，支持首次部署和配置修改后重启 |
| **流式日志** | 部署过程实时推送日志（备份 → 加载镜像 → 启动服务），每一步都可见 |
| **健康检查** | 自动轮询当前 Compose 项目的容器状态，显示运行/异常/停止 |
| **配置重置** | 一键恢复至初始备份配置（二次确认） |
| **表单校验** | 统一错误收集，编号列表展示，拦截错误输入 |
| **操作防误** | 非首次部署中，配置修改未保存时拦截“重启服务”操作 |


## 🏗️ 技术架构

### 后端

- **框架**：Flask + Gunicorn
- **模块化拆分**：
  - `app.py`：Flask 主入口（路由注册）
  - `config_manager.py`：配置读写（`docker-compose.yaml` / `config.cfg`）
  - `docker_manager.py`：Docker 操作（镜像加载、服务启停）
  - `health.py`：容器健康检查（`docker ps` + 容器名白名单匹配）
  - `deploy.py`：流式部署生成器（备份 → 加载镜像 → 启动）
- **流式响应**：Python 生成器 + `stream_with_context` + `subprocess.Popen`（`bufsize=1` 行缓冲）
- **YAML 安全修改**：正则替换环境变量值，保留注释和格式

### 前端

- **纯原生**：HTML5 + CSS3 + JavaScript (ES6)
- **静态资源分离**：`static/css/style.css`、`static/js/app.js`
- **流式数据接收**：`fetch` + `ReadableStream` 逐行解析 JSON 日志

### 容器化部署

- **容器运行时**：Docker
- **生产服务**：Gunicorn 监听 9002 端口
- **容器编排**：`docker-compose.yaml` 一键启动
- **日志管理**：统一挂载到 `logs/` 目录


## 📁 项目结构

```
agent_local/
├── web/                              # Web 控制台（独立可迁移）
│   ├── src/                          # Python 源代码
│   │   ├── __init__.py
│   │   ├── app.py                    # Flask 主入口
│   │   ├── config_manager.py         # 配置读写 + 路径管理
│   │   ├── docker_manager.py         # Docker 操作
│   │   ├── health.py                 # 健康检查（容器名白名单）
│   │   └── deploy.py                 # 流式部署生成器
│   ├── static/                       # 前端静态资源
│   │   ├── css/style.css
│   │   └── js/app.js
│   ├── templates/                    # HTML 模板
│   │   └── index.html
│   ├── config/                       # 配置文件
│   │   ├── gunicorn.conf.py
│   │   └── requirements.txt
│   ├── Dockerfile                    # 容器镜像构建文件
│   ├── docker-compose.yaml           # 容器编排启动文件
│   └── .dockerignore                 # Docker 构建排除文件
├── algorithm/                        # 算法组件（独立）
│   ├── docker-compose.yaml           # 5 个微服务编排文件
│   ├── images/                       # Docker 镜像 tar 包
│   │   ├── agent_local_deep.tar
│   │   ├── agent_mysql_deep.tar
│   │   ├── agent_planner.tar
│   │   ├── agent_redis.tar
│   │   └── milvus.tar
│   ├── test/                         # 测试脚本
│   │   ├── config.cfg
│   │   ├── main.sh
│   │   ├── llm_test.sh
│   │   ├── embedding_test.sh
│   │   ├── reranker_test.sh
│   │   └── connect_websocket.py
│   └── tools/                        # 工具与备份文件
│       ├── docker-compose-Linux-x86_64
│       ├── docker-compose.yaml.bak
│       └── config.cfg.bak
├── logs/                             # 统一日志目录（运行时生成）
├── deploy.sh                         # 原始部署脚本（已适配新结构）
├── .gitignore
└── README.md
```


## 🚀 快速开始

### 环境要求

| 要求 | 说明 |
| :--- | :--- |
| **Docker** | 已安装 Docker（版本 20.10+） |
| **Docker 权限** | 当前用户在 docker 组中 |
| **端口** | 9002 端口可用（Web 控制台访问） |
| **目录结构** | 按上述项目结构保持完整 |

### 一键启动

```bash
cd /data/tuoni/agent_local/web
docker-compose up -d
```

### 验证

```bash
# 健康检查
curl http://127.0.0.1:9002/api/health

# 访问 Web 界面
# 浏览器打开 http://<服务器IP>:9002
```

### 服务管理

| 操作 | 命令 |
| :--- | :--- |
| **启动** | `cd web && docker-compose up -d` |
| **停止** | `cd web && docker-compose down` |
| **重启** | `cd web && docker-compose restart` |
| **查看日志** | `docker logs -f agent-control` |
| **进入容器** | `docker exec -it agent-control bash` |


## 📖 使用指南

### 首次部署

1. 进入 **“算法服务初始化启动”** 场景
2. 填写企业大脑地址（`IP:端口`）、LLM 配置、Embedding 配置
3. 点击 **“加载镜像并启动服务”**
4. 实时查看部署日志，完成后自动弹窗提示

### 非首次部署（配置修改）

1. 点击对应模块的 **“保存”** 按钮修改配置
2. 点击 **“重启服务”** 使新配置生效

### 健康检查

页面顶部状态条自动每 3 秒刷新，显示 5 个容器的运行状态。

### 配置重置

点击 **“执行重置”** 并二次确认，恢复初始配置并清空 `deploy.log`。


## 🔌 API 接口

| 端点 | 方法 | 功能 |
| :--- | :--- | :--- |
| `/` | GET | 返回前端页面 |
| `/api/state` | GET | 返回当前配置及首次/非首次状态 |
| `/api/modify` | POST | 修改指定模块配置 |
| `/api/deploy/stream` | POST | **流式完整部署** |
| `/api/service/restart/stream` | POST | **流式重启服务** |
| `/api/health` | GET | 返回当前项目的容器健康状态 |
| `/api/reset` | POST | 重置配置（需 `confirm: true`） |


## 🛠️ 技术亮点

### 1. 流式部署日志

- 使用 Python 生成器 `yield` 逐行产出日志
- `subprocess.Popen` + `bufsize=1`（行缓冲）实时捕获 `docker` 命令输出
- 前端 `ReadableStream` 逐行解析并渲染

### 2. YAML 配置安全修改

- 正则替换精准定位环境变量行，只改值不破坏注释、缩进、空行
- 避免 `yaml.dump` 导致文件格式化重写

### 3. 健康检查白名单匹配

- 采用容器名白名单匹配，不依赖 `com.docker.compose.project` 标签
- 兼容性更强，适用于多种部署方式

### 4. 统一日志管理

- 所有日志统一存放在 `logs/` 目录
- 便于查看、备份和清理
- 容器内日志目录挂载到宿主机，重启不丢失


## 🐳 容器化架构详解

### Web 控制台容器

```
web/
├── Dockerfile              # 镜像构建（Python 3.10-slim + 依赖）
├── docker-compose.yaml     # 容器编排（端口映射 + 挂载）
└── src/                    # 应用代码（打包进镜像）
```

### 挂载说明

| 宿主机路径 | 容器内路径 | 说明 |
| :--- | :--- | :--- |
| `/var/run/docker.sock` | `/var/run/docker.sock` | Docker API 调用 |
| `/usr/bin/docker` | `/usr/bin/docker` | Docker CLI |
| `../algorithm/` | `/app/` | 算法组件配置文件 |
| `../logs/` | `/app/logs/` | 统一日志目录 |

### 健康检查

容器内置了健康检查，每 30 秒检查一次，确保服务正常运行：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9002/api/health || exit 1
```


## 📝 配置说明

### `algorithm/docker-compose.yaml` 环境变量

| 变量名 | 说明 |
| :--- | :--- |
| `LOCAL_DIFY_URL` | 企业大脑地址 |
| `LOCAL_LLM_URL` | LLM 模型服务 URL |
| `LOCAL_LLM_UID` | LLM 模型 UID |
| `API_KEY` | LLM API Key |
| `LOCAL_EMB_URL` | Embedding 模型服务 URL |
| `LOCAL_EMB_UID` | Embedding 模型 UID |
| `MYSQL_HOST` | MySQL 主机名 |
| `MYSQL_PORT` | MySQL 端口 |


## 🧪 测试与排错

### 测试脚本运行

```bash
cd /data/tuoni/agent_local/algorithm/test
./main.sh
```

选择 1（模型测试）或 2（业务流程测试）。

### 常用排错命令

```bash
# 查看 Web 容器日志
docker logs agent-control

# 进入 Web 容器调试
docker exec -it agent-control bash

# 查看健康检查结果
curl http://127.0.0.1:9002/api/health

# 查看算法组件容器状态
docker ps | grep -E "agent_websocket|mysql_tars|redis_offline|milvus|planner"

# 查看统一日志目录
tail -f /data/tuoni/agent_local/logs/gunicorn_error.log
```

### 常见问题

| 现象 | 可能原因 | 解决 |
| :--- | :--- | :--- |
| 健康检查返回空列表 | 容器名不在白名单中 | 检查 `health.py` 中的 `target_names` |
| 重置时 `deploy.log` 被占用 | 文件被进程锁定 | 代码已支持删除失败时清空内容 |
| 容器内找不到 `docker` 命令 | 未挂载 Docker 二进制 | 检查 `docker-compose.yaml` 挂载配置 |
| 端口 9002 被占用 | 旧进程未清理 | `ss -tlnp \| grep 9002` 找到并停止 |


## 🔧 传统部署方式（原始脚本）

如果不需要容器化，也可以使用原始脚本：

```bash
cd /data/tuoni/agent_local
./deploy.sh
```

脚本已适配新目录结构，支持：
1. 算法服务初始化启动
2. 模型测试和业务流程测试
3. 服务配置重置


## 📊 重构前后对比

| 对比项 | 重构前 | 重构后 |
| :--- | :--- | :--- |
| **代码组织** | 混乱，文件散落各处 | 清晰分层（`web/` + `algorithm/`） |
| **日志管理** | 散落在根目录 | 统一在 `logs/` 目录 |
| **部署方式** | 手动 `nohup` 启动 | 一键 `docker-compose up -d` |
| **环境一致性** | 依赖宿主机配置 | 容器内环境完全一致 |
| **迁移成本** | 高（需重新配置环境） | 低（只需 Docker） |
| **可维护性** | 低（路径散落） | 高（路径集中管理） |


## 🚀 后续优化方向

| 优先级 | 优化项 | 说明 |
| :--- | :--- | :--- |
| P0 | 镜像推送到私有仓库 | 发布 `agent-control:latest` 到 Harbor |
| P1 | CI/CD 自动化构建 | GitHub Actions 自动构建镜像 |
| P1 | 多环境配置支持 | 开发/测试/生产环境配置分离 |
| P2 | Kubernetes 部署支持 | 编写 Deployment + Service YAML |
| P2 | 监控告警集成 | 接入 Prometheus + Alertmanager |
