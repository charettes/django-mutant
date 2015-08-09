from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from mutant.contrib.boolean.models import (
    BooleanFieldDefinition, NullBooleanFieldDefinition,
)
from mutant.test.testcases import FieldDefinitionTestMixin

from .utils import BaseModelDefinitionTestCase


class BooleanFieldDefinitionTestMixin(FieldDefinitionTestMixin):
    field_definition_category = _('Boolean')

    def test_create_with_default(self):
        super(BooleanFieldDefinitionTestMixin, self).test_create_with_default()


class BooleanFieldDefinitionTest(BooleanFieldDefinitionTestMixin,
                                 BaseModelDefinitionTestCase):
    field_definition_cls = BooleanFieldDefinition
    field_definition_init_kwargs = {'default': True}
    field_values = (False, True)


class NullBooleanFieldDefinitionTest(BooleanFieldDefinitionTestMixin,
                                     BaseModelDefinitionTestCase):
    field_definition_cls = NullBooleanFieldDefinition
    field_values = (True, None)
