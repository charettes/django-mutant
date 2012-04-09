import warnings

from django.core.exceptions import ValidationError
from django.utils.unittest.case import TestCase

from mutant.contrib.numeric.models import IntegerFieldDefinition
from mutant.contrib.text.models import CharFieldDefinition
from mutant.models.field import (FieldDefinition, FieldDefinitionChoice,
    NOT_PROVIDED)
from mutant.tests.models.utils import BaseModelDefinitionTestCase


class FieldDefinitionInheritanceTest(BaseModelDefinitionTestCase):
    
    def test_proxy_inheritance(self):
        obj = CharFieldDefinition.objects.create(name='caca',
                                                  max_length=25,
                                                  model_def=self.model_def)
        save_obj = self.model_def.fielddefinitions.select_subclasses().get()
        self.assertEqual(obj, save_obj)
        
        Model = self.model_def.model_class()
        Model.objects.create(caca="NO WAY")

class FieldDefinitionDeclarationTest(TestCase):
    
    def test_delete_override(self):
        """
        Make sure a warning is raised when declaring a `FieldDefinition`
        subclass that override the `delete` method.
        """
        with self.assertRaises(TypeError):
            with warnings.catch_warnings(record=True) as w:
                class CustomFieldDefinition(FieldDefinition):
                    def delete(self, *args, **kwargs):
                        pass
                    
                class CustomFieldDefinitionProxy(CustomFieldDefinition):
                    class Meta:
                        proxy = True
                    def delete(self, *args, **kwargs):
                        pass

        self.assertIn('Avoid overriding the `delete` method on '
                      '`FieldDefinition` subclass `CustomFieldDefinition`',
                      w[0].message.message)

def module_level_pickable_default():
    module_level_pickable_default.incr += 1
    return module_level_pickable_default.incr
module_level_pickable_default.incr = 0

class FieldDefaultTest(BaseModelDefinitionTestCase):
    
    def test_clean(self):
        field = IntegerFieldDefinition(name='field', model_def=self.model_def)
        
        # Field cleaning should work when a default value isn't provided
        field.clean()
        
        with self.assertRaises(ValidationError):
            field.default = 'invalid'
            field.clean()
        
        field.default = module_level_pickable_default
        field.clean()
        field.save()
        
        Model = self.model_def.model_class()
        self.assertEqual(Model.objects.create().field,
                         module_level_pickable_default.incr)
        
        field.default = NOT_PROVIDED
        field.save()
        
        with self.assertRaises(ValidationError):
            obj = Model()
            obj.field
            obj.full_clean()
            
    def test_default_value_set(self):
        Model = self.model_def.model_class()
        
        Model.objects.create()
        IntegerFieldDefinition.objects.create(name='field',
                                              default=module_level_pickable_default,
                                              model_def=self.model_def)
        
        # Call after field creation so we can identify if the default value
        # was set when creating the field or when fetching the instance.
        incr = module_level_pickable_default.incr
        module_level_pickable_default()
        
        before = Model.objects.get()
        self.assertEqual(before.field, incr)
        
        after = Model.objects.create()
        self.assertEqual(after.field, incr + 2)
        
    def test_create_with_default(self):
        Model = self.model_def.model_class()
        
        Model.objects.create()
        IntegerFieldDefinition.objects.create_with_default(1337, name='field',
                                                           model_def=self.model_def)
        
        before = Model.objects.get()
        self.assertEqual(before.field, 1337)
        self.assertFalse(Model().field)
            
class FieldDefinitionChoiceTest(BaseModelDefinitionTestCase):
    
    def test_simple_choices(self):
        field_def = CharFieldDefinition.objects.create(name='gender',
                                                       max_length=1,
                                                       model_def=self.model_def)
        choice = FieldDefinitionChoice(field_def=field_def,
                                       value='Male', label='Male')
        
        self.assertRaises(ValidationError, choice.clean)
        
        choice.value = 'M'
        choice.full_clean()
        choice.save()
        
        Model = self.model_def.model_class()
        obj = Model(gender='Male')
        
        self.assertRaises(ValidationError, obj.full_clean)
        
        FieldDefinitionChoice.objects.create(field_def=field_def,
                                             value='F', label='Female')
        
        obj = Model(gender='F')
        obj.full_clean()

        choices = Model._meta.get_field('gender').get_choices(include_blank=False)
        self.assertEqual(choices, [(u'M', u'Male'), (u'F', u'Female')])
        
    def test_grouped_choices(self):
        field_def = CharFieldDefinition.objects.create(name='media',
                                                       max_length=5,
                                                       model_def=self.model_def)
        
        FieldDefinitionChoice.objects.create(field_def=field_def, group='Audio',
                                             value='vinyl', label='Vinyl')
        FieldDefinitionChoice.objects.create(field_def=field_def, group='Audio',
                                             value='cd', label='CD')
        
        FieldDefinitionChoice.objects.create(field_def=field_def, group='Video',
                                             value='vhs', label='VHS Tape')
        FieldDefinitionChoice.objects.create(field_def=field_def, group='Video',
                                             value='dvd', label='DVD')
        
        FieldDefinitionChoice.objects.create(field_def=field_def,
                                             value='unknown', label='Unknown')
        
        Model = self.model_def.model_class()
        choices = Model._meta.get_field('media').get_choices(include_blank=False)
        expected_choices = [
            ('Audio', (
                    ('vinyl', 'Vinyl'),
                    ('cd', 'CD'),
                )
             ),
            ('Video', (
                    ('vhs', 'VHS Tape'),
                    ('dvd', 'DVD'),
                )
             ),
            ('unknown', 'Unknown')
        ]
        self.assertEqual(choices, expected_choices)
    