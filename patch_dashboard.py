"""
Patch wp-dashboard.html:
1. Add System Status sidebar panel
2. Add LLM config panel
3. Add Tools panel
4. Add Feedback panel
5. Inject live_dashboard.js
"""
import os, re

TARGET = r"C:\mcp-agent\templates\wp-dashboard.html"

with open(TARGET, "r", encoding="utf-8") as f:
    html = f.read()

if "live_dashboard.js" in html:
    print("Already patched — skipping")
    exit(0)

# ── 1. Add sidebar panels before </nav>
SIDEBAR_PANELS = """
      <div class="divider" style="height:1px;background:rgba(255,255,255,.07);margin:12px 0;"></div>
      <div class="menu-section">النظام</div>

      <!-- System Stats mini -->
      <div style="padding:8px 12px;font-size:11px;color:#a7aaad;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span>Uptime</span><span id="sys-uptime" style="color:#fff">—</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
          <span>Tasks</span><span id="sys-tasks" style="color:#fff">0</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
          <span>Success</span><span id="sys-rate" style="color:#10b981">—</span>
        </div>
      </div>

      <div class="menu-section" style="margin-top:8px;">LLM</div>
      <div style="padding:6px 12px;font-size:11px;color:#a7aaad;">
        <div>Provider: <span id="llm-provider" style="color:#00e5ff">mock</span></div>
        <div>Model: <span id="llm-model" style="color:#ccc">—</span></div>
        <div>Key: <span id="llm-key" style="color:#f59e0b">❌ No key</span></div>
      </div>
"""

html = html.replace("</nav>", SIDEBAR_PANELS + "\n    </nav>", 1)

# ── 2. Add Tools + Feedback panels to Overview page
OVERVIEW_EXTRA = """

      <!-- Tools & Feedback Row -->
      <div class="cards-grid" style="grid-template-columns:1fr 1fr;margin-top:0;">

        <!-- Tools Panel -->
        <div class="wp-card card-blue">
          <h3>🔧 Active Tools <span id="tools-health" style="font-size:10px;color:var(--muted);font-weight:400"></span></h3>
          <div id="tools-panel" style="font-size:12px;color:var(--muted);">Loading...</div>
        </div>

        <!-- Feedback Panel -->
        <div class="wp-card card-ok">
          <h3>📈 Performance</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
            <div style="text-align:center;">
              <div class="stat-number" id="fb-total" style="font-size:24px;">0</div>
              <div class="stat-label">Tasks</div>
            </div>
            <div style="text-align:center;">
              <div class="stat-number" id="fb-rate" style="font-size:24px;color:var(--green)">—</div>
              <div class="stat-label">Success Rate</div>
            </div>
          </div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:4px;">Avg: <strong id="fb-avg">—</strong></div>
          <div style="font-size:11px;font-weight:600;margin-bottom:4px;">💡 Suggestions:</div>
          <div id="fb-tips" style="color:var(--muted);font-size:11px;">Loading...</div>
        </div>
      </div>

      <!-- Site Latency Badge -->
      <div style="font-size:12px;color:var(--muted);margin-bottom:16px;">
        Latency: <strong id="site-latency">—</strong>
      </div>
"""

# Insert after overview-cards div
html = html.replace(
    '<div class="ai-analysis"',
    OVERVIEW_EXTRA + '\n      <div class="ai-analysis"',
    1
)

