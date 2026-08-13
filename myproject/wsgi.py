import os
import sys
from django.core.wsgi import get_wsgi_application

# =====================================================================
# 🌟 ABSOLUTE DEEP TARGET OVERRIDE: DJANGO 6.1 + UNFOLD THEME ALIGNMENT
# =====================================================================
try:
    # 🧠 Target the exact library node that is crashing inside the Unfold theme package
    import unfold.templatetags.unfold_list as unfold_list
    
    # Capture their explicit list wrapper class
    original_unfold_init = unfold_list.InclusionAdminNode.__init__
    
    def tolerant_unfold_node_init(self, parser, token, *args, **kwargs):
        # Gracefully handle the incoming Django 6.1 template token argument patterns
        try:
            return original_unfold_init(self, parser, token, *args, **kwargs)
        except TypeError:
            # Fallback cleanly if running on older local dependency cached layers
            return original_unfold_init(self, parser, *args, **kwargs)
            
    # Inject our safety guard straight into Unfold's custom engine tracking array
    unfold_list.InclusionAdminNode.__init__ = tolerant_unfold_node_init
    print("======== ✅ CHOSEN UNFOLD TEMPLATE ENGINES RE-ALIGNED SUCCESS ======== ")
except Exception as e:
    print(f"⚠️ Dynamic runtime patch exception bypass note: {e}")

# =====================================================================
# STANDARD DJANGO PROD ENTRY POINT
# =====================================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()
