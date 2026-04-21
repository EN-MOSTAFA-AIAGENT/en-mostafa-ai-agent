"""
Fix dashboard JS:
1. Load sites from server on startup
2. Fix sidebar + button
3. Fix site selector dropdown
4. Fix addSite() to refresh after add
"""
import os, re

TARGET = r"C:\mcp-agent\templates\wp-dashboard.html"
html   = open(TARGET, encoding="utf-8", errors="replace").read()

# ── Fix 1: Load sites from server on window.onload
OLD_ONLOAD = """window.onload = () => {
  renderSitesList();
  updateClock();
  setInterval(updateClock, 1000);
  document.getElementById('agent-url-input').value = state.agentUrl;
  if (state.sites.length) autoSelectSite(state.sites[0]);
};"""

NEW_ONLOAD = """window.onload = async () => {
  updateClock();
  setInterval(updateClock, 1000);
  const agentInput = document.getElementById('agent-url-input');
  if (agentInput) agentInput.value = state.agentUrl;

  // Load sites from server (not just localStorage)
  await loadSitesFromServer();

  if (state.sites.length) {
    autoSelectSite(state.sites[0]);
    // Auto-select in dropdown
    const sel = document.getElementById('site-selector');
    if (sel && state.sites[0]) sel.value = state.sites[0].name;
  }
};

async function loadSitesFromServer() {
  try {
    const r = await fetch(state.agentUrl + '/wp/sites');
    if (!r.ok) return;
    const d = await r.json();
    const serverSites = d.sites || [];
    // Merge with localStorage (keep api_key from localStorage)
    serverSites.forEach(ss => {
      const local = state.sites.find(x => x.name === ss.name);
      if (!local) {
        state.sites.push({ name: ss.name, url: ss.url, key: '', connected: ss.connection === 'connected' });
      } else {
        local.connected = ss.connection === 'connected';
        local.url       = ss.url;
      }
    });
    localStorage.setItem('aiwa_sites', JSON.stringify(state.sites));
    renderSitesList();
  } catch(e) {}
}"""

if OLD_ONLOAD in html:
    html = html.replace(OLD_ONLOAD, NEW_ONLOAD, 1)
    print("Fixed: window.onload — loads sites from server")
else:
    print("WARN: onload pattern not found — appending fix")
    # append before </script> of main script
    html = html.replace(
        "document.addEventListener('DOMContentLoaded', () => {",
        "document.addEventListener('DOMContentLoaded', () => { loadSitesFromServer();",
        1
    )

# ── Fix 2: addSite() — refresh after adding
OLD_ADDSITE_END = """    chrome.storage.local.set({sites});
        renderSitesList(sites);
      });"""

# This pattern may not exist in this dashboard — use a different approach
# Find addSite function and fix it
OLD_ADDSITE = """async function addSite() {
  const name = document.getElementById('ns-name').value.trim();
  const url  = document.getElementById('ns-url').value.trim();
  const key  = document.getElementById('ns-key').value.trim();
  if (!name || !url || !key) return alert('أدخل كل الحقول');
  state.sites.push({name, url, key, connected: false});
  localStorage.setItem('aiwa_sites', JSON.stringify(state.sites));
  renderSitesList();
  // Register on agent
  agentPost('/wp/add-site', {name, url, api_key: key}).then(() => log('Site added: ' + name));
  document.getElementById('ns-name').value = '';
  document.getElementById('ns-url').value  = '';
  document.getElementById('ns-key').value  = '';
}"""

NEW_ADDSITE = """async function addSite() {
  const name = document.getElementById('ns-name').value.trim();
  const url  = document.getElementById('ns-url').value.trim();
  const key  = document.getElementById('ns-key').value.trim();
  if (!name || !url || !key) { log('أدخل كل الحقول (اسم، URL، API Key)', 'warn'); return; }

  log('جارٍ إضافة الموقع: ' + name, 'info');

  try {
    const r = await fetch(state.agentUrl + '/wp/add-site', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ name, url, api_key: key })
    });
    const d = await r.json();

    if (d.success) {
      // Add to local state
      const existing = state.sites.find(s => s.name === name);
      if (!existing) {
        state.sites.push({ name, url, key, connected: d.connected || false });
      } else {
        existing.connected = d.connected || false;
      }
      localStorage.setItem('aiwa_sites', JSON.stringify(state.sites));
      renderSitesList();

      // Update selector
      const sel = document.getElementById('site-selector');
      if (sel) {
        sel.innerHTML = '<option value="">— اختر موقع —</option>' +
          state.sites.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
        sel.value = name;
      }

      log('✅ تم إضافة الموقع: ' + name + (d.connected ? ' (متصل)' : ' (غير متصل)'), 'info');

      // Clear inputs
      document.getElementById('ns-name').value = '';
      document.getElementById('ns-url').value  = '';
      document.getElementById('ns-key').value  = '';

      // Auto-switch to new site
      switchSite(name);
      showPage('overview');

    } else {
      log('❌ فشل إضافة الموقع: ' + (d.error || 'خطأ غير معروف'), 'err');
    }
  } catch(e) {
    log('❌ خطأ في الاتصال: ' + e.message, 'err');
  }
}"""

