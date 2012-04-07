
from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models.utils import BaseModelDefinitionTestCase

from .models import BooleanFieldDefinition, NullBooleanFieldDefinition


class CharFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = BooleanFieldDefinition
    field_defintion_init_kwargs = {'default': True}
    field_values = (True, False)

class NullBooleanFieldDefinitionTest(FieldDefinitionTestMixin,
                                     BaseModelDefinitionTestCase):
    field_definition_cls = NullBooleanFieldDefinition
    field_values = (True, None)
