"""warmup.py — called by launcher.bat during startup"""
import sys, os
sys.path.insert(0, r'C:\mcp-agent')
os.chdir(r'C:\mcp-agent')
try:
    from sites_store      import sites_store, restore_sites_to_manager
    from wp_manager       import wp_manager
    from health_monitor   import health_monitor
    from knowledge_manager import knowledge_manager
    n  = restore_sites_to_manager(wp_manager)
    kn = knowledge_manager.get_stats().get('total', 0)
    print('  Sites restored  :', n)
    print('  Knowledge docs  :', kn)
    print('  Health Monitor  : ready')
except Exception as e:
    print('  [WARN] Warm-up :', str(e)[:70])