if OLD_ADDSITE in html:
    html = html.replace(OLD_ADDSITE, NEW_ADDSITE, 1)
    print("Fixed: addSite() — now shows feedback and auto-switches")
else:
    # Try partial match
    if "agentPost('/wp/add-site'" in html:
        # Replace the agentPost call with proper fetch
        html = html.replace(
            "agentPost('/wp/add-site', {name, url, api_key: key}).then(() => log('Site added: ' + name));",
            """fetch(state.agentUrl + '/wp/add-site', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name, url, api_key: key})
    }).then(r=>r.json()).then(d=>{
      if(d.success){ log('✅ تم: '+name+' '+(d.connected?'(متصل)':''), 'info'); switchSite(name); }
      else { log('❌ '+d.error, 'err'); }
      loadSitesFromServer();
    });""",
            1
        )
        print("Fixed: addSite() agentPost → fetch with feedback")
    else:
        print("WARN: addSite pattern not found")

# ── Fix 3: renderSitesList — also update the dropdown
OLD_RENDER = """function renderSitesList() {
  const sel  = document.getElementById('site-selector');
  const list = document.getElementById('sites-list');
  sel.innerHTML  = '<option value="">— اختر موقع —</option>';
  list.innerHTML = '';
  state.sites.forEach(s => {
    sel.innerHTML += `<option value="${s.name}">${s.name}</option>`;
    list.innerHTML += `<div class="site-item" onclick="switchSite('${s.name}')"><span class="site-dot ${s.connected?'ok':'err'}"></span>${s.name}</div>`;
  });
}"""

NEW_RENDER = """function renderSitesList() {
  const sel  = document.getElementById('site-selector');
  const list = document.getElementById('sites-list');
  if (sel) {
    const prev = sel.value;
    sel.innerHTML = '<option value="">— اختر موقع —</option>';
    state.sites.forEach(s => {
      sel.innerHTML += `<option value="${s.name}">${s.connected ? '🟢' : '🔴'} ${s.name}</option>`;
    });
    if (prev) sel.value = prev;
  }
  if (list) {
    list.innerHTML = '';
    if (!state.sites.length) {
      list.innerHTML = '<div style="color:#6b7280;font-size:11px;padding:8px;text-align:center">لا يوجد مواقع<br><small>أضف موقعاً من الإعدادات</small></div>';
      return;
    }
    state.sites.forEach(s => {
      list.innerHTML += `<div class="site-item ${s.name === state.currentSite?.name ? 'active' : ''}"
        onclick="switchSite('${s.name}');document.getElementById('site-selector').value='${s.name}'">
        <span class="site-dot ${s.connected ? 'ok' : 'err'}"></span>
        <span>${s.name}</span>
        <span style="font-size:9px;color:#6b7280;margin-right:auto">${s.connected ? 'متصل' : 'غير متصل'}</span>
      </div>`;
    });
  }
}"""

if OLD_RENDER in html:
    html = html.replace(OLD_RENDER, NEW_RENDER, 1)
    print("Fixed: renderSitesList() — shows connection status + emoji")
else:
    print("WARN: renderSitesList pattern not found")

# ── Fix 4: saveAgentURL — also reload sites
OLD_SAVE = """function saveAgentURL() {
  state.agentUrl = document.getElementById('agent-url-input').value.trim();
  localStorage.setItem('aiwa_agent_url', state.agentUrl);
  log('✅ Agent URL saved: ' + state.agentUrl);
}"""

NEW_SAVE = """function saveAgentURL() {
  state.agentUrl = document.getElementById('agent-url-input').value.trim();
  localStorage.setItem('aiwa_agent_url', state.agentUrl);
  log('✅ Agent URL saved: ' + state.agentUrl);
  loadSitesFromServer();
  pollSystemStatus();
}"""

if OLD_SAVE in html:
    html = html.replace(OLD_SAVE, NEW_SAVE, 1)
    print("Fixed: saveAgentURL() — reloads sites after save")

# ── Write
with open(TARGET, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nDashboard updated — {len(html)} chars")
print("Reload http://127.0.0.1:5001/wp-dashboard in browser")
