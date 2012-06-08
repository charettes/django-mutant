
from django.test.testcases import TestCase

from mutant.models.field import FieldDefinition

from ..forms import FieldDefinitionTypeField


class FieldDefinitionTypeFieldTest(TestCase):
    
    def test_choices_caching(self):
        FieldDefinitionTypeField()
        
        with self.assertNumQueries(0):
            FieldDefinitionTypeField()
        
        class ModelProxy(FieldDefinition):
            class Meta:
                proxy = True
                
        self.assertFalse(hasattr(FieldDefinitionTypeField, '_choices'))
        
    def test_allowed_instance_choices(self):
        field = FieldDefinitionTypeField()
        
        class_choices = field.choices
        
        instance_choices = [(0, 'Worthless'),]
        
        field.choices = instance_choices
        self.assertEqual(field.choices, instance_choices)
        
        self.assertEqual(FieldDefinitionTypeField().choices, class_choices)
