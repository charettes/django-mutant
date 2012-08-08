from __future__ import unicode_literals

import django
from django.db.models.fields import TextField
from django.utils.encoding import smart_unicode
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy as _


if django.VERSION[0:2] > (1, 4):
    _delegate_bytes = '_delegate_bytes'
    _delegate_text = '_delegate_text'
else:
    _delegate_bytes = '_delegate_str'
    _delegate_text = '_delegate_unicode'

def _is_gettext_promise(value):
    return isinstance(value, Promise) and (getattr(value, _delegate_bytes) or
                                           getattr(value, _delegate_text))


class LazilyTranslatedField(TextField):
    def to_python(self, value):
        if value is None or _is_gettext_promise(value):
            return value
        return _(smart_unicode(value))

    def get_prep_value(self, value):
        if value is None:
            return value
        elif _is_gettext_promise(value):
            value = smart_unicode(value._proxy____args[0])
        return smart_unicode(value)
