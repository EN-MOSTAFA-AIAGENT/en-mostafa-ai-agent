// live_dashboard.js — injected at bottom of wp-dashboard.html
// ═══════════════════════════════════════════════════════
//  LIVE POLLING ENGINE — connects Dashboard to Agent
// ═══════════════════════════════════════════════════════

const POLL_INTERVAL = 5000;  // 5 seconds
let _pollTimer = null;

// ── Main poll ────────────────────────────────────────
async function startLivePolling() {
  if (_pollTimer) return;
  _pollTimer = setInterval(pollSystemStatus, POLL_INTERVAL);
  pollSystemStatus(); // immediate first call
  console.log('[Dashboard] Live polling started');
}

async function pollSystemStatus() {
  try {
    const r = await fetch(state.agentUrl + '/system/status');
    if (!r.ok) return;
    const d = await r.json();
    updateSystemPanel(d);
    updateSitesFromAwareness(d.awareness);
    updateToolsPanel(d.tools, d.tools_health);
    updateFeedbackPanel(d.feedback, d.improvements);
    updateLLMStatus(d.llm);
  } catch(e) {
    setGlobalStatus(false);
  }
}

// ── System Panel ─────────────────────────────────────
function updateSystemPanel(d) {
  const aw = d.awareness || {};
  setGlobalStatus(true);

  // Running task
  if (aw.current_task) {
    document.getElementById('global-status').textContent = '⬤ Running: ' + aw.current_task.slice(0,30);
    document.getElementById('global-status').className = 'pill connected';
  } else {
    document.getElementById('global-status').textContent = '⬤ Idle';
    document.getElementById('global-status').className = 'pill connected';
  }

  // Overview cards
  const el = id => document.getElementById(id);
  if (el('ov-status'))  el('ov-status').textContent  = aw.is_running ? '🔄 Running' : '✅ Idle';
  if (el('sys-uptime')) el('sys-uptime').textContent = formatUptime(aw.uptime_seconds);
  if (el('sys-tasks'))  el('sys-tasks').textContent  = aw.tasks_done || 0;
  if (el('sys-rate'))   el('sys-rate').textContent   = (aw.success_rate || 0) + '%';
}

// ── Sites Status (Heartbeat-based) ───────────────────
function updateSitesFromAwareness(awareness) {
  if (!awareness || !awareness.sites) return;
  const sites = awareness.sites;

  // Sync local state with real data
  sites.forEach(s => {
    const existing = state.sites.find(x => x.name === s.name);
    if (!existing) {
      state.sites.push({ name: s.name, url: s.url, connected: s.connection === 'connected' });
    } else {
      existing.connected = s.connection === 'connected';
    }
  });

  renderSitesList();

  // Update current site widgets if selected
  if (state.currentSite) {
    const siteData = sites.find(s => s.name === state.currentSite.name);
    if (siteData) {
      updateSiteCards(siteData);
    }
  }
}

function updateSiteCards(siteData) {
  const connected = siteData.connection === 'connected';
  const el = id => document.getElementById(id);

  if (el('ov-status'))  el('ov-status').textContent  = connected ? '✅ Connected' : '❌ Disconnected';
  if (el('ov-plugins')) el('ov-plugins').textContent = siteData.plugins_active || '—';

  const statusEl = document.getElementById('global-status');
  if (statusEl) {
    statusEl.className  = 'pill ' + (connected ? 'connected' : 'disconnected');
    statusEl.textContent = '⬤ ' + (connected ? 'Connected' : 'Disconnected');
  }

  // Latency badge
  if (el('site-latency')) {
    el('site-latency').textContent = siteData.latency_ms
      ? siteData.latency_ms.toFixed(0) + 'ms'
      : '—';
  }
}

