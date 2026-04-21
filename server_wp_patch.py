"""
WordPress Integration Patch for server.py
يُضاف في نهاية server.py أو يُشغّل منفصلاً
يسجّل كل WordPress routes على نفس Flask app
"""

# ── يُنفَّذ هذا في نهاية server.py مباشرة ──
# أضف هذه الأسطر بعد: app = Flask(__name__)

"""
# ══════════════════════════════════════════════
#  WordPress Integration — أضف هذا لـ server.py
# ══════════════════════════════════════════════

from wp_routes import init_wp_routes, wp_bp
from system_awareness import system_awareness
from feedback_loop import feedback_loop

# تسجيل Blueprint
app.register_blueprint(wp_bp)

# Route: /run  (موحّد — يدعم Local + Remote)
@app.route('/run', methods=['POST'])
def run_task():
    from agent_core import AgentCore
    from system_awareness import system_awareness, ExecutionMode
    from feedback_loop import feedback_loop
    import time

    data     = request.get_json(force=True) or {}
    task     = data.get('task', '')
    site     = data.get('site')
    all_sites= data.get('all_sites', False)
    explain  = data.get('explain', False)

    if not task:
        return jsonify({'error': 'task required'}), 400

    agent = AgentCore()
    system_awareness.begin_task(task, tool='agent_core', site=site)

    t0 = time.time()
    try:
        if all_sites:
            result = agent.execute_on_all_sites(task)
        elif site:
            result = agent.execute_wordpress_task(site, task)
        else:
            result = agent.handle_task(task, explain=explain)
    except Exception as e:
        result = {'status': 'error', 'error': str(e)}
    finally:
        dur = time.time() - t0
        system_awareness.end_task(success=result.get('status') == 'completed')
        feedback_loop.record(
            task=task, result=result, tool='agent_core',
            site=site or '', duration=dur,
            memory_engine=agent.memory,
            strategy_engine=agent.strategy
        )

    return jsonify(result)


# Route: /knowledge/upload (multipart)
@app.route('/knowledge/upload', methods=['POST'])
def knowledge_upload():
    from knowledge_manager import knowledge_manager
    import tempfile, os
    f    = request.files.get('file')
    tags = request.form.get('tags', '').split(',')
    if not f:
        return jsonify({'success': False, 'reason': 'no file'}), 400
    # حفظ مؤقت
    ext  = os.path.splitext(f.filename)[1]
    tmp  = tempfile.mktemp(suffix=ext)
    f.save(tmp)
    result = knowledge_manager.learn_from_file(tmp, tags=[t.strip() for t in tags if t.strip()])
    try:
        os.remove(tmp)
    except:
        pass
    return jsonify(result)

"""
