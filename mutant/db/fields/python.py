from __future__ import unicode_literals

import os
import re

from django.core.exceptions import ValidationError
from django.db.models.fields import CharField
from django.utils.translation import ugettext_lazy as _

from ...validators import validate_python_identifier


class DirectoryPathField(CharField):
    def validate(self, value, model_instance):
        if not os.path.exists(value):
            raise ValidationError(_("Specified path doesn't exist"))
        elif not os.path.isdir(value):
            raise ValidationError(_("Specified path isn't a directory"))


class RegExpStringField(CharField):
    def to_python(self, value):
        value = super(RegExpStringField, self).to_python(value)
        if value is None:
            return
        try:
            re.compile(value)
        except Exception as e:
            raise ValidationError(_(e))
        else:
            return value


class PythonIdentifierField(CharField):
    default_validators = [validate_python_identifier]
    description = _('Python identifier')

    def __init__(self, *args, **kwargs):
        defaults = {'max_length': 255}
        defaults.update(kwargs)
        super(PythonIdentifierField, self).__init__(*args, **defaults)

    def to_python(self, value):
        value = super(PythonIdentifierField, self).to_python(value)
        if value is not None:
            return str(value)
