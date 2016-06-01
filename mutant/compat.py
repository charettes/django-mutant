from __future__ import unicode_literals

from operator import attrgetter

import django

get_remote_field = attrgetter('remote_field' if django.VERSION >= (1, 9) else 'rel')

if django.VERSION >= (1, 9):
    def get_remote_field_model(field):
        model = getattr(field, 'model', None)
        if model:
            return field.remote_field.model
        else:
            return field.related_model
else:
    def get_remote_field_model(field):
        return getattr(getattr(field, 'rel', None), 'to', None)
