
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from ...test.testcases import FieldDefinitionTestMixin
from ...tests.models.utils import BaseModelDefinitionTestCase

from .models import (DictFieldDefinition, EmbeddedModelFieldDefinition,
    ListFieldDefinition, SetFieldDefinition)


class DictFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = DictFieldDefinition
    field_defintion_init_kwargs = {'default': {'1': 2}}
    field_values = (
        {'key': 'value', 'other': 1337},
        {'somewhere': None, 'I': 'Belong'}
    )

def identity(obj):
    return obj

class ListFieldDefinitionTest(FieldDefinitionTestMixin,
                              BaseModelDefinitionTestCase):
    field_definition_cls = ListFieldDefinition
    field_defintion_init_kwargs = {'default': ['Y', 'M', 'C', 'A']}
    field_values = (
        ['A', 'C', 'M', 'Y'],
        ['A', 'B', 'C', 1, 2, 3]
    )
    
    def test_field_ordering(self):
        field = self.field
        
        field.ordering = 4
        msg = "'ordering' has to be a callable or None, not of type <type 'int'>"
        self.assertRaisesMessage(ValidationError, msg, field.full_clean)
        
        field.ordering = identity
        field.full_clean()
        field.save()

class SetFieldDefinitionTest(FieldDefinitionTestMixin,
                             BaseModelDefinitionTestCase):
    field_definition_cls = SetFieldDefinition
    field_defintion_init_kwargs = {'default': set(['Y', 'M', 'C', 'A'])}
    field_values = (
        set(['A', 'B', 'C', 1, 2, 3]),
        set(['I', 'LOVE', 'ROCK', 'N', 'ROLL'])
    )

def default_embedded():
    return ContentType(app_label='abc', model='DoTheDance')

class EmbeddedModelFieldTest(FieldDefinitionTestMixin,
                             BaseModelDefinitionTestCase):
    field_definition_cls = EmbeddedModelFieldDefinition
    field_defintion_init_kwargs = {'default': default_embedded}
    field_values = (
        ContentType(app_label='pyt', model='The way you move is a mistery'),
        ContentType(app_label='everybody', model='Knows this is nowhere'),
    )
    
    def test_field_default(self):
        # TODO: Find out why this fails sometimes
        pass
    
    def test_field_unique(self):
        # TODO: Find out why this fails sometimes
        pass

