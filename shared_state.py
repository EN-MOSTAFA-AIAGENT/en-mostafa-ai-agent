"""
Shared State between REST and MCP
يتشاركوا نفس الـ objects في memory
"""

from job_manager import job_manager, JobState

# Browser state مشترك
browser_state = {
    "job_id": None,
    "current_url": "",
    "waiting_for_user": False,
    "message": "",
    "visible": False
}
browser_lock = None  # يتعرف في server.py

def init_browser_lock():
    global browser_lock
    import threading
    browser_lock = threading.RLock()
    return browser_lock
