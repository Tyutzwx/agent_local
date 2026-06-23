# Agent 部署控制台

将原本基于终端交互的部署脚本迁移为 Web 图形界面，在浏览器中完成企业大脑与智能体服务的配置、部署、测试引导和状态监控。

---

## 功能概览

- **首次部署**：填写完整配置（企业大脑地址、LLM、Embedding、数据库），一键加载镜像并启动服务，实时显示每一步日志。
- **非首次部署**：独立修改 Dify/LLM/Embedding 配置，保存后重启服务生效。
- **健康检查**：自动轮询当前 Compose 项目的容器状态，实时展示运行/停止/部分异常。
- **流式部署日志**：点击部署或重启，日志区域逐行推送操作进度（备份 → 加载镜像 → 启动服务），不再长时间无响应。
- **配置重置**：一键恢复至初始备份配置（需二次确认）。
- **测试指引**：提供终端测试命令（模型测试/业务流程测试）的复制提示。
- **配置快照**：使用 Git 进行本地版本管理，可随时回滚。

---

## 环境要求

- 操作系统：Linux (x86_64)
- Python：3.8 及以上
- Docker 与 Docker Compose（当前用户需有执行权限，建议加入 `docker` 组）
- 项目目录：需与 `docker-compose.yaml` 位于同一目录（例如 `/data/tuoni/agent_local`）

---

## 项目结构

```
agent_local/
├── app.py                      # Flask 主入口（路由注册）
├── config_manager.py           # 配置文件读写（docker-compose.yaml, config.cfg）
├── docker_manager.py           # Docker 操作（命令执行、镜像加载、服务启停）
├── health.py                   # 容器健康检查逻辑
├── deploy.py                   # 流式部署生成器（备份→加载→启动）
├── static/
│   ├── css/
│   │   └── style.css           # 前端样式
│   └── js/
│       └── app.js              # 前端交互逻辑
├── templates/
│   └── index.html              # HTML 模板（引用静态资源）
├── test/
│   ├── config.cfg              # 测试配置文件（网页修改会同步更新）
│   └── main.sh                 # 测试入口脚本（终端使用）
├── tools/                      # 存放 docker-compose 二进制及备份文件
├── images/                     # Docker 镜像文件（加载到本地）
├── gunicorn.conf.py            # Gunicorn 生产配置文件
├── requirements.txt            # Python 依赖
├── .gitignore                  # Git 忽略规则
└── README.md
```

---

## 安装依赖

在项目根目录下执行：

```bash
python3 -m pip install -r requirements.txt
```

若 `requirements.txt` 不存在，则手动安装：

```bash
python3 -m pip install flask flask-cors pyyaml gunicorn
```

---

## 启动服务

### 方案一：Gunicorn（生产推荐）

#### 1. 手动启动（前台运行，用于调试）

```bash
cd /data/tuoni/agent_local
gunicorn -c gunicorn.conf.py app:app
```

#### 2. 后台持久化运行

```bash
cd /data/tuoni/agent_local
nohup gunicorn -c gunicorn.conf.py app:app > /dev/null 2>&1 &
```

#### 3. 开机自启（可选）

通过 `crontab` 实现：

```bash
crontab -e
# 添加以下内容（注意替换实际路径）
@reboot sleep 10 && cd /data/tuoni/agent_local && nohup gunicorn -c gunicorn.conf.py app:app > /dev/null 2>&1 &
```

#### 4. 服务管理

| 操作               | 命令                                                   |
| ------------------ | ------------------------------------------------------ |
| 查看进程           | `ps aux \| grep gunicorn \| grep -v grep`              |
| 查看端口监听       | `ss -tlnp \| grep 9002`                                |
| 平滑重启           | `kill -HUP $(cat /data/tuoni/agent_local/gunicorn.pid)`|
| 强制停止           | `pkill -u tuoni -f gunicorn`                           |
| 查看错误日志       | `tail -f /data/tuoni/agent_local/gunicorn_error.log`   |
| 查看访问日志       | `tail -f /data/tuoni/agent_local/gunicorn_access.log`  |

#### 5. 访问控制台

浏览器访问：`http://服务器IP:9002`（例如 `http://10.4.2.64:9002`）

---

### 方案二：Flask 开发服务器（仅调试）

```bash
cd /data/tuoni/agent_local
python3 app.py
```

访问：`http://服务器IP:5001`

> 开发服务器仅适合调试，不应用于生产环境。

---

## 功能说明

### 场景一：算法服务初始化启动