# ── 3. Add LLM Config panel to Settings page
LLM_PANEL = """
      <div class="wp-card" style="margin-top:16px;">
        <h3>🤖 LLM Configuration</h3>
        <div style="display:grid;gap:12px;max-width:500px;">
          <div>
            <label style="font-size:13px;">Provider</label><br>
            <select id="llm-provider-sel" style="width:100%;padding:7px;border:1px solid var(--wp-border);border-radius:3px;margin-top:4px;font-size:13px;">
              <option value="mock">Mock (Testing — no API needed)</option>
              <option value="claude">Claude (Anthropic)</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="ollama">Ollama (Local — Free)</option>
            </select>
          </div>
          <div>
            <label style="font-size:13px;">API Key</label><br>
            <input type="password" id="llm-key-input" placeholder="sk-..." style="width:100%;padding:7px;border:1px solid var(--wp-border);border-radius:3px;margin-top:4px;font-size:13px;">
          </div>
          <div>
            <label style="font-size:13px;">Model</label><br>
            <input type="text" id="llm-model-input" placeholder="claude-sonnet-4-5 / gpt-4o-mini / llama3" style="width:100%;padding:7px;border:1px solid var(--wp-border);border-radius:3px;margin-top:4px;font-size:13px;">
          </div>
          <div>
            <label style="font-size:13px;">Base URL (Ollama only)</label><br>
            <input type="url" id="llm-base-url" placeholder="http://localhost:11434" style="width:100%;padding:7px;border:1px solid var(--wp-border);border-radius:3px;margin-top:4px;font-size:13px;">
          </div>
          <button class="btn btn-primary" onclick="saveLLMConfig()">💾 Save LLM Config</button>
          <p style="font-size:11px;color:var(--muted);">
            💡 Ollama = local free LLM. Claude/OpenAI require API key.<br>
            Current status: Provider=<strong id="llm-provider-badge">—</strong>, Key=<strong id="llm-key-badge">—</strong>
          </p>
        </div>
      </div>
"""

html = html.replace(
    "<!-- ══ MEDIA & USERS ══ -->",
    LLM_PANEL + "\n    <!-- ══ MEDIA & USERS ══ -->",
    1
)

