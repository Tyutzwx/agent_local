let stateCache = null;
let healthInterval = null;

// ========== 配置修改与保存状态 ==========
window._configChanged = false;   // 任何表单是否被修改过（用于首次和非首次）
window._configSaved = false;    // 首次部署专用：是否已成功保存配置

function markConfigChanged(element) {
    // 清除该输入框自身的错误提示
    if (element) {
        element.style.border = '1px solid #ced4da';
        element.style.backgroundColor = '';
        const hint = element.parentElement.querySelector('.error-hint');
        if (hint) hint.remove();
    }

    // 更新全局修改标记：检查所有带 data-initial-value 的输入/选择框
    const inputs = document.querySelectorAll(
        '#single-module-form input[data-initial-value], ' +
        '#config-form input[data-initial-value], ' +
        '#config-form select[data-initial-value]'
    );
    let hasChange = false;
    inputs.forEach(input => {
        const initial = input.getAttribute('data-initial-value') || '';
        if (input.tagName === 'SELECT') {
            if (input.value !== initial) hasChange = true;
        } else {
            if (input.value !== initial) hasChange = true;
        }
    });
    window._configChanged = hasChange;
    // 如果有修改，则之前的保存无效（重置保存标志）
    if (hasChange) {
        window._configSaved = false;
    }
}