- **首次部署**（无 `deploy.log` 文件）：  
  显示完整配置表单（企业大脑地址、LLM、Embedding、数据库），填写后点击“加载镜像并启动服务”。  
  后台执行：备份配置 → 修改配置文件 → 加载 `images/` 目录下的 Docker 镜像 → `docker-compose up -d`。  
  日志区域实时推送每一步进度，无需等待最终结果。

- **非首次部署**：  
  提供三个独立修改按钮（企业大脑地址 / 大语言模型 / Embedding 模型），保存后点击“重启服务”生效。  
  重启过程同样实时显示日志。

### 场景二：模型测试与业务流程测试

网页端提供终端操作提示，复制命令后执行：

```bash
cd ~/agent_local/test
./main.sh
```

根据菜单选择 `1`（模型测试）或 `2`（业务流程测试）。

### 场景三：服务配置重置

点击“执行重置”并二次确认，将：
- 删除 `deploy.log`
- 用 `tools/` 下的备份文件恢复 `docker-compose.yaml` 和 `test/config.cfg`

重置后再次进入部署页面将视为首次部署。

### 健康检查

页面顶部状态栏自动轮询（每 3 秒）当前 Compose 项目的容器运行状态，显示：
- ✅ 运行中（全部容器 Up）
- ⚠️ 部分异常（部分容器非 Up）
- ❌ 已停止（无容器运行或全部停止）

鼠标悬停或查看详情可查看每个容器的具体状态。

---

## API 端点

| 端点                                | 方法   | 功能                                   |
| ----------------------------------- | ------ | -------------------------------------- |
| `/`                                 | GET    | 返回前端页面                           |
| `/api/state`                        | GET    | 返回当前配置及首次/非首次状态          |
| `/api/modify`                       | POST   | 修改指定模块（dify/llm/embedding/db）  |
| `/api/deploy/backup`                | POST   | 备份当前配置文件到 `tools/`            |
| `/api/deploy/load_images`           | POST   | 加载 `images/` 下所有镜像（同步）      |
| `/api/deploy/start_service`         | POST   | 启动服务（同步）                       |
| `/api/deploy/stream`                | POST   | 流式执行完整部署（备份→加载→启动）     |
| `/api/service/restart/stream`       | POST   | 流式重启服务                           |
| `/api/health`                       | GET    | 返回当前 Compose 项目的容器健康状态    |
| `/api/test/run`                     | POST   | 返回测试操作指引                       |
| `/api/reset`                        | POST   | 重置配置（需 `confirm: true`）         |

---

## 配置说明

- **`docker-compose.yaml`**：环境变量通过 `services.*.environment` 管理，网页修改会通过正则替换已有的键值。
- **`test/config.cfg`**：测试模块的配置文件，与 `docker-compose.yaml` 中的 LLM/Embedding 信息保持同步。
- **`tools/`**：存放 `docker-compose` 二进制文件及自动备份（`*.bak`）。
- **`images/`**：存放 `.tar` 镜像文件，部署时自动加载。

---

## 常见问题

**Q: 网页访问无响应？**  
- 检查 Gunicorn 是否运行：`ps aux | grep gunicorn`
- 检查端口监听：`ss -tlnp | grep 9002`
- 查看错误日志：`tail -f gunicorn_error.log`

**Q: 执行 Docker 命令提示权限不足？**  
将当前用户加入 `docker` 组（需 `sudo` 权限）：
```bash
sudo usermod -aG docker $USER
# 重新登录生效
```

**Q: 修改配置后服务未生效？**  
必须重启服务（网页点击“重启服务”或执行 `docker-compose down && docker-compose up -d`）。

**Q: 状态栏显示“无法获取状态”？**  
检查 Docker 是否运行，以及当前用户是否有执行 `docker ps` 的权限。如果 `docker ps` 正常，则可能是后端健康检查模块未正确加载，查看 Gunicorn 错误日志。

**Q: 如何更新代码？**  
1. 拉取最新代码（若使用 Git）或替换文件。
2. 若修改了后端，重启 Gunicorn：`pkill -u tuoni -f gunicorn && nohup gunicorn -c gunicorn.conf.py app:app > /dev/null 2>&1 &`
3. 若修改了前端静态资源，只需强制刷新浏览器（`Ctrl+F5`）。

**Q: 如何回滚配置？**  
- 使用 Git 回滚代码版本（本地已提交历史）。
- 或使用 `tools/` 下的备份文件手动覆盖。

---

## 开发与维护

- 后端模块已拆分为独立文件，便于单元测试和功能扩展。
- 前端静态资源独立，修改样式或脚本无需修改模板。
- 流式部署接口支持逐步扩展（如增加更多步骤或自定义校验）。

---
