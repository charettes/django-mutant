from __future__ import unicode_literals

import re

from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

python_identifier_re = re.compile(r'^[a-z_][\w_]*$', re.IGNORECASE)
validate_python_identifier = RegexValidator(python_identifier_re,
                                            _('Enter a valid python identifier.'),
                                            'invalid')

python_object_path_re = re.compile(r'^[a-z_]+(\.[\w_]+)*$', re.IGNORECASE)
validate_python_object_path = RegexValidator(python_object_path_re,
                                             _('Enter a valid python object path.'),
                                             'invalid')