// ========== 前端表单校验工具 ==========
function isValidIPPort(value) {
    if (!value) return false;
    const regex = /^(\d{1,3}\.){3}\d{1,3}:\d+$/;
    if (!regex.test(value)) return false;
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
            window._configChanged = false;
            window._configSaved = false;
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

// ========== 渲染首次部署完整表单 ==========
function renderFullConfigForm() {
    const formDiv = document.getElementById('config-form');
    formDiv.innerHTML = `
        <div class="config-module">
            <h3>企业大脑地址</h3>
            <div class="input-group">
                <label>当前值：<span class="current-value">${stateCache.dify_url || '未设置'}</span></label>
                <input type="text" id="dify-ip-port" 
                       data-initial-value="${stateCache.dify_url || ''}"
                       placeholder="例: 127.0.0.1:8089"
                       oninput="markConfigChanged(this)">
            </div>
        </div>
        <div class="config-module">
            <h3>大语言模型 (LLM)</h3>
            <div class="input-group">
                <label>URL <span class="current-value">(${stateCache.llm_url || '无'})</span></label>
                <input type="text" id="llm-url" 
                       data-initial-value="${stateCache.llm_url || ''}"
                       placeholder="例: http://127.0.0.1:16000/v1"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>UID <span class="current-value">(${stateCache.llm_uid || '无'})</span></label>
                <input type="text" id="llm-uid" 
                       data-initial-value="${stateCache.llm_uid || ''}"
                       placeholder="模型ID"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>API_KEY <span class="current-value">(${stateCache.llm_key || 'xxx'})</span></label>
                <input type="text" id="llm-key" 
                       data-initial-value="${stateCache.llm_key || ''}"
                       placeholder="留空则使用默认"
                       oninput="markConfigChanged(this)">
            </div>
        </div>
        <div class="config-module">
            <h3>Embedding 模型</h3>
            <div class="input-group">
                <label>URL <span class="current-value">(${stateCache.emb_url || '无'})</span></label>
                <input type="text" id="emb-url" 
                       data-initial-value="${stateCache.emb_url || ''}"
                       placeholder="例: http://127.0.0.1:16001/v1/embeddings"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>UID <span class="current-value">(${stateCache.emb_uid || '无'})</span></label>
                <input type="text" id="emb-uid" 
                       data-initial-value="${stateCache.emb_uid || ''}"
                       placeholder="模型ID"
                       oninput="markConfigChanged(this)">
            </div>
        </div>
        <div class="config-module">
            <h3>数据库配置（可选）</h3>
            <div class="input-group">
                <label>Host <span class="current-value">(${stateCache.mysql_host || '无'})</span></label>
                <input type="text" id="db-host" 
                       data-initial-value="${stateCache.mysql_host || ''}"
                       placeholder="数据库主机"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>Port <span class="current-value">(${stateCache.mysql_port || '无'})</span></label>
                <input type="text" id="db-port" 
                       data-initial-value="${stateCache.mysql_port || ''}"
                       placeholder="端口号"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>数据库名 <span class="current-value">(${stateCache.db_db || 'saas'})</span></label>
                <input type="text" id="db-db" 
                       data-initial-value="${stateCache.db_db || ''}"
                       placeholder="默认 saas"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>用户名 <span class="current-value">(${stateCache.db_user || '无'})</span></label>
                <input type="text" id="db-user" 
                       data-initial-value="${stateCache.db_user || ''}"
                       placeholder="用户名"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>密码 <span class="current-value">(已隐藏)</span></label>
                <input type="password" id="db-password" 
                       data-initial-value="${stateCache.db_password || ''}"
                       placeholder="输入新密码"
                       oninput="markConfigChanged(this)">
            </div>
            <div class="input-group">
                <label>类型 <span class="current-value">(${stateCache.db_type || 'mysql'})</span></label>
                <select id="db-type" data-initial-value="${stateCache.db_type || 'mysql'}" onchange="markConfigChanged(this)">
                    <option value="mysql" ${stateCache.db_type === 'mysql' ? 'selected' : ''}>mysql</option>
                    <option value="dm" ${stateCache.db_type === 'dm' ? 'selected' : ''}>dm</option>
                    <option value="kb" ${stateCache.db_type === 'kb' ? 'selected' : ''}>kb</option>
                </select>
            </div>
            <div class="input-group">
                <label>Schema <span class="current-value">(${stateCache.db_schema || 'public'})</span></label>
                <input type="text" id="db-schema" 
                       data-initial-value="${stateCache.db_schema || ''}"
                       placeholder="默认 public"
                       oninput="markConfigChanged(this)">
            </div>
        </div>
    `;
    // 重置状态：刚加载表单，尚未保存，且无修改
    window._configChanged = false;
    window._configSaved = false;
}

// ========== 非首次部署，单模块表单 ==========
function showModule(module) {
    const div = document.getElementById('single-module-form');
    let html = '';
    if (module === 'dify') {
        html = `
            <div class="config-module">
                <h3>企业大脑地址</h3>
                <div class="input-group">
                    <label>当前值：<span class="current-value">${stateCache.dify_url || '无'}</span></label>
                    <input type="text" id="dify-ip-single" 
                           data-initial-value="${stateCache.dify_url || ''}"
                           placeholder="例: 127.0.0.1:8089"
                           oninput="markConfigChanged(this)">
                </div>
                <button class="btn" onclick="submitSingle('dify')">保存</button>
            </div>`;
    } else if (module === 'llm') {
        html = `
            <div class="config-module">
                <h3>大语言模型</h3>
                <div class="input-group">
                    <label>URL <span class="current-value">(${stateCache.llm_url || '无'})</span></label>
                    <input type="text" id="llm-url-single" 
                           data-initial-value="${stateCache.llm_url || ''}"
                           placeholder="例: http://127.0.0.1:16000/v1"
                           oninput="markConfigChanged(this)">
                </div>
                <div class="input-group">
                    <label>UID <span class="current-value">(${stateCache.llm_uid || '无'})</span></label>
                    <input type="text" id="llm-uid-single" 
                           data-initial-value="${stateCache.llm_uid || ''}"
                           placeholder="模型ID"
                           oninput="markConfigChanged(this)">
                </div>
                <div class="input-group">
                    <label>API_KEY <span class="current-value">(${stateCache.llm_key || 'xxx'})</span></label>
                    <input type="text" id="llm-key-single" 
                           data-initial-value="${stateCache.llm_key || ''}"
                           placeholder="留空则使用默认"
                           oninput="markConfigChanged(this)">
                </div>
                <button class="btn" onclick="submitSingle('llm')">保存</button>
            </div>`;
    } else if (module === 'embedding') {
        html = `
            <div class="config-module">
                <h3>Embedding 模型</h3>
                <div class="input-group">
                    <label>URL <span class="current-value">(${stateCache.emb_url || '无'})</span></label>
                    <input type="text" id="emb-url-single" 
                           data-initial-value="${stateCache.emb_url || ''}"
                           placeholder="例: http://127.0.0.1:16001/v1/embeddings"
                           oninput="markConfigChanged(this)">
                </div>
                <div class="input-group">
                    <label>UID <span class="current-value">(${stateCache.emb_uid || '无'})</span></label>
                    <input type="text" id="emb-uid-single" 
                           data-initial-value="${stateCache.emb_uid || ''}"
                           placeholder="模型ID"
                           oninput="markConfigChanged(this)">
                </div>
                <button class="btn" onclick="submitSingle('embedding')">保存</button>
            </div>`;
    }
    div.innerHTML = html;
    div.style.display = 'block';
    document.getElementById('btn-restart-service').style.display = 'inline-block';
    // 重置修改标记（因为刚加载完，无修改）
    window._configChanged = false;
}

// ========== submitSingle（非首次部署） ==========
async function submitSingle(module) {
    clearAllErrors();
    let errors = [];
    let values = {};

    if (module === 'dify') {
        const ipPort = document.getElementById('dify-ip-single')?.value?.trim();
        if (!ipPort) {
            markError('dify-ip-single', '❌ 此项为必填，请输入 IP:端口');
            errors.push('企业大脑地址不能为空');
        } else if (!isValidIPPort(ipPort)) {
            markError('dify-ip-single', '❌ 格式错误，请使用 IP:端口');
            errors.push('企业大脑地址格式不正确，请使用 IP:端口 格式');
        }
        values.ip_port = ipPort;
    } else if (module === 'llm') {
        const url = document.getElementById('llm-url-single')?.value?.trim();
        const uid = document.getElementById('llm-uid-single')?.value?.trim();
        const key = document.getElementById('llm-key-single')?.value || '';
        if (!url || !uid) {
            if (!url) markError('llm-url-single', '❌ URL 不能为空');
            if (!uid) markError('llm-uid-single', '❌ UID 不能为空');
            errors.push('LLM URL 和 UID 都不能为空');
        } else {
            if (!isValidUrl(url)) {
                markError('llm-url-single', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
                errors.push('LLM URL 格式错误，请以 http:// 或 https:// 开头');
            }
        }
        values.url = url;
        values.uid = uid;
        values.key = key;
    } else if (module === 'embedding') {
        const url = document.getElementById('emb-url-single')?.value?.trim();
        const uid = document.getElementById('emb-uid-single')?.value?.trim();
        if (!url || !uid) {
            if (!url) markError('emb-url-single', '❌ URL 不能为空');
            if (!uid) markError('emb-uid-single', '❌ UID 不能为空');
            errors.push('Embedding URL 和 UID 都不能为空');
        } else {
            if (!isValidUrl(url)) {
                markError('emb-url-single', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
                errors.push('Embedding URL 格式错误，请以 http:// 或 https:// 开头');
            }
        }
        values.url = url;
        values.uid = uid;
    }

    if (errors.length > 0) {
        let msg = '⚠️ 共发现 ' + errors.length + ' 个问题：\n\n';
        errors.forEach((e, i) => {
            msg += (i + 1) + '. ' + e + '\n';
        });
        showResult('输入错误', msg);
        return;
    }

    const resp = await fetch('/api/modify', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({module, values})
    });
    const data = await resp.json();
    if (data.success) {
        showResult('✅ 保存成功', data.message || '配置已更新');
        await fetchState();
        window._configChanged = false;
        // 重新渲染该模块表单，更新初始值
        showModule(module);
    } else {
        showResult('❌ 保存失败', data.error || data.message || '未知错误');
    }
}

// ========== saveAllConfigs（首次部署完整表单保存） ==========
async function saveAllConfigs() {
    clearAllErrors();
    let errors = [];

    const difyIp = document.getElementById('dify-ip-port')?.value?.trim();
    if (difyIp && !isValidIPPort(difyIp)) {
        markError('dify-ip-port', '❌ 格式错误，请使用 IP:端口');
        errors.push('企业大脑地址格式不正确，请使用 IP:端口 格式');
    }

    const llmUrl = document.getElementById('llm-url')?.value?.trim();
    const llmUid = document.getElementById('llm-uid')?.value?.trim();
    if (llmUrl || llmUid) {
        if (!llmUrl) {
            markError('llm-url', '❌ URL 不能为空');
            errors.push('LLM URL 不能为空');
        } else if (!llmUid) {
            markError('llm-uid', '❌ UID 不能为空');
            errors.push('LLM UID 不能为空');
        } else if (!isValidUrl(llmUrl)) {
            markError('llm-url', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
            errors.push('LLM URL 格式错误，请以 http:// 或 https:// 开头');
        }
    }

    const embUrl = document.getElementById('emb-url')?.value?.trim();
    const embUid = document.getElementById('emb-uid')?.value?.trim();
    if (embUrl || embUid) {
        if (!embUrl) {
            markError('emb-url', '❌ URL 不能为空');
            errors.push('Embedding URL 不能为空');
        } else if (!embUid) {
            markError('emb-uid', '❌ UID 不能为空');
            errors.push('Embedding UID 不能为空');
        } else if (!isValidUrl(embUrl)) {
            markError('emb-url', '❌ URL 格式错误，必须以 http:// 或 https:// 开头');
            errors.push('Embedding URL 格式错误，请以 http:// 或 https:// 开头');
        }
    }

    // 数据库校验（可选）
    const dbHost = document.getElementById('db-host')?.value?.trim();
    const dbPort = document.getElementById('db-port')?.value?.trim();
    const dbDb = document.getElementById('db-db')?.value?.trim();
    const dbUser = document.getElementById('db-user')?.value?.trim();
    const dbSchema = document.getElementById('db-schema')?.value?.trim();

    if (dbHost && !/^[a-zA-Z0-9.-]+$/.test(dbHost)) {
        markError('db-host', '❌ 主机名只能包含字母、数字、点、横线');
        errors.push('数据库主机名格式不正确');
    }
    if (dbPort) {
        const portNum = Number(dbPort);
        if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
            markError('db-port', '❌ 端口必须是 1-65535 的数字');
            errors.push('数据库端口格式不正确');
        }
    }
    if (dbDb && !/^[a-zA-Z0-9_]+$/.test(dbDb)) {
        markError('db-db', '❌ 数据库名只能包含字母、数字、下划线');
        errors.push('数据库名格式不正确');
    }
    if (dbUser && !/^[a-zA-Z0-9_]+$/.test(dbUser)) {
        markError('db-user', '❌ 用户名只能包含字母、数字、下划线');
        errors.push('数据库用户名格式不正确');
    }
    if (dbSchema && !/^[a-zA-Z0-9_]+$/.test(dbSchema)) {
        markError('db-schema', '❌ Schema 只能包含字母、数字、下划线');
        errors.push('数据库 Schema 格式不正确');
    }

    if (errors.length > 0) {
        let msg = '⚠️ 共发现 ' + errors.length + ' 个问题：\n\n';
        errors.forEach((e, i) => {
            msg += (i + 1) + '. ' + e + '\n';
        });
        showResult('输入错误', msg);
        return false;
    }

    try {
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
        // 数据库
        if (dbHost || dbPort || dbDb || dbUser || document.getElementById('db-password')?.value || document.getElementById('db-type')?.value || dbSchema) {
            const dbValues = {};
            if (dbHost) dbValues.host = dbHost;
            if (dbPort) dbValues.port = dbPort;
            if (dbDb) dbValues.db_db = dbDb;
            if (dbUser) dbValues.db_user = dbUser;
            const dbPwd = document.getElementById('db-password')?.value;
            if (dbPwd) dbValues.db_password = dbPwd;
            const dbType = document.getElementById('db-type')?.value;
            if (dbType) dbValues.db_type = dbType;
            if (dbSchema) dbValues.db_schema = dbSchema;
            await fetch('/api/modify', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({module:'db', values: dbValues})
            });
        }
        // 保存成功，重置状态
        window._configChanged = false;
        window._configSaved = true;
        return true;
    } catch (error) {
        showResult('保存失败', error.message);
        return false;
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
    let hasError = false;

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
                    if (status === 'error') {
                        hasError = true;
                    }
                } catch (e) {
                    logDiv.innerHTML += `<div>${line}</div>`;
                }
            }
        }
    } catch (err) {
        logDiv.innerHTML += `<div style="color: red;">请求失败: ${err.message}</div>`;
        hasError = true;
    } finally {
        btn.disabled = false;
        btn.textContent = btnId === 'btn-load-start' ? '加载镜像并启动服务' : '重启服务';
        await fetchState();
    }
}

