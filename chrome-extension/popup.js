// AI WordPress Agent — Popup Script (External JS - CSP Compliant)
// لا inline handlers — كل شيء هنا

const AGENT_URL_KEY = 'aiwa_agent_url';
const SITES_KEY     = 'aiwa_sites';
const LLM_KEY       = 'aiwa_llm';

let state = {
  agentUrl: 'http://127.0.0.1:5001',
  sites:    [],
  current:  null,
  online:   false,
};

// ── Init ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const saved = await chrome.storage.local.get([AGENT_URL_KEY, SITES_KEY, LLM_KEY]);
  if (saved[AGENT_URL_KEY]) state.agentUrl = saved[AGENT_URL_KEY];
  if (saved[SITES_KEY])     state.sites    = saved[SITES_KEY];

  render();
  bindEvents();
  await pingAgent();
  await loadSystemStatus();
  loadSites();
});

// ── Render ──────────────────────────────────────────────
function render() {
  document.getElementById('agent-url-inp').value = state.agentUrl;
  renderSitesList();
}

function renderSitesList() {
  const list = document.getElementById('sites-list');
  if (!list) return;
  if (!state.sites.length) {
    list.innerHTML = '<div style="color:#6b7280;font-size:11px;text-align:center;padding:8px">No sites — add one in Settings</div>';
    return;
  }
  list.innerHTML = state.sites.map(s =>
    `<div class="site-row ${s.name === state.current?.name ? 'active' : ''}"
          data-site="${escHtml(s.name)}">
       <span class="dot ${s.connected ? 'ok' : 'err'}"></span>
       <span class="site-name">${escHtml(s.name)}</span>
       <span class="conn-badge">${s.connected ? 'متصل' : 'غير متصل'}</span>
     </div>`
  ).join('');
  // Bind click per site
  list.querySelectorAll('.site-row').forEach(row => {
    row.addEventListener('click', () => selectSite(row.dataset.site));
  });
}

// ── Events ──────────────────────────────────────────────
function bindEvents() {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Task
  document.getElementById('btn-run')?.addEventListener('click', runTask);
  document.getElementById('btn-explain')?.addEventListener('click', () => runTask(true));
  document.getElementById('task-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) runTask();
  });

  // Quick tasks
  document.querySelectorAll('[data-quick]').forEach(btn => {
    btn.addEventListener('click', () => {
      const inp = document.getElementById('task-input');
      if (inp) { inp.value = btn.dataset.quick; runTask(); }
    });
  });

  // Page analysis
  document.getElementById('btn-analyze')?.addEventListener('click', analyzePage);
  document.getElementById('btn-learn')?.addEventListener('click', learnPage);

  // Sites
  document.getElementById('btn-add-site')?.addEventListener('click', addSite);

  // Settings
  document.getElementById('btn-save-url')?.addEventListener('click', saveAgentUrl);
  document.getElementById('btn-save-llm')?.addEventListener('click', saveLLM);
  document.getElementById('btn-open-dash')?.addEventListener('click', () =>
    chrome.tabs.create({ url: state.agentUrl + '/wp-dashboard' })
  );

  // Knowledge
  document.getElementById('btn-kb-search')?.addEventListener('click', kbSearch);
  document.getElementById('btn-kb-url')?.addEventListener('click', kbLearnUrl);
}

// ── Tabs ────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + name));
  if (name === 'system') loadSystemStatus();
  if (name === 'sites')  loadSites();
}

// ── Agent API ───────────────────────────────────────────
async function api(path, body = null, method = body ? 'POST' : 'GET') {
  try {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(state.agentUrl + path, opts);
    return r.ok ? await r.json() : { error: `HTTP ${r.status}` };
  } catch(e) {
    return { error: e.message };
  }
}

// ── Ping ────────────────────────────────────────────────
async function pingAgent() {
  const r = await api('/healthz');
  state.online = r.ok === true;
  const dot = document.getElementById('agent-dot');
  const txt = document.getElementById('agent-status');
  if (dot) dot.className = 'status-dot ' + (state.online ? 'ok' : 'err');
  if (txt) txt.textContent = state.online ? 'Online — ' + state.agentUrl : 'Offline';
}

