import os
import sys
from django.core.wsgi import get_wsgi_application

# =====================================================================
# 🌟 EMERGENCY MONKEY-PATCH FOR DJANGO 6.1 + UNFOLD THEME ALIGNMENT
# =====================================================================
try:
    from django.template.library import InclusionNode
    original_node_init = InclusionNode.__init__
    
    def tolerant_node_init(self, parser, token, *args, **kwargs):
        try:
            return original_node_init(self, parser, token, *args, **kwargs)
        except TypeError:
            return original_node_init(self, parser, *args, **kwargs)
            
    InclusionNode.__init__ = tolerant_node_init
    print("🚀 Production Gunicorn WSGI thread auto-patched cleanly.")
except Exception as e:
    pass

# =====================================================================
# STANDARD DJANGO ENGINE HOOKS
# =====================================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()