// ========== 模态框 ==========
function showResult(title, msg, callback) {
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-msg').textContent = msg;
    document.getElementById('result-modal').classList.add('active');
    window._resultCallback = callback || null;
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    if (id === 'result-modal' && window._resultCallback) {
        const cb = window._resultCallback;
        window._resultCallback = null;
        cb();
    }
}

// ========== 事件绑定 ==========
document.addEventListener('DOMContentLoaded', function() {
    // ----- 首次部署：保存配置按钮 -----
    const btnSave = document.getElementById('btn-save-config');
    if (btnSave) {
        btnSave.addEventListener('click', async function() {
            const saved = await saveAllConfigs();
            if (saved) {
                showResult('✅ 配置已保存', '所有配置已保存成功，可以继续部署。');
            }
        });
    }

    // ----- 首次部署：加载镜像并启动服务按钮 -----
    const btnLoad = document.getElementById('btn-load-start');
    if (btnLoad) {
        btnLoad.addEventListener('click', async function() {
            // 检查配置是否已保存
            if (window._configChanged) {
                showResult('⚠️ 配置未保存', '检测到配置已修改但尚未保存。\n\n请先点击“保存配置”按钮保存后再启动服务。');
                return;
            }
            if (!window._configSaved) {
                showResult('⚠️ 配置未保存', '请先点击“保存配置”按钮保存当前配置，然后再加载镜像启动服务。');
                return;
            }   
            // 记录当前是否为首次部署（部署完成后状态会变化）
            const wasFirstTime = stateCache && stateCache.is_first_time;
            // 执行部署流
            await handleStream('/api/deploy/stream', 'deploy-log', 'btn-load-start');
            // 如果部署前是首次部署，则弹窗并返回首页
            if (wasFirstTime) {
                showResult('🎉 首次部署完成', '服务已成功部署并启动！\n\n点击确定返回首页。', function() {
                    goHome();
                });
            }
        });
    } 

    // ----- 非首次部署：重启服务按钮 -----
    const btnRestart = document.getElementById('btn-restart-service');
    if (btnRestart) {
        btnRestart.addEventListener('click', async function() {
            if (window._configChanged) {
                showResult('⚠️ 配置未保存', '检测到配置已被修改但尚未保存。\n\n请先点击对应模块的"保存"按钮，保存成功后再重启服务。');
                return;
            }
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

// ========== 初始化 ==========
window.onload = function() {
    fetchState();
    startHealthCheck();
};
