# 🤖 AI WordPress Control Center v2.0
### EN MOSTAFA AI AGENT

نظام متكامل لإدارة مواقع WordPress باستخدام الذكاء الاصطناعي.

---

## 🚀 التشغيل السريع

```bash
# 1. Setup (مرة واحدة فقط)
py -3.11 setup.py

# 2. Start Server
py -3.11 server.py
# OR
start.bat

# 3. Open Dashboard
http://localhost:5001/wp-dashboard
```

---

## 🏗️ المعمارية

```
┌─────────────────────────────────────────────────────┐
│                  Agent Server :5001                  │
│                                                      │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │  AgentCore   │◄──►│   Integration Layer      │   │
│  │              │    │  (Unified Tool Interface) │   │
│  └──────┬───────┘    └──────────────────────────┘   │
│         │                                            │
│  ┌──────▼────────────────────────────────────────┐  │
│  │           Multi-Agent Orchestrator             │  │
│  │  🎨 Creative  ⚙️ Technical  🎓 Educator        │  │
│  └──────┬────────────────────────────────────────┘  │
│         │                                            │
│  ┌──────▼──────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ WPManager   │ │ LLMBridge│ │ KnowledgeManager  │ │
│  │ (Multi-Site)│ │Claude/GPT│ │ PDF/TXT/URL/Plugin│ │
│  └──────┬──────┘ └──────────┘ └───────────────────┘ │
│         │                                            │
│  ┌──────▼──────┐ ┌──────────┐ ┌───────────────────┐ │
│  │SystemAwarns │ │FeedbackLp│ │ ToolRegistry      │ │
│  │ Heartbeat   │ │ Learning │ │ 7 tools unified   │ │
│  └─────────────┘ └──────────┘ └───────────────────┘ │
└─────────────────────────────────────────────────────┘
         ▲                    ▲
         │                    │
┌────────┴────────┐  ┌────────┴────────┐
│ WordPress Plugin│  │Chrome Extension │
│  REST API v1    │  │ Fallback DOM    │
│  Heartbeat 60s  │  │ Context Menu    │
│  Self-Heal      │  │ Popup UI        │
└─────────────────┘  └─────────────────┘
```

---

## 📁 ملفات المشروع

### Python Agent
| الملف | الوظيفة |
|---|---|
| `server.py` | Flask REST Server — نقطة الدخول الرئيسية |
| `agent_core.py` | المركز الرئيسي + Integration Layer |
| `multi_agent.py` | Creative / Technical / Educator agents |
| `wp_manager.py` | Multi-site WordPress Python Client |
| `wp_routes.py` | كل WordPress API routes (Blueprint) |
| `knowledge_manager.py` | تعلم من PDF/TXT/URL/Plugin كامل |
| `llm_bridge.py` | Claude / OpenAI / Ollama interface |
| `tool_registry.py` | Unified Tool Interface |
| `system_awareness.py` | وعي كامل بحالة النظام |
| `feedback_loop.py` | تحسين مستمر بعد كل تنفيذ |

### WordPress Plugin (`wordpress-plugin/ai-wordpress-agent/`)
| الملف | الوظيفة |
|---|---|
| `ai-wordpress-agent.php` | Main plugin — Auto-registers with Agent |
| `includes/class-aiwa-api.php` | 14 REST endpoints |
| `includes/class-aiwa-heartbeat.php` | Heartbeat كل دقيقة |
| `includes/class-aiwa-selfheal.php` | Self-Healing Firewall |
| `admin/class-aiwa-dashboard.php` | WordPress Admin Panel |

### Chrome Extension (`chrome-extension/`)
| الملف | الوظيفة |
|---|---|
| `manifest.json` | Manifest v3 |
| `background.js` | Service Worker — Agent Bridge |
| `content.js` | DOM Analysis + Commands |
| `popup.html` | Extension UI |

---

## 🌐 API Endpoints