// ── Tools Panel ──────────────────────────────────────
function updateToolsPanel(tools, health) {
  const panel = document.getElementById('tools-panel');
  if (!panel || !tools) return;

  const statusColor = { idle:'#10b981', busy:'#f59e0b', error:'#ef4444', active:'#2271b1' };
  panel.innerHTML = tools.map(t => `
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:6px 10px;border-bottom:1px solid var(--wp-border);font-size:12px;">
      <span><strong>${t.name}</strong> <span style="color:var(--muted);font-size:10px">[${t.type}]</span></span>
      <span style="color:${statusColor[t.status]||'#999'};font-weight:600">${t.status.toUpperCase()}</span>
    </div>
  `).join('');

  if (health && document.getElementById('tools-health')) {
    document.getElementById('tools-health').textContent =
      `${health.idle}/${health.total} idle · ${health.errors} errors`;
  }
}

// ── Feedback Panel ───────────────────────────────────
function updateFeedbackPanel(stats, improvements) {
  if (!stats) return;
  const s = id => document.getElementById(id);
  if (s('fb-total'))   s('fb-total').textContent   = stats.total || 0;
  if (s('fb-rate'))    s('fb-rate').textContent     = (stats.success_rate || 0) + '%';
  if (s('fb-avg'))     s('fb-avg').textContent      = (stats.avg_duration || 0).toFixed(1) + 's';
  if (s('fb-tips')) {
    s('fb-tips').innerHTML = (improvements || []).map(tip =>
      `<div style="font-size:11px;padding:4px 0;border-bottom:1px solid var(--wp-border)">${tip}</div>`
    ).join('') || '<span style="color:var(--muted);font-size:11px">No issues detected</span>';
  }
}

// ── LLM Status ───────────────────────────────────────
function updateLLMStatus(llm) {
  if (!llm) return;
  const el = id => document.getElementById(id);
  if (el('llm-provider')) el('llm-provider').textContent = llm.provider || 'mock';
  if (el('llm-model'))    el('llm-model').textContent    = llm.model    || '—';
  if (el('llm-key'))      el('llm-key').textContent      = llm.has_key  ? '✅ Key set' : '❌ No key';
}

// ── Helpers ──────────────────────────────────────────
function setGlobalStatus(online) {
  const el = document.getElementById('global-status');
  if (!el) return;
  if (!online) {
    el.className = 'pill disconnected';
    el.textContent = '⬤ Agent Offline';
  }
}

function formatUptime(seconds) {
  if (!seconds) return '0s';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return h ? `${h}h ${m}m` : m ? `${m}m ${s}s` : `${s}s`;
}

// ── LLM Configure helper ─────────────────────────────
async function saveLLMConfig() {
  const provider = document.getElementById('llm-provider-sel')?.value || 'mock';
  const api_key  = document.getElementById('llm-key-input')?.value   || '';
  const model    = document.getElementById('llm-model-input')?.value || '';
  const r = await fetch(state.agentUrl + '/llm/configure', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ provider, api_key, model })
  });
  const d = await r.json();
  log(d.success ? `✅ LLM configured: ${d.config.provider} / ${d.config.model}` : '❌ ' + d.error);
}

// ── Knowledge search helper ──────────────────────────
async function searchKnowledge() {
  const q  = document.getElementById('kb-search')?.value || '';
  const r  = await fetch(state.agentUrl + '/wp/knowledge/search', {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({query: q})
  });
  const d  = await r.json();
  const el = document.getElementById('kb-results');
  if (!el) return;
  el.innerHTML = (d.results || []).map(item => `
    <div style="padding:10px;border:1px solid var(--wp-border);border-radius:4px;margin-bottom:8px;">
      <strong style="font-size:13px;">${item.title || item.source}</strong>
      <span style="font-size:10px;color:var(--muted);margin-right:6px;">[${item.type}]</span>
      <p style="font-size:12px;color:var(--muted);margin-top:4px;">${item.snippet || ''}</p>
    </div>`).join('') || '<p style="color:var(--muted)">No results found</p>';
}

// ── Auto-start polling when page loads ───────────────
document.addEventListener('DOMContentLoaded', () => {
  startLivePolling();
});
