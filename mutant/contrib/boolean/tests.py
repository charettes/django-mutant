from __future__ import unicode_literals

try:
    from unittest.case import skipIf
except ImportError:  # TODO: Remove when support for Python 2.6 is dropped
    from django.utils.unittest.case import skipIf

from django.db import connection
from django.utils.translation import ugettext_lazy as _
import south

from mutant.test.testcases import FieldDefinitionTestMixin
from mutant.tests.utils import BaseModelDefinitionTestCase

from .models import BooleanFieldDefinition, NullBooleanFieldDefinition


class BooleanFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Boolean')

    @skipIf(
        connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3' and
        south.__version__ == '0.8.1',
        "South 0.8.1 doesn't escape added column default value correctly on SQLite3."
    )
    def test_create_with_default(self):
        super(BooleanFieldDefinitionTestMixin, self).test_create_with_default()


class BooleanFieldDefinitionTest(BooleanFieldDefinitionTestMixin,
                                 BaseModelDefinitionTestCase):
    field_definition_cls = BooleanFieldDefinition
    field_definition_init_kwargs = {'default': True}
    field_values = (True, False)


class NullBooleanFieldDefinitionTest(BooleanFieldDefinitionTestMixin,
                                     BaseModelDefinitionTestCase):
    field_definition_cls = NullBooleanFieldDefinition
    field_values = (True, None)
