from __future__ import unicode_literals

from django.utils.module_loading import import_by_path

from ..settings import STATE_HANDLER


class StateHandlerProxy(object):
    __slots__ = ['path']

    def __init__(self, path):
        self.path = path

    def __getattribute__(self, name):
        path = super(StateHandlerProxy, self).__getattribute__('path')
        handler = import_by_path(path, 'MUTANT_STATE_HANDLER ')()
        return getattr(handler, name)


handler = StateHandlerProxy(STATE_HANDLER)
