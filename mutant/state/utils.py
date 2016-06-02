from __future__ import unicode_literals

from django.apps import apps


class HandlerProxy(object):
    def __getattribute__(self, name):
        if not apps.apps_ready:
            raise AttributeError
        handler = apps.get_app_config('mutant').state_handler
        return getattr(handler, name)