// ── System Status ───────────────────────────────────────
async function loadSystemStatus() {
  const d = await api('/system/status');
  if (d.error) return;
  const aw = d.awareness || {};
  const fb = d.feedback  || {};
  const lm = d.llm       || {};

  setEl('sys-uptime',   formatUptime(aw.uptime_seconds));
  setEl('sys-tasks',    aw.tasks_done || 0);
  setEl('sys-rate',     (fb.success_rate || 0) + '%');
  setEl('sys-sites',    (aw.connected_sites || []).length + ' connected');
  setEl('sys-kb',       (d.knowledge?.total || 0) + ' docs');
  setEl('sys-llm',      lm.provider || 'mock');
  setEl('sys-tools',    (d.tools_health?.idle || 0) + '/' + (d.tools_health?.total || 0));

  // Badge
  const badge = document.getElementById('llm-badge');
  if (badge) { badge.textContent = lm.provider || 'mock'; badge.className = 'badge ' + (lm.provider || 'mock'); }

  // Update LLM selector
  const sel = document.getElementById('llm-provider-sel');
  if (sel && lm.provider) sel.value = lm.provider;

  // Update sites from awareness
  if (aw.sites?.length) {
    aw.sites.forEach(s => {
      const ex = state.sites.find(x => x.name === s.name);
      if (!ex) state.sites.push({ name: s.name, url: s.url, key: '', connected: s.connection === 'connected' });
      else ex.connected = s.connection === 'connected';
    });
    renderSitesList();
    await chrome.storage.local.set({ [SITES_KEY]: state.sites });
  }
}

// ── Sites ───────────────────────────────────────────────
async function loadSites() {
  const r = await api('/wp/sites');
  if (r.sites?.length) {
    r.sites.forEach(s => {
      const ex = state.sites.find(x => x.name === s.name);
      if (!ex) state.sites.push({ name: s.name, url: s.url, key: '', connected: s.connection === 'connected' });
      else ex.connected = s.connection === 'connected';
    });
    renderSitesList();
    await chrome.storage.local.set({ [SITES_KEY]: state.sites });
  }
}

function selectSite(name) {
  state.current = state.sites.find(s => s.name === name) || null;
  renderSitesList();
  log('Selected: ' + name, 'info');
}

async function addSite() {
  const name = document.getElementById('ns-name')?.value.trim();
  const url  = document.getElementById('ns-url')?.value.trim();
  const key  = document.getElementById('ns-key')?.value.trim();
  if (!name || !url || !key) { log('أدخل كل الحقول', 'warn'); return; }
  log('Adding: ' + name, 'info');
  const r = await api('/wp/add-site', { name, url, api_key: key });
  if (r.success) {
    const ex = state.sites.find(s => s.name === name);
    if (!ex) state.sites.push({ name, url, key, connected: r.connected || false });
    else ex.connected = r.connected || false;
    await chrome.storage.local.set({ [SITES_KEY]: state.sites });
    renderSitesList();
    state.current = state.sites.find(s => s.name === name);
    log('Added: ' + name + (r.connected ? ' (connected)' : ''), 'ok');
    clearInputs(['ns-name','ns-url','ns-key']);
  } else {
    log('Failed: ' + (r.error || '?'), 'err');
  }
}

// ── Task Runner ─────────────────────────────────────────
async function runTask(explain = false) {
  const task     = document.getElementById('task-input')?.value.trim();
  const allSites = document.getElementById('chk-all-sites')?.checked;
  if (!task) { log('Enter a task', 'warn'); return; }
  clearLog();
  log('Running: ' + task, 'info');
  const body = { task, explain };
  if (allSites) body.all_sites = true;
  else if (state.current) body.site = state.current.name;
  const r = await api('/run', body);
  if (r.error) { log('Error: ' + r.error, 'err'); return; }
  log('Done — ' + (r.status || 'ok'), 'ok');
  if (r.agent_type)     log('Agent: ' + r.agent_type, 'info');
  if (r.knowledge_used) log('Knowledge: ' + r.knowledge_used + ' docs', 'info');
}

