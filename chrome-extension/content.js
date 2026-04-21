// AI WordPress Agent — Content Script (Fallback DOM Control)
(function () {
  'use strict';
  // URL يُقرأ من chrome.storage — fallback لـ localhost أثناء التطوير
  let AGENT = 'http://127.0.0.1:5001';
  chrome.storage?.local.get('agentUrl', r => { if (r?.agentUrl) AGENT = r.agentUrl; });

  // ── DOM Analysis ──────────────────────────────────────
  function analyzePage() {
    return {
      url:        location.href,
      title:      document.title,
      wpVersion:  document.querySelector('meta[name=generator]')?.content || '',
      isWP:       !!(document.getElementById('wpadminbar') || document.body.classList.contains('wp-admin')),
      isElementor:!!document.querySelector('[data-elementor-type]'),
      isLearnDash:!!(document.querySelector('.learndash-wrapper') || location.pathname.includes('/course')),
      pageType:   detectPageType(),
      forms:      document.querySelectorAll('form').length,
      links:      document.querySelectorAll('a').length,
      images:     document.querySelectorAll('img').length,
      h1:         document.querySelector('h1')?.innerText?.trim() || '',
      adminBar:   !!document.getElementById('wpadminbar'),
    };
  }

  function detectPageType() {
    const p = location.pathname;
    if (p.includes('/wp-admin'))              return 'wp-admin';
    if (p.includes('/wp-login'))              return 'wp-login';
    if (p.includes('/checkout'))              return 'woocommerce-checkout';
    if (p.includes('/course') || p.includes('/lesson')) return 'learndash';
    if (document.querySelector('[data-elementor-type]')) return 'elementor';
    return 'frontend';
  }

  // ── DOM Commands ──────────────────────────────────────
  function execCommand(cmd) {
    try {
      switch (cmd.action) {
        case 'click': {
          const el = document.querySelector(cmd.selector);
          if (!el) return {ok: false, error: 'Selector not found: ' + cmd.selector};
          el.click();
          return {ok: true, selector: cmd.selector};
        }
        case 'type': {
          const inp = document.querySelector(cmd.selector);
          if (!inp) return {ok: false, error: 'Input not found: ' + cmd.selector};
          inp.focus();
          inp.value = cmd.value || '';
          inp.dispatchEvent(new Event('input',  {bubbles: true}));
          inp.dispatchEvent(new Event('change', {bubbles: true}));
          return {ok: true};
        }
        case 'scroll': {
          const amount = parseInt(cmd.amount) || 300;
          if (cmd.selector) {
            document.querySelector(cmd.selector)?.scrollIntoView({behavior: 'smooth'});
          } else {
            window.scrollBy({top: amount, behavior: 'smooth'});
          }
          return {ok: true, amount};
        }
        case 'getText': {
          const el = document.querySelector(cmd.selector);
          return {ok: true, text: el?.innerText?.trim() || ''};
        }
        case 'setAttribute': {
          const el = document.querySelector(cmd.selector);
          if (!el) return {ok: false, error: 'Not found'};
          el.setAttribute(cmd.attr, cmd.value);
          return {ok: true};
        }
        case 'getElementorData': {
          const data = window._elementorConfig
            || window.elementorFrontend?.config
            || Array.from(document.querySelectorAll('[data-elementor-type]'))
               .map(el => el.getAttribute('data-elementor-type'));
          return {ok: true, data};
        }
        case 'findWPNonce': {
          const nonce = document.querySelector('#_wpnonce')?.value
            || window.wpApiSettings?.nonce || '';
          return {ok: true, nonce};
        }
        case 'getPageHTML': {
          return {ok: true, html: document.documentElement.outerHTML.slice(0, 10000)};
        }
        case 'screenshot': {
          return {ok: true, info: analyzePage(), note: 'Use Playwright for real screenshots'};
        }
        default:
          return {ok: false, error: 'Unknown action: ' + cmd.action};
      }
    } catch (e) {
      return {ok: false, error: e.message};
    }
  }

  // ── Interactive Overlay ───────────────────────────────
  function showOverlay(text, color, duration) {
    let el = document.getElementById('__aiwa_overlay__');
    if (!el) {
      el = document.createElement('div');
      el.id = '__aiwa_overlay__';
      Object.assign(el.style, {
        position:   'fixed',
        top:        '12px',
        left:       '50%',
        transform:  'translateX(-50%)',
        zIndex:     '2147483647',
        padding:    '10px 24px',
        borderRadius: '6px',
        fontFamily: 'monospace',
        fontSize:   '13px',
        fontWeight: '700',
        boxShadow:  '0 4px 20px rgba(0,0,0,.4)',
        transition: 'opacity .4s',
        pointerEvents: 'none',
        maxWidth:   '80vw',
        wordBreak:  'break-all',
      });
      document.body.appendChild(el);
    }
    el.style.background = color || '#2271b1';
    el.style.color      = '#fff';
    el.style.opacity    = '1';
    el.textContent      = text;
    setTimeout(() => { el.style.opacity = '0'; }, duration || 3000);
  }

  // ── Message listener ──────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'ANALYZE_DOM')   { sendResponse({ok: true,  data: analyzePage()}); }
    if (msg.type === 'EXEC_COMMAND')  { sendResponse(execCommand(msg.command)); }
    if (msg.type === 'SHOW_OVERLAY')  { showOverlay(msg.text, msg.color, msg.duration); sendResponse({ok: true}); }
    if (msg.type === 'SCROLL_TO_TOP') { window.scrollTo({top: 0, behavior: 'smooth'}); sendResponse({ok: true}); }
    return true;
  });

  // ── Auto-heartbeat from WP Admin pages ───────────────
  if (location.pathname.includes('/wp-admin') || document.getElementById('wpadminbar')) {
    try {
      fetch(AGENT + '/wp/heartbeat', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({
          site_url:   location.origin,
          source:     'chrome_extension',
          page_type:  detectPageType(),
          wp_version: document.querySelector('meta[name=generator]')?.content || '',
        }),
      }).catch(() => {});
    } catch (e) {}
  }

})();
