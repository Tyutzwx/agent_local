let stateCache = null;
let healthInterval = null;

// ========== 前端表单校验工具 ==========
function isValidIPPort(value) {
    if (!value) return false;
    // 简单校验 IP:端口，允许 0-255 的数字，端口为数字
    const regex = /^(\d{1,3}\.){3}\d{1,3}:\d+$/;
    if (!regex.test(value)) return false;
    // 进一步校验每个数字在 0-255 之间
    const parts = value.split(':');
    const ipParts = parts[0].split('.');
    for (let p of ipParts) {
        const num = parseInt(p, 10);
        if (num < 0 || num > 255) return false;
    }
    return true;
}

function isValidUrl(value) {
    if (!value) return false;
    try {
        const url = new URL(value);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function isNotEmpty(value) {
    return value && value.trim() !== '';
}

function markError(elementId, errorMsg) {
    const el = document.getElementById(elementId);
    if (el) {
        el.style.border = '2px solid #e74c3c';
        el.style.backgroundColor = '#fff5f5';
        let hint = el.parentElement.querySelector('.error-hint');
        if (!hint) {
            hint = document.createElement('div');
            hint.className = 'error-hint';
            hint.style.color = '#e74c3c';
            hint.style.fontSize = '0.8rem';
            hint.style.marginTop = '4px';
            el.parentElement.appendChild(hint);
        }
        hint.textContent = errorMsg;
    }
}

function clearAllErrors() {
    document.querySelectorAll('.error-hint').forEach(el => el.remove());
    document.querySelectorAll('.input-group input, .input-group select').forEach(el => {
        el.style.border = '1px solid #ced4da';
        el.style.backgroundColor = '';
    });
}

// ========== 健康检查 ==========
function startHealthCheck() {
    if (healthInterval) clearInterval(healthInterval);
    healthInterval = setInterval(fetchHealth, 3000);
    fetchHealth();
}
function stopHealthCheck() {
    if (healthInterval) { clearInterval(healthInterval); healthInterval = null; }
}
async function fetchHealth() {
    try {
        const resp = await fetch('/api/health');
        const data = await resp.json();
        const textSpan = document.getElementById('status-text');
        const detailSpan = document.getElementById('status-detail');
        if (data.success) {
            let statusText = '', color = '';
            if (data.overall === 'running') {
                statusText = `✅ 运行中 (${data.running}/${data.total})`;
                color = '#27ae60';
            } else if (data.overall === 'partial') {
                statusText = `⚠️ 部分异常 (${data.running}/${data.total})`;
                color = '#f39c12';
            } else {
                statusText = `❌ 已停止 (${data.running}/${data.total})`;
                color = '#e74c3c';
            }
            textSpan.textContent = statusText;
            textSpan.style.color = color;
            if (data.containers && data.containers.length > 0) {
                const detail = data.containers.map(c => `${c.service}: ${c.state}`).join('; ');
                detailSpan.textContent = detail;
            } else {
                detailSpan.textContent = '无容器';
            }
        } else {
            textSpan.textContent = '❌ 无法获取状态';
            textSpan.style.color = '#e74c3c';
            detailSpan.textContent = data.error || '';
        }
    } catch (e) { /* 忽略网络错误 */ }
}

// ========== 状态管理 ==========
async function fetchState() {
    const resp = await fetch('/api/state');
    stateCache = await resp.json();
}

async function showScene(scene) {
    await fetchState();
    document.getElementById('view-home').style.display = 'none';
    document.getElementById('view-deploy').classList.remove('active');
    document.getElementById('view-test').classList.remove('active');
    document.getElementById('view-reset').classList.remove('active');

    if (scene === 'deploy') {
        document.getElementById('view-deploy').classList.add('active');
        if (stateCache.is_first_time) {
            document.getElementById('deploy-first').style.display = 'block';
            document.getElementById('deploy-not-first').style.display = 'none';
            renderFullConfigForm();
        } else {
            document.getElementById('deploy-first').style.display = 'none';
            document.getElementById('deploy-not-first').style.display = 'block';
            document.getElementById('single-module-form').style.display = 'none';
            document.getElementById('btn-restart-service').style.display = 'none';
            document.getElementById('deploy-log2').style.display = 'none';
        }
    } else if (scene === 'test') {
        document.getElementById('view-test').classList.add('active');
        document.getElementById('test-log').style.display = 'none';
        document.getElementById('test-log').textContent = '';
    } else if (scene === 'reset') {
        document.getElementById('view-reset').classList.add('active');
    }
}

function goHome() {
    document.querySelectorAll('.form-section').forEach(el => el.classList.remove('active'));
    document.getElementById('view-home').style.display = 'block';
}

// ========== 渲染表单 ==========
function renderFullConfigForm() {
    const formDiv = document.getElementById('config-form');
    formDiv.innerHTML = `
        <div class="config-module">
            <h3>企业大脑地址</h3>
            <div class="input-group">
                <label>当前值：<span class="current-value">${stateCache.dify_url || '未设置'}</span></label>
                <input type="text" id="dify-ip-port" placeholder="例: 127.0.0.1:8089">
            </div>
        </div>
        <div class="config-module">
            <h3>大语言模型 (LLM)</h3>
            <div class="input-group">
                <label>URL <span class="current-value">(${stateCache.llm_url || '无'})</span></label>
                <input type="text" id="llm-url" placeholder="例: http://127.0.0.1:16000/v1">
            </div>
            <div class="input-group">
                <label>UID <span class="current-value">(${stateCache.llm_uid || '无'})</span></label>
                <input type="text" id="llm-uid" placeholder="模型ID">
            </div>
            <div class="input-group">
                <label>API_KEY <span class="current-value">(${stateCache.llm_key || 'xxx'})</span></label>
                <input type="text" id="llm-key" placeholder="留空则使用默认">
            </div>
        </div>
        <div class="config-module">
            <h3>Embedding 模型</h3>
            <div class="input-group">
                <label>URL <span class="current-value">(${stateCache.emb_url || '无'})</span></label>
                <input type="text" id="emb-url" placeholder="例: http://127.0.0.1:16001/v1/embeddings">
            </div>
            <div class="input-group">
                <label>UID <span class="current-value">(${stateCache.emb_uid || '无'})</span></label>
                <input type="text" id="emb-uid" placeholder="模型ID">
            </div>
        </div>
        <div class="config-module">
            <h3>数据库配置（可选）</h3>
            <div class="input-group">
                <label>Host <span class="current-value">(${stateCache.mysql_host || '无'})</span></label>
                <input type="text" id="db-host" placeholder="数据库主机">
            </div>
            <div class="input-group">
                <label>Port <span class="current-value">(${stateCache.mysql_port || '无'})</span></label>
                <input type="text" id="db-port" placeholder="端口号">
            </div>
            <div class="input-group">
                <label>数据库名 <span class="current-value">(${stateCache.db_db || 'saas'})</span></label>
                <input type="text" id="db-db" placeholder="默认 saas">
            </div>
            <div class="input-group">
                <label>用户名 <span class="current-value">(${stateCache.db_user || '无'})</span></label>
                <input type="text" id="db-user" placeholder="用户名">
            </div>
            <div class="input-group">
                <label>密码 <span class="current-value">(已隐藏)</span></label>
                <input type="password" id="db-password" placeholder="输入新密码">
            </div>
            <div class="input-group">
                <label>类型 <span class="current-value">(${stateCache.db_type || 'mysql'})</span></label>
                <select id="db-type">
                    <option value="mysql">mysql</option>
                    <option value="dm">dm</option>
                    <option value="kb">kb</option>
                </select>
            </div>
            <div class="input-group">
                <label>Schema <span class="current-value">(${stateCache.db_schema || 'public'})</span></label>
                <input type="text" id="db-schema" placeholder="默认 public">
            </div>
        </div>
    `;
}

function showModule(module) {
    const div = document.getElementById('single-module-form');
    let html = '';
    if (module === 'dify') {
        html = `
            <div class="config-module">
                <h3>企业大脑地址</h3>
                <div class="input-group">
                    <label>当前值：<span class="current-value">${stateCache.dify_url || '无'}</span></label>
                    <input type="text" id="dify-ip-single" placeholder="例: 127.0.0.1:8089">
                </div>
                <button class="btn" onclick="submitSingle('dify')">保存</button>
            </div>`;
    } else if (module === 'llm') {
        html = `
            <div class="config-module">
                <h3>大语言模型</h3>
                <div class="input-group"><label>URL <span class="current-value">(${stateCache.llm_url || '无'})</span></label><input type="text" id="llm-url-single"></div>
                <div class="input-group"><label>UID <span class="current-value">(${stateCache.llm_uid || '无'})</span></label><input type="text" id="llm-uid-single"></div>
                <div class="input-group"><label>API_KEY <span class="current-value">(${stateCache.llm_key || 'xxx'})</span></label><input type="text" id="llm-key-single"></div>
                <button class="btn" onclick="submitSingle('llm')">保存</button>
            </div>`;
    } else if (module === 'embedding') {
        html = `
            <div class="config-module">
                <h3>Embedding 模型</h3>
                <div class="input-group"><label>URL <span class="current-value">(${stateCache.emb_url || '无'})</span></label><input type="text" id="emb-url-single"></div>
                <div class="input-group"><label>UID <span class="current-value">(${stateCache.emb_uid || '无'})</span></label><input type="text" id="emb-uid-single"></div>
                <button class="btn" onclick="submitSingle('embedding')">保存</button>
            </div>`;
    }
    div.innerHTML = html;
    div.style.display = 'block';
    document.getElementById('btn-restart-service').style.display = 'inline-block';
}

// ========== 修改后的 submitSingle（含校验） ==========
async function submitSingle(module) {
    // 清除旧错误
    clearAllErrors();

    let values = {};

    if (module === 'dify') {
        const ipPort = document.getElementById('dify-ip-single')?.value;
        if (ipPort && !isValidIPPort(ipPort)) {
            markError('dify-ip-single', '❌ 格式错误，请使用 IP:端口 (例: 127.0.0.1:8089)');
            showResult('输入错误', '企业大脑地址格式不正确，请使用 IP:端口 格式');
            return;
        }
        values.ip_port = ipPort;
    } else if (module === 'llm') {
        const url = document.getElementById('llm-url-single')?.value;
        const uid = document.getElementById('llm-uid-single')?.value;
        const key = document.getElementById('llm-key-single')?.value || '';
        if (url && !isValidUrl(url)) {
            markError('llm-url-single', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
            showResult('输入错误', 'LLM URL 格式错误');
            return;
        }
        if ((url && !uid) || (!url && uid)) {
            markError('llm-uid-single', '❌ URL 和 UID 必须同时填写');
            showResult('输入错误', 'LLM URL 和 UID 必须同时填写');
            return;
        }
        values.url = url;
        values.uid = uid;
        values.key = key;
    } else if (module === 'embedding') {
        const url = document.getElementById('emb-url-single')?.value;
        const uid = document.getElementById('emb-uid-single')?.value;
        if (url && !isValidUrl(url)) {
            markError('emb-url-single', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
            showResult('输入错误', 'Embedding URL 格式错误');
            return;
        }
        if ((url && !uid) || (!url && uid)) {
            markError('emb-uid-single', '❌ URL 和 UID 必须同时填写');
            showResult('输入错误', 'Embedding URL 和 UID 必须同时填写');
            return;
        }
        values.url = url;
        values.uid = uid;
    }

    // 校验通过，提交
    const resp = await fetch('/api/modify', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({module, values})
    });
    const data = await resp.json();
    showResult(data.success ? '成功' : '失败', data.message || data.error);
    await fetchState();
    showModule(module);
}

// ========== 修改后的 saveAllConfigs（含校验） ==========
async function saveAllConfigs() {
    // 清除旧错误
    clearAllErrors();

    // ----- 1. 校验企业大脑 -----
    const difyIp = document.getElementById('dify-ip-port')?.value;
    if (difyIp && !isValidIPPort(difyIp)) {
        markError('dify-ip-port', '❌ 格式错误，请使用 IP:端口 (例: 127.0.0.1:8089)');
        showResult('输入错误', '企业大脑地址格式不正确，请使用 IP:端口 格式');
        return;
    }

    // ----- 2. 校验 LLM -----
    const llmUrl = document.getElementById('llm-url')?.value;
    const llmUid = document.getElementById('llm-uid')?.value;
    if (llmUrl && !isValidUrl(llmUrl)) {
        markError('llm-url', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
        showResult('输入错误', 'LLM URL 格式错误，请以 http:// 或 https:// 开头');
        return;
    }
    if ((llmUrl && !llmUid) || (!llmUrl && llmUid)) {
        markError('llm-uid', '❌ URL 和 UID 必须同时填写');
        showResult('输入错误', 'LLM URL 和 UID 必须同时填写');
        return;
    }

    // ----- 3. 校验 Embedding -----
    const embUrl = document.getElementById('emb-url')?.value;
    const embUid = document.getElementById('emb-uid')?.value;
    if (embUrl && !isValidUrl(embUrl)) {
        markError('emb-url', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
        showResult('输入错误', 'Embedding URL 格式错误，请以 http:// 或 https:// 开头');
        return;
    }
    if ((embUrl && !embUid) || (!embUrl && embUid)) {
        markError('emb-uid', '❌ URL 和 UID 必须同时填写');
        showResult('输入错误', 'Embedding URL 和 UID 必须同时填写');
        return;
    }

    // ----- 4. 校验通过，执行原有的保存逻辑（完全不变） -----
    if (difyIp) {
        await fetch('/api/modify', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({module:'dify', values:{ip_port: difyIp}})
        });
    }
    if (llmUrl && llmUid) {
        const llmKey = document.getElementById('llm-key')?.value || '';
        await fetch('/api/modify', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({module:'llm', values:{url:llmUrl, uid:llmUid, key:llmKey}})
        });
    }
    if (embUrl && embUid) {
        await fetch('/api/modify', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({module:'embedding', values:{url:embUrl, uid:embUid}})
        });
    }
    const dbHost = document.getElementById('db-host')?.value;
    const dbPort = document.getElementById('db-port')?.value;
    if (dbHost || dbPort) {
        const dbValues = {};
        if (dbHost) dbValues.host = dbHost;
        if (dbPort) dbValues.port = dbPort;
        const dbDb = document.getElementById('db-db')?.value;
        if (dbDb) dbValues.db_db = dbDb;
        const dbUser = document.getElementById('db-user')?.value;
        if (dbUser) dbValues.db_user = dbUser;
        const dbPwd = document.getElementById('db-password')?.value;
        if (dbPwd) dbValues.db_password = dbPwd;
        const dbType = document.getElementById('db-type')?.value;
        if (dbType) dbValues.db_type = dbType;
        const dbSchema = document.getElementById('db-schema')?.value;
        if (dbSchema) dbValues.db_schema = dbSchema;
        await fetch('/api/modify', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({module:'db', values: dbValues})
        });
    }
}

// ========== 流式处理通用函数 ==========
async function handleStream(url, logDivId, btnId) {
    const logDiv = document.getElementById(logDivId);
    const btn = document.getElementById(btnId);
    logDiv.style.display = 'block';
    logDiv.innerHTML = '';
    btn.disabled = true;
    btn.textContent = '执行中...';

    try {
        const response = await fetch(url, { method: 'POST' });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.trim() === '') continue;
                try {
                    const data = JSON.parse(line);
                    const step = data.step || '';
                    const status = data.status || 'info';
                    const color = status === 'success' ? '#27ae60' :
                                  status === 'error' ? '#e74c3c' :
                                  status === 'warning' ? '#f39c12' : '#ecf0f1';
                    logDiv.innerHTML += `<div style="color: ${color};">${step}</div>`;
                    logDiv.scrollTop = logDiv.scrollHeight;
                } catch (e) {
                    logDiv.innerHTML += `<div>${line}</div>`;
                }
            }
        }
    } catch (err) {
        logDiv.innerHTML += `<div style="color: red;">请求失败: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = btnId === 'btn-load-start' ? '加载镜像并启动服务' : '重启服务';
        await fetchState();
    }
}

// ========== 事件绑定 ==========
document.addEventListener('DOMContentLoaded', function() {
    // 首次部署：保存配置 + 流式部署
    const btnLoad = document.getElementById('btn-load-start');
    if (btnLoad) {
        btnLoad.addEventListener('click', async function() {
            await saveAllConfigs();
            await handleStream('/api/deploy/stream', 'deploy-log', 'btn-load-start');
        });
    }

    // 重启服务按钮（非首次）
    const btnRestart = document.getElementById('btn-restart-service');
    if (btnRestart) {
        btnRestart.addEventListener('click', async function() {
            await handleStream('/api/service/restart/stream', 'deploy-log2', 'btn-restart-service');
        });
    }
});

// ========== 测试提示 ==========
async function runTest() {
    const logDiv = document.getElementById('test-log');
    logDiv.style.display = 'block';
    logDiv.textContent = '正在获取提示...';
    try {
        const resp = await fetch('/api/test/run', { method: 'POST' });
        const data = await resp.json();
        logDiv.textContent = data.message || data.error || '未知错误';
    } catch (e) {
        logDiv.textContent = '请求失败: ' + e.message;
    }
}

// ========== 重置 ==========
function showResetModal() {
    document.getElementById('reset-modal').classList.add('active');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}
async function confirmReset() {
    closeModal('reset-modal');
    const resp = await fetch('/api/reset', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({confirm: true})
    });
    const data = await resp.json();
    showResult(data.success ? '重置完成' : '重置失败', data.message || data.error);
}

function showResult(title, msg) {
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-msg').textContent = msg;
    document.getElementById('result-modal').classList.add('active');
}

// ========== 初始化 ==========
window.onload = function() {
    fetchState();
    startHealthCheck();
};
