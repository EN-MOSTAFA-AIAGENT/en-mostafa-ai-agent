# 🔗 دليل ربط WordPress Plugin بالـ Agent

## المبدأ العام

```
WordPress ←→ API Key ←→ Agent Server
   (Plugin)              (server.py :5001)
```

الـ **API Key** هو الجسر الوحيد بين الطرفين.
- Plugin يحتفظ بالـ Key ويرسله في كل request
- Agent يتحقق منه قبل أي عملية

---

## الخطوات العملية

### 1. تشغيل الـ Agent أولاً
```
launcher.bat (على جهازك)
↓
Server يبدأ على http://YOUR-IP:5001
```

### 2. تثبيت الـ Plugin
```
نسخ المجلد:
C:\mcp-agent\wordpress-plugin\ai-wordpress-agent\
↓
لصقه في:
wp-content/plugins/ai-wordpress-agent/
↓
تفعيل من: WP Admin → Plugins
```

### 3. الإعداد الوحيد المطلوب
```
WP Admin → AI Agent → Settings

Agent URL = http://YOUR-IP:5001
             ↑
             IP جهازك (مش localhost لو WordPress على server خارجي)
             لو على نفس الجهاز: http://127.0.0.1:5001

اضغط Save → Plugin يسجّل نفسه تلقائياً
```

### 4. التحقق من الاتصال
```
WP Admin → Dashboard → Widget "AI Agent Status"

🟢 Connected = تمام
🔴 Disconnected = راجع Agent URL
```

---

## كيف يعمل كل شيء تلقائياً

### عند الحفظ (مرة واحدة):
```
Plugin
  └→ POST http://YOUR-IP:5001/wp/register-site
     {site_name, site_url, api_key}
     
Agent
  └→ يحفظ الموقع في DB
  └→ يبدأ Heartbeat monitoring
  └→ Dashboard يظهر الموقع
```

### كل 60 ثانية (تلقائي):
```
Plugin
  └→ POST http://YOUR-IP:5001/wp/heartbeat
     {wp_version, plugins_list, errors}
     
Agent
  └→ يُحدث حالة الاتصال
  └→ يُحلل الأخطاء
  └→ يُطلق Self-Heal لو في Fatal errors
```

### عند تنفيذ أي أمر من Dashboard:
```
Dashboard (browser)
  └→ POST http://YOUR-IP:5001/wp/update-plugins
     {site: "my-blog"}
     
Agent (Python)
  └→ يجيب API Key المحفوظ
  └→ POST https://myblog.com/wp-json/ai-agent/v1/update-plugins
     Header: X-AI-Agent-Key: abc123...
     
WordPress Plugin (PHP)
  └→ يتحقق من Key
  └→ ينفذ wp_update_plugins()
  └→ يرجع النتيجة
```

---

## جدول كل الـ Endpoints

### من Agent → WordPress (Agent يتحكم في WP):
```
GET  /wp-json/ai-agent/v1/ping               تحقق اتصال
GET  /wp-json/ai-agent/v1/site-info          معلومات الموقع
GET  /wp-json/ai-agent/v1/plugins            قائمة الإضافات
POST /wp-json/ai-agent/v1/update-plugins     تحديث الإضافات
POST /wp-json/ai-agent/v1/toggle-plugin      تفعيل/تعطيل إضافة
GET  /wp-json/ai-agent/v1/users              قائمة المستخدمين
POST /wp-json/ai-agent/v1/manage-users       إدارة المستخدمين
GET  /wp-json/ai-agent/v1/elementor-data     بيانات Elementor
POST /wp-json/ai-agent/v1/elementor-data     تعديل Elementor
GET  /wp-json/ai-agent/v1/learndash-courses  قائمة الكورسات
POST /wp-json/ai-agent/v1/learndash-courses  إنشاء كورس
POST /wp-json/ai-agent/v1/run-cli            WP-CLI commands
GET  /wp-json/ai-agent/v1/error-log          قراءة debug.log
POST /wp-json/ai-agent/v1/import-xml         استيراد XML
```

### من WordPress → Agent (WP يُبلّغ Agent):
```
POST http://AGENT:5001/wp/register-site      تسجيل الموقع
POST http://AGENT:5001/wp/heartbeat          نبضة حياة كل دقيقة
POST http://AGENT:5001/wp/error-report       تقرير إصلاح ذاتي
```

---

## حالات شائعة وحلولها

### ❌ Plugin مش بيتصل
```
السبب: Agent URL غلط
الحل:
  1. تأكد server.py شغال: py -3.11 server.py
  2. افتح http://YOUR-IP:5001/healthz في browser
  3. لو شغال ← عدّل Agent URL في Plugin Settings
  4. لو على server خارجي: افتح Port 5001 في Firewall
```

### ❌ 401 Unauthorized
```
السبب: API Key غلط
الحل:
  1. WP Admin → AI Agent → Settings
  2. انسخ API Key من هناك
  3. لما تسجّل الموقع من Dashboard
     الصق نفس الـ Key
```

### ❌ Heartbeat مش بيوصل
```
السبب: WordPress مش قادر يوصل جهازك
الحل: استخدم Cloudflare Tunnel
  cloudflared tunnel run mcp-agent
  
  ثم Agent URL = https://api.devmostafa.com
```

### ❌ WP على localhost وAgent على localhost
```
الإعداد: Agent URL = http://127.0.0.1:5001
يشتغل بدون مشاكل
```

---

## ملخص - ملف التحكم الرئيسي

```
ملف واحد يتحكم في كل شيء:
wp-dashboard → http://localhost:5001/wp-dashboard

من هنا تقدر:
  ✅ تضيف مواقع جديدة
  ✅ تشوف حالة كل موقع (Connected/Disconnected)
  ✅ تشغّل أي مهمة على أي موقع
  ✅ تحدّث الإضافات
  ✅ تنشئ كورسات LearnDash
  ✅ تعدّل Elementor
  ✅ تقرأ Error Log
  ✅ Self-Heal تلقائي
```
