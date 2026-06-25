# Agent 算法组件自动化部署控制台

> 将企业大脑 Agent 算法组件的部署从手动 Shell 脚本操作升级为 Web 可视化工具，实现配置管理、镜像加载、服务启停、健康检查的一站式自动化运维。


## 📌 项目背景

在企业大脑私有化交付过程中，Agent 算法组件（包含 Xinference 模型服务、MySQL、Redis、Milvus、Planner、Agent WebSocket 等 5 个微服务）的部署长期依赖手动操作：

- 登录服务器 → 编辑 `docker-compose.yaml` → 逐条 `docker load -i` 加载镜像 → 手动启动容器 → 导入 SQL 和向量数据
- 每次部署耗时约 30 分钟，且容易因配置错误（如 IP 格式不对、YAML 缩进错误）导致失败

**本项目将整个流程 Web 化**，用户通过浏览器即可完成部署，部署时间压缩至 10 分钟以内。


## ✨ 核心功能

| 功能 | 说明 |
| :--- | :--- |
| **配置管理** | Web 表单填写 Dify/LLM/Embedding/数据库配置，自动生成 `docker-compose.yaml` 和 `test/config.cfg` |
| **镜像加载** | 一键加载 `images/` 目录下所有 Docker 镜像（支持批量 `.tar`） |
| **服务启停** | 一键执行 `docker-compose up -d`，支持首次部署和配置修改后重启 |
| **流式日志** | 部署过程实时推送日志（备份 → 加载镜像 → 启动服务），每一步都可见 |
| **健康检查** | 自动轮询当前 Compose 项目的容器状态，显示运行/异常/停止 |
| **配置重置** | 一键恢复至初始备份配置（二次确认） |
| **表单校验** | 统一错误收集，编号列表展示，拦截错误输入 |
| **操作防误** | 非首次部署中，配置修改未保存时拦截“重启服务”操作 |


## 🏗️ 技术架构

### 后端

- **框架**：Flask + Gunicorn
- **模块化拆分**（从单体重构为模块化架构）：
  - `app_jieou.py`：**主入口文件**（路由注册），当前生产环境使用的版本
  - `config_manager.py`：配置读写（`docker-compose.yaml` / `test/config.cfg`）
  - `docker_manager.py`：Docker 操作（镜像加载、服务启停、命令执行）
  - `health.py`：容器健康检查（`docker ps` + 标签过滤）
  - `deploy.py`：流式部署生成器（备份 → 加载镜像 → 启动）
- `app_zong.py`：解耦前的单体版本（全部代码集中在一个文件），保留作为历史参考，当前未使用
- **流式响应**：Python 生成器 + `stream_with_context` + `subprocess.Popen`（`bufsize=1` 行缓冲）
- **YAML 安全修改**：正则替换环境变量值，保留注释和格式

### 前端

- **纯原生**：HTML5 + CSS3 + JavaScript (ES6)
- **静态资源分离**：`static/css/style.css`、`static/js/app.js`
- **流式数据接收**：`fetch` + `ReadableStream` 逐行解析 JSON 日志

### 部署

- **生产服务**：Gunicorn 监听 9002 端口
- **后台运行**：`nohup` 实现退出终端后服务不中断
- **开机自启**：`crontab @reboot` 实现服务器重启后自动拉起
- **调试模式**：Flask 开发服务器监听 `127.0.0.1:5002`（仅本机）


## 📁 项目结构

```
agent_local/
├── app_jieou.py               # ✅ 主入口文件（解耦后版本，生产用）
├── app_zong.py                # 解耦前的单体版本（历史参考，当前未使用）
├── config_manager.py          # 配置读写模块（docker-compose.yaml / config.cfg）
├── docker_manager.py          # Docker 操作模块
├── health.py                  # 健康检查模块
├── deploy.py                  # 流式部署生成器
├── static/
│   ├── css/
│   │   └── style.css          # 全局样式
│   └── js/
│       └── app.js             # 前端逻辑（校验、流式、健康检查）
├── templates/
│   └── index.html             # HTML 骨架
├── test/
│   ├── config.cfg             # 测试配置文件
│   └── main.sh                # 原有 Shell 测试脚本（保留）
├── tools/                     # 备份文件及工具二进制
├── images/                    # Docker 镜像 tar 包
├── gunicorn.conf.py           # Gunicorn 生产配置
├── requirements.txt           # Python 依赖
└── README.md                  # 本文档
```