// ── Page Analysis ───────────────────────────────────────
async function analyzePage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { type: 'ANALYZE_DOM' }, res => {
    if (!res?.ok) { logPage('Cannot analyze page', 'err'); return; }
    const d = res.data;
    const info = document.getElementById('page-info');
    if (info) info.innerHTML = [
      row('URL',       d.url?.slice(0,40) || '—'),
      row('Title',     d.title || '—'),
      row('Type',      d.pageType || '—'),
      row('WordPress', d.isWP ? 'Yes' : 'No'),
      row('Elementor', d.isElementor ? 'Yes' : 'No'),
      row('Forms',     d.forms),
      row('Images',    d.images),
    ].join('');
    logPage('Analyzed: ' + d.pageType, 'ok');
    chrome.tabs.sendMessage(tab.id, { type: 'SHOW_OVERLAY', text: 'AI Agent analyzed', color: '#2271b1' });
  });
}

async function learnPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  logPage('Learning: ' + tab.url, 'info');
  const r = await api('/wp/knowledge/learn-url', { url: tab.url });
  logPage(r.success ? 'Learned' : 'Failed: ' + r.reason, r.success ? 'ok' : 'err');
}

// ── Knowledge ───────────────────────────────────────────
async function kbSearch() {
  const q   = document.getElementById('kb-query')?.value || '';
  const r   = await api('/wp/knowledge/search', { query: q });
  const el  = document.getElementById('kb-results');
  if (!el) return;
  el.innerHTML = (r.results || []).map(item =>
    `<div class="kb-item"><strong>${escHtml(item.title || item.source || '')}</strong>
     <span class="type-badge">${item.type}</span>
     <p>${escHtml(item.snippet || '')}</p></div>`
  ).join('') || '<p style="color:#6b7280">No results</p>';
}

async function kbLearnUrl() {
  const url = document.getElementById('kb-url-inp')?.value.trim();
  if (!url) return;
  const r = await api('/wp/knowledge/learn-url', { url });
  log(r.success ? 'Learned: ' + url : 'Failed: ' + r.reason, r.success ? 'ok' : 'err');
}

// ── Settings ────────────────────────────────────────────
async function saveAgentUrl() {
  const val = document.getElementById('agent-url-inp')?.value.trim();
  if (!val) return;
  state.agentUrl = val;
  await chrome.storage.local.set({ [AGENT_URL_KEY]: val });
  await pingAgent();
  await loadSites();
  log('Saved: ' + val, 'ok');
}

async function saveLLM() {
  const provider = document.getElementById('llm-provider-sel')?.value || 'mock';
  const api_key  = document.getElementById('llm-key-inp')?.value || '';
  const model    = document.getElementById('llm-model-inp')?.value || '';
  const r = await api('/llm/configure', { provider, api_key, model });
  if (r.success) {
    await chrome.storage.local.set({ [LLM_KEY]: { provider, model } });
    log('LLM: ' + provider + ' / ' + model, 'ok');
  } else {
    log('LLM error: ' + r.error, 'err');
  }
}

// ── Helpers ─────────────────────────────────────────────
function log(msg, cls = 'info') {
  const el = document.getElementById('task-log');
  if (!el) return;
  const span = document.createElement('div');
  span.className = 'log-line ' + cls;
  span.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
  el.appendChild(span);
  el.scrollTop = el.scrollHeight;
}
function logPage(msg, cls = 'info') {
  const el = document.getElementById('page-log');
  if (!el) return;
  const span = document.createElement('div');
  span.className = 'log-line ' + cls;
  span.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
  el.appendChild(span);
}
function clearLog() {
  const el = document.getElementById('task-log');
  if (el) el.innerHTML = '';
}
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function clearInputs(ids) {
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
}
function formatUptime(s) {
  if (!s) return '0s';
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return h ? h + 'h ' + m + 'm' : m ? m + 'm ' + sec + 's' : sec + 's';
}
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function row(k, v) {
  return `<div class="info-row"><span class="key">${k}</span><span class="val">${escHtml(String(v))}</span></div>`;
}
