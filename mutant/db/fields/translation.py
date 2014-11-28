from __future__ import unicode_literals

from django.db.models.fields import TextField
from django.utils.encoding import smart_text
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy as _


def _is_gettext_promise(value):
    return isinstance(value, Promise) and (value._delegate_bytes or value._delegate_text)


class LazilyTranslatedField(TextField):
    def to_python(self, value):
        if value is None or _is_gettext_promise(value):
            return value
        return _(smart_text(value))

    def get_prep_value(self, value):
        if value is None:
            return value
        elif _is_gettext_promise(value):
            value = smart_text(value._proxy____args[0])
        return smart_text(value)