### 文件说明

| 文件 | 说明 |
| :--- | :--- |
| `app_jieou.py` | **✅ 当前运行的主入口**，包含完整的路由注册和启动逻辑 |
| `app_zong.py` | 解耦前的单体版本（全部代码在同一个文件中），**当前未使用**，仅作历史参考 |
| `config_manager.py` | 全局路径常量 + 配置读写（`read_compose_env`、`write_compose_env` 等） |
| `docker_manager.py` | Docker 操作封装（`load_images`、`start_service`、`backup_config`、`execute_command`） |
| `health.py` | 健康检查核心逻辑（`get_health_status`） |
| `deploy.py` | 流式部署生成器（`generate_deploy_stream`、`generate_restart_stream`） |


## 🚀 快速开始

### 环境要求

- Linux (x86_64)
- Python 3.8+
- Docker & Docker Compose（当前用户需有执行权限）
- 项目目录与 `docker-compose.yaml` 同级

### 安装依赖

```bash
cd /data/tuoni/agent_local
pip install -r requirements.txt
```

### 启动服务

#### 生产模式（Gunicorn）

```bash
gunicorn -c gunicorn.conf.py app_jieou:app
# 访问 http://服务器IP:9002
```

#### 后台持久化运行（退出终端后服务持续运行）

```bash
nohup gunicorn -c gunicorn.conf.py app_jieou:app > /dev/null 2>&1 &
```

- `nohup`：忽略挂断信号（SIGHUP），退出终端后进程不被终止
- `&`：将进程放入后台运行
- `> /dev/null 2>&1`：标准输出和标准错误重定向到 `/dev/null`，避免产生 `nohup.out` 日志文件

#### 开机自启

通过 crontab 的 `@reboot` 机制实现服务器重启后自动拉起服务：

```bash
crontab -e
# 添加以下内容
@reboot sleep 10 && cd /data/tuoni/agent_local && nohup gunicorn -c gunicorn.conf.py app_jieou:app > /dev/null 2>&1 &
```

`sleep 10` 等待 Docker 等基础服务就绪后再启动 Gunicorn，避免依赖服务未就绪导致启动失败。

#### 调试模式（仅本机访问）

```bash
python3 app_jieou.py
# 访问 http://127.0.0.1:5002
```


## 📖 使用指南

### 首次部署

1. 进入 **“算法服务初始化启动”** 场景
2. 填写以下配置（数据库可选）：
   - 企业大脑地址（`IP:端口`）
   - LLM 模型 URL、UID、API_KEY
   - Embedding 模型 URL、UID
   - 数据库（可选）
3. 点击 **“加载镜像并启动服务”**
4. 系统自动执行：
   - 校验表单 → 保存配置 → 备份旧配置 → 加载镜像 → 启动服务
   - 实时显示日志，每一步都可见
5. 部署成功后弹窗提示，返回首页

### 非首次部署（配置修改）

1. 进入部署场景，页面显示三个独立修改按钮
2. 点击对应模块的 **“保存”** 按钮
   - 输入格式错误时会统一列出所有问题
   - 保存成功后，配置写入文件
3. 点击底部 **“重启服务”** 按钮
   - 若有未保存的修改，系统拦截并提示
   - 无修改时，执行 `docker-compose up -d` 并实时推送日志

### 健康检查

页面顶部状态条自动每 3 秒刷新，显示当前项目容器的整体状态及每个容器的详细状态。

### 配置重置

在重置场景中点击 **“执行重置”**，并二次确认，将删除 `deploy.log` 并用 `tools/` 下的备份文件恢复配置。


## 🔌 API 接口

| 端点 | 方法 | 功能 |
| :--- | :--- | :--- |
| `/` | GET | 返回前端页面 |
| `/api/state` | GET | 返回当前配置及首次/非首次状态 |
| `/api/modify` | POST | 修改指定模块配置（dify/llm/embedding/db） |
| `/api/deploy/backup` | POST | 备份配置文件到 `tools/` |
| `/api/deploy/load_images` | POST | 同步加载 `images/` 下所有镜像 |
| `/api/deploy/start_service` | POST | 同步启动服务 |
| `/api/deploy/stream` | POST | **流式完整部署**（备份→加载→启动） |
| `/api/service/restart/stream` | POST | **流式重启服务** |
| `/api/health` | GET | 返回当前项目的容器健康状态 |
| `/api/test/run` | POST | 返回测试操作指引 |
| `/api/reset` | POST | 重置配置（需 `confirm: true`） |


