from __future__ import unicode_literals

from django.utils.module_loading import import_by_path

from ..settings import STATE_HANDLER

from .utils import HandlerProxy


handler = HandlerProxy(STATE_HANDLER)
