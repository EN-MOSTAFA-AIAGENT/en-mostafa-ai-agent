// AI WordPress Agent — Background Service Worker
const AGENT_URL = 'http://localhost:5001';

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const post = (path, body) =>
    fetch(AGENT_URL + path, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    }).then(r => r.json()).then(d => sendResponse({ok: true, data: d}))
      .catch(e => sendResponse({ok: false, error: e.message}));

  if (msg.type === 'PING_AGENT')    { fetch(AGENT_URL + '/healthz').then(r=>r.json()).then(d=>sendResponse({ok:true,data:d})).catch(e=>sendResponse({ok:false,error:e.message})); return true; }
  if (msg.type === 'RUN_TASK')      { post('/run',              {task: msg.task, site: msg.site}); return true; }
  if (msg.type === 'SYSTEM_STATUS') { fetch(AGENT_URL + '/system/status').then(r=>r.json()).then(d=>sendResponse({ok:true,data:d})).catch(e=>sendResponse({ok:false,error:e.message})); return true; }
  if (msg.type === 'WP_ACTION')     { post(msg.endpoint,        msg.payload); return true; }
  if (msg.type === 'REGISTER_SITE') { post('/wp/register-site', msg.payload); return true; }
  if (msg.type === 'LEARN_URL')     { post('/wp/knowledge/learn-url', {url: msg.url}); return true; }
});

chrome.contextMenus.create({id:'send-to-agent', title:'Send to AI Agent', contexts:['page','selection']});
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'send-to-agent') {
    const task = info.selectionText ? 'Analyze: ' + info.selectionText : 'Analyze page: ' + tab.url;
    fetch(AGENT_URL + '/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({task})});
  }
});
