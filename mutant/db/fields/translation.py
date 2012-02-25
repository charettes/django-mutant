
from django.db.models.fields import TextField
from django.utils.encoding import smart_unicode
from django.utils.functional import Promise
from django.utils.translation import ugettext, ugettext_lazy as _


class LazilyTranslatedField(TextField):
    
    def to_python(self, value):
        if (isinstance(value, Promise) and
            value._proxy____func == ugettext) or value is None:
            return value
        return _(smart_unicode(value))
    
    def get_prep_value(self, value):
        if value is None:
            return value
        elif isinstance(value, basestring):
            return smart_unicode(value)
        # We assume it's a ugettext promise
        return smart_unicode(value._proxy____args[0])
