#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys






# 🌟 EMERGENCY MONKEY-PATCH FOR DJANGO 6.1 + UNFOLD COMPATIBILITY
try:
    from django.contrib.admin.templatetags import admin_list
    from django.template.library import InclusionNode
    
    # Force the base InclusionNode initializer to accept 'token' safely if passed by Django 6.1
    original_node_init = InclusionNode.__init__
    
    def tolerant_node_init(self, parser, token, *args, **kwargs):
        try:
            return original_node_init(self, parser, token, *args, **kwargs)
        except TypeError:
            return original_node_init(self, parser, *args, **kwargs)
            
    InclusionNode.__init__ = tolerant_node_init
    print("🚀 Natively patched InclusionNode for Django 6.1 template parser alignment.")
except Exception as e:
    pass



def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