# ── 4. Inject live_dashboard.js before </body>
LIVE_JS_INCLUDE = """
<script>
// ══════════════════════════════════════════
//  LIVE POLLING ENGINE
// ══════════════════════════════════════════
const POLL_INTERVAL = 5000;
let _pollTimer = null;

async function startLivePolling() {
  if (_pollTimer) return;
  _pollTimer = setInterval(pollSystemStatus, POLL_INTERVAL);
  pollSystemStatus();
}

async function pollSystemStatus() {
  try {
    const r = await fetch(state.agentUrl + '/system/status');
    if (!r.ok) { setGlobalStatus(false); return; }
    const d = await r.json();
    updateSystemPanel(d);
    updateSitesFromAwareness(d.awareness);
    updateToolsPanel(d.tools, d.tools_health);
    updateFeedbackPanel(d.feedback, d.improvements);
    updateLLMStatus(d.llm);
  } catch(e) { setGlobalStatus(false); }
}

function updateSystemPanel(d) {
  const aw = d.awareness || {};
  setGlobalStatus(true);
  const gs = document.getElementById('global-status');
  if (gs) {
    gs.className = 'pill connected';
    gs.textContent = aw.current_task ? '⬤ Running: ' + aw.current_task.slice(0,25) : '⬤ Idle';
  }
  const s = id => document.getElementById(id);
  if (s('ov-status'))  s('ov-status').textContent  = aw.is_running ? '🔄 Running' : '✅ Idle';
  if (s('sys-uptime')) s('sys-uptime').textContent = formatUptime(aw.uptime_seconds);
  if (s('sys-tasks'))  s('sys-tasks').textContent  = aw.tasks_done || 0;
  if (s('sys-rate'))   s('sys-rate').textContent   = (aw.success_rate || 0) + '%';
}

function updateSitesFromAwareness(awareness) {
  if (!awareness || !awareness.sites) return;
  awareness.sites.forEach(s => {
    const ex = state.sites.find(x => x.name === s.name);
    if (ex) { ex.connected = s.connection === 'connected'; }
    else { state.sites.push({name: s.name, url: s.url, key: '', connected: s.connection === 'connected'}); }
  });
  renderSitesList();
  if (state.currentSite) {
    const sd = awareness.sites.find(s => s.name === state.currentSite.name);
    if (sd) {
      const el = id => document.getElementById(id);
      if (el('ov-status'))  el('ov-status').textContent  = sd.connection === 'connected' ? '✅ Connected' : '❌ Disconnected';
      if (el('ov-plugins')) el('ov-plugins').textContent = sd.plugins_active || '—';
      if (el('site-latency')) el('site-latency').textContent = sd.latency_ms ? sd.latency_ms.toFixed(0) + 'ms' : '—';
      const gs = document.getElementById('global-status');
      if (gs) { gs.className = 'pill ' + (sd.connection==='connected' ? 'connected':'disconnected'); }
    }
  }
}

function updateToolsPanel(tools, health) {
  const panel = document.getElementById('tools-panel');
  if (!panel || !tools) return;
  const clr = {idle:'#10b981', busy:'#f59e0b', error:'#ef4444'};
  panel.innerHTML = tools.map(t =>
    `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--wp-border);font-size:11px;">
       <span><strong>${t.name}</strong> <span style="color:var(--muted)">[${t.type}]</span> · ${t.call_count} calls</span>
       <span style="color:${clr[t.status]||'#999'};font-weight:700">${t.status}</span>
     </div>`
  ).join('');
  const hel = document.getElementById('tools-health');
  if (hel && health) hel.textContent = `(${health.idle}/${health.total} idle${health.errors?' · '+health.errors+' err':''})`;
}

function updateFeedbackPanel(stats, improvements) {
  if (!stats) return;
  const s = id => document.getElementById(id);
  if (s('fb-total')) s('fb-total').textContent = stats.total || 0;
  if (s('fb-rate'))  s('fb-rate').textContent  = (stats.success_rate || 0) + '%';
  if (s('fb-avg'))   s('fb-avg').textContent   = (stats.avg_duration || 0).toFixed(1) + 's';
  if (s('fb-tips'))  s('fb-tips').innerHTML    = (improvements || [])
    .map(tip => `<div style="padding:3px 0;border-bottom:1px solid var(--wp-border);font-size:11px;">${tip}</div>`)
    .join('') || '<span style="color:var(--muted)">✅ System healthy</span>';
}

function updateLLMStatus(llm) {
  if (!llm) return;
  const s = id => document.getElementById(id);
  if (s('llm-provider'))      s('llm-provider').textContent      = llm.provider || 'mock';
  if (s('llm-model'))         s('llm-model').textContent         = llm.model    || '—';
  if (s('llm-key'))           s('llm-key').textContent           = llm.has_key  ? '✅ Key set' : '❌ No key';
  if (s('llm-provider-badge'))s('llm-provider-badge').textContent= llm.provider || '—';
  if (s('llm-key-badge'))     s('llm-key-badge').textContent     = llm.has_key  ? '✅' : '❌';
  const sel = s('llm-provider-sel');
  if (sel && llm.provider) sel.value = llm.provider;
}

function setGlobalStatus(online) {
  const el = document.getElementById('global-status');
  if (!el || online) return;
  el.className = 'pill disconnected';
  el.textContent = '⬤ Agent Offline';
}

function formatUptime(sec) {
  if (!sec) return '0s';
  const h = Math.floor(sec/3600), m = Math.floor((sec%3600)/60), s = sec%60;
  return h ? h+'h '+m+'m' : m ? m+'m '+s+'s' : s+'s';
}

async function saveLLMConfig() {
  const r = await fetch(state.agentUrl + '/llm/configure', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      provider: document.getElementById('llm-provider-sel')?.value || 'mock',
      api_key:  document.getElementById('llm-key-input')?.value   || '',
      model:    document.getElementById('llm-model-input')?.value || '',
      base_url: document.getElementById('llm-base-url')?.value    || '',
    })
  });
  const d = await r.json();
  log(d.success ? '✅ LLM: ' + d.config.provider + ' / ' + d.config.model : '❌ ' + d.error);
  pollSystemStatus();
}

async function searchKnowledge() {
  const q = document.getElementById('kb-search')?.value || '';
  const r = await fetch(state.agentUrl + '/wp/knowledge/search', {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:q})
  });
  const d  = await r.json();
  const el = document.getElementById('kb-results');
  if (!el) return;
  el.innerHTML = (d.results||[]).map(item =>
    `<div style="padding:10px;border:1px solid var(--wp-border);border-radius:4px;margin-bottom:8px;">
       <strong>${item.title||item.source}</strong>
       <span style="font-size:10px;color:var(--muted);margin-right:6px">[${item.type}]</span>
       <p style="font-size:12px;color:var(--muted);margin-top:4px">${item.snippet||''}</p>
     </div>`
  ).join('') || '<p style="color:var(--muted)">No results</p>';
}

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(startLivePolling, 500);
});
</script>
</body>"""

html = html.replace("</body>", LIVE_JS_INCLUDE, 1)

# Backup + write
with open(TARGET + ".bak", "w", encoding="utf-8") as f:
    f.write(html[:1000])   # small backup marker

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard patched — {len(html)} chars")
