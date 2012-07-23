from __future__ import unicode_literals

from django.db.models.fields import TextField
from django.utils.encoding import smart_unicode
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy as _


def _is_ugettext_promise(obj):
    return isinstance(obj, Promise) and (obj._delegate_unicode or
                                         obj._delegate_str)

class LazilyTranslatedField(TextField):
    def to_python(self, value):
        if value is None or _is_ugettext_promise(value):
            return value
        return _(smart_unicode(value))

    def get_prep_value(self, value):
        if value is None:
            return value
        elif _is_ugettext_promise(value):
            value = smart_unicode(value._proxy____args[0])
        return smart_unicode(value)
