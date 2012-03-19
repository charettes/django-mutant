
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from .models import (DictFieldDefinition, EmbeddedModelFieldDefinition,
    ListFieldDefinition, SetFieldDefinition)
from ...tests.models import BaseModelDefinitionTestCase


def identity(obj):
    return obj

class IterableFieldDefinitionTest(BaseModelDefinitionTestCase):
    
    def test_dict_field(self):
        default = {'1': 2}
        field = DictFieldDefinition.objects.create(model_def=self.model_def,
                                                   name='field',
                                                   default=default)
        field.full_clean()
        
        Model = self.model_def.model_class()
        instance = Model.objects.create()
        self.assertEqual(instance.field, default)
        
        value = {'key': 'value', 'other': 1337}
        instance.field = value
        instance.save()
        
        field.item_field = models.IntegerField()
        # Hopefully this will fail when djangotoolbox validates values
        field.full_clean()
        field.save()
        
        instance = Model.objects.get()
        self.assertEqual(instance.field, value)
        
    def test_list_field(self):
        default = ['Y', 'M', 'C', 'A']
        field = ListFieldDefinition.objects.create(model_def=self.model_def,
                                                   name='field',
                                                   default=default)
        field.full_clean()
        
        Model = self.model_def.model_class()
        instance = Model.objects.create()
        self.assertEqual(instance.field, default)
        
        field.ordering = 4
        self.assertRaisesMessage(ValidationError,
                                 "'ordering' has to be a callable or None, not of type <type 'int'>",
                                 field.full_clean)
        field.ordering = identity
        field.full_clean()
        field.save()
        
        instance = Model.objects.get()
        instance.save()
        self.assertEqual(instance.field, ['A', 'C', 'M', 'Y'])
        
        value = ['A', 'B', 'C', 1, 2, 3]
        instance.field = value
        instance.save()
        
        field.item_field = models.IntegerField()
        # Hopefully this will fail when djangotoolbox validates values
        field.full_clean()
        field.save()
        
        instance = Model.objects.get()
        self.assertEqual(instance.field, value)
        
    def test_set_field(self):
        default = {'Y', 'M', 'C', 'A'}
        field = SetFieldDefinition.objects.create(model_def=self.model_def,
                                                  name='field', default=default)
        field.full_clean()
        
        Model = self.model_def.model_class()
        instance = Model.objects.create()
        self.assertEqual(instance.field, default)
        
        value = {'A', 'B', 'C', 1, 2, 3}
        instance.field = value
        instance.save()
        
        field.item_field = models.IntegerField()
        # Hopefully this will fail when djangotoolbox validates values
        field.full_clean()
        field.save()
        
        instance = Model.objects.get()
        self.assertEqual(instance.field, value)

def default_embedded():
    return ContentType(app_label='abc', model='DoTheDance')

class EmbeddedModelFieldTest(BaseModelDefinitionTestCase):
    
    def test_interactions(self):
        field = EmbeddedModelFieldDefinition.objects.create(model_def=self.model_def,
                                                            name='field',
                                                            default=default_embedded)
        field.full_clean()
        
        
        Model = self.model_def.model_class()
        instance = Model.objects.create()
        self.assertEqual(instance.field, default_embedded())
        
        value = ContentType(app_label='pyt', model='The way you move is a mistery')
        instance.field = value
        instance.save()
        
        instance = Model.objects.get()
        self.assertEqual(instance.field, value)