## 🛠️ 技术亮点

### 1. 流式部署日志

- 使用 Python 生成器 `yield` 逐行产出日志，Flask `stream_with_context` 保持长连接
- `subprocess.Popen` + `bufsize=1`（行缓冲）实时捕获 `docker` 命令输出
- 前端 `ReadableStream` 逐行解析并渲染，实现“边执行边展示”

### 2. YAML 配置安全修改

- 正则替换精准定位环境变量行，只改值不破坏注释、缩进、空行
- 避免 `yaml.dump` 导致文件格式化重写，保留用户自定义结构

### 3. 健康检查兼容性

- 使用 `docker ps` + 容器标签（`com.docker.compose.project`）过滤
- 解决旧版 Docker Compose 不支持 `--format` 自定义分隔符的问题

### 4. 前端表单校验

- 统一错误收集，编号列表展示，不遇错即停
- 实时清除单个输入框错误（输入时自动去掉红色边框）
- 非首次部署中，配置修改未保存时拦截“重启服务”

### 5. 从单体到模块化的架构演进

- 原有 500+ 行单体代码（`app_zong.py`）拆分为 5 个独立模块
- 配置、Docker、健康检查、部署逻辑各自独立，便于测试和扩展
- 前端静态资源从 400+ 行内联代码分离到 `static/` 目录


## 📝 配置说明

### `docker-compose.yaml` 环境变量

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
| `DB_DB` | 数据库名 |
| `DB_USER` | 数据库用户 |
| `DB_PASSWORD` | 数据库密码 |
| `DB_TYPE` | 数据库类型（mysql/dm/kb） |
| `DB_SCHEMA` | 数据库 Schema |

### `test/config.cfg` 测试配置

| 变量名 | 说明 |
| :--- | :--- |
| `LLM_MODEL_URL` | LLM 测试地址（自动补全 `/chat/completions`） |
| `LLM_MODEL_ID` | LLM 模型 ID |
| `LLM_MODEL_KEY` | LLM API Key |
| `EMBEDDING_MODEL_URL` | Embedding 测试地址 |
| `EMBEDDING_MODEL_ID` | Embedding 模型 ID |


## 🧪 测试与排错

### 服务管理速查

| 操作 | 命令 |
| :--- | :--- |
| 后台启动 | `nohup gunicorn -c gunicorn.conf.py app_jieou:app > /dev/null 2>&1 &` |
| 停止服务 | `pkill -u tuoni -f "gunicorn.*app_jieou:app"` |
| 确认运行 | `ps aux \| grep "gunicorn.*app_jieou:app" \| grep -v grep` |
| 确认端口 | `ss -tlnp \| grep 9002` |
| 查看错误日志 | `tail -f /data/tuoni/agent_local/gunicorn_error.log` |
| 平滑重启 | `kill -HUP $(cat /data/tuoni/agent_local/gunicorn.pid)` |

### 常见问题

| 现象 | 可能原因 | 解决 |
| :--- | :--- | :--- |
| 页面状态一直“检查中” | `/api/health` 未响应 | 检查 Docker 是否运行，或 Gunicorn 是否正常 |
| 流式日志不滚动 | `bufsize=1` 未生效 | 检查 `deploy.py` 中 `Popen` 参数 |
| 配置修改后未生效 | 未点击“重启服务” | 必须重启容器才能加载新配置 |
| 镜像加载失败 | 镜像文件损坏或格式不对 | 重新导出镜像，确保为 `.tar` |


## 🤝 贡献与开发

如需本地开发：

1. 克隆仓库
2. 修改代码后，调试模式运行：
   ```bash
   python3 app_jieou.py
   ```
3. 提交前确保所有 API 正常，前端静态资源已更新
4. 提交规范：`feat:` / `fix:` / `refactor:` / `docs:` 等前缀