### Agent Server
```
GET  /                    Health check
GET  /system/status       Full system snapshot
POST /run                 Execute any task (Local + Remote)
GET  /wp-dashboard        WordPress-like Dashboard HTML

POST /wp/register-site    Register WordPress site with Agent
POST /wp/site-info        Get site information
GET  /wp/sites-status     All sites connection status
POST /wp/plugins          List plugins
POST /wp/update-plugins   Update all plugins
POST /wp/toggle-plugin    Activate / Deactivate plugin
POST /wp/elementor-get    Read Elementor JSON
POST /wp/elementor-set    Update Elementor JSON
POST /wp/courses          List LearnDash courses
POST /wp/create-course    Create LearnDash course
POST /wp/analyze          AI site analysis
POST /wp/auto-heal        Self-healing execution
POST /wp/agents/run       Multi-agent task execution
GET  /wp/agents/status    All agents status
POST /wp/agents/route     Route task to correct agent

POST /knowledge/upload    Upload file to knowledge base
POST /wp/knowledge/search Search knowledge base
POST /wp/knowledge/learn-url Learn from URL

GET  /llm/configure       Get LLM config
POST /llm/configure       Set LLM provider + key
```

### WordPress Plugin
```
GET  /wp-json/ai-agent/v1/ping
GET  /wp-json/ai-agent/v1/site-info
GET  /wp-json/ai-agent/v1/plugins
POST /wp-json/ai-agent/v1/update-plugins
POST /wp-json/ai-agent/v1/toggle-plugin
GET  /wp-json/ai-agent/v1/users
POST /wp-json/ai-agent/v1/manage-users
POST /wp-json/ai-agent/v1/elementor-data
GET  /wp-json/ai-agent/v1/elementor-data
GET  /wp-json/ai-agent/v1/learndash-courses
POST /wp-json/ai-agent/v1/learndash-courses
POST /wp-json/ai-agent/v1/run-cli
GET  /wp-json/ai-agent/v1/error-log
POST /wp-json/ai-agent/v1/heartbeat
POST /wp-json/ai-agent/v1/register-site
```

---

## 🤖 LLM Configuration

```bash
# Claude (Anthropic)
POST /llm/configure
{"provider":"claude","api_key":"sk-ant-...","model":"claude-sonnet-4-5"}

# OpenAI
POST /llm/configure
{"provider":"openai","api_key":"sk-...","model":"gpt-4o-mini"}

# Ollama (Local - Free)
POST /llm/configure
{"provider":"ollama","model":"llama3","base_url":"http://localhost:11434"}

# Mock (Testing - no key needed)
POST /llm/configure
{"provider":"mock"}
```

---

## 🔧 WordPress Plugin Setup

1. Copy `wordpress-plugin/ai-wordpress-agent/` to `/wp-content/plugins/`
2. Activate plugin in WordPress Admin
3. Go to **AI Agent → Settings**
4. Set **Agent URL**: `http://YOUR_SERVER:5001`
5. Copy **API Key** from plugin settings
6. Plugin auto-registers with Agent on save

---

## 🧩 Chrome Extension Setup

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select `C:\mcp-agent\chrome-extension\`
5. Click extension icon → Configure Agent URL

---

## 📚 Knowledge Base

```python
# Learn from file
POST /knowledge/upload
# (multipart form: file + tags)

# Learn from URL
POST /wp/knowledge/learn-url
{"url": "https://docs.learndash.com/..."}

# Learn from WordPress Plugin
POST /wp/knowledge/learn-plugin
{"path": "C:/wamp/www/wp-content/plugins/my-plugin"}

# Search
POST /wp/knowledge/search
{"query": "how to create LearnDash course"}
```

---

## 🎯 Examples

```bash
# Run task via AI
POST /run
{"task": "create learndash course called Python Basics", "site": "my-site"}

# Multi-site plugin update
POST /run
{"task": "update all plugins", "all_sites": true}

# Design with Elementor
POST /wp/agents/run
{"task": "design hero section with blue background", "site": "my-site"}

# Self-heal
POST /wp/auto-heal
{"site": "my-site"}

# System status
GET /system/status
```

---

## 📊 System Requirements

- Python 3.11+
- Flask + Flask-SocketIO
- Playwright (for browser control)
- WordPress 5.8+ (for Plugin)
- Chrome (for Extension)

---

*Built with EN MOSTAFA AI AGENT — AI WordPress Control Center v2.0*
