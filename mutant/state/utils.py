from __future__ import unicode_literals

from threading import local

from django.utils.module_loading import import_string


class HandlerProxy(object):
    def __init__(self, path):
        self._handlers = local()
        self.path = path

    def __getattribute__(self, name):
        get = super(HandlerProxy, self).__getattribute__
        try:
            return get(name)
        except AttributeError:
            pass
        handlers = get('_handlers')
        path = get('path')
        try:
            handler = getattr(handlers, path)
        except AttributeError:
            handler = import_string(path)()
            setattr(handlers, path, handler)
        return getattr(handler, name)
