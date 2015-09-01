from __future__ import unicode_literals

from unittest import TestCase

from django.apps.registry import Apps
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

from mutant.db.fields.related import ModelClassAttributeDescriptor
from mutant.db.fields.translation import LazilyTranslatedField

from .models import ModelWithModelDefinitionReference
from .utils import BaseModelDefinitionTestCase


class LazilyTranslatedFieldTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.field = LazilyTranslatedField()
        return super(LazilyTranslatedFieldTest, cls).setUpClass()

    def test_to_python(self):
        self.assertIsNone(self.field.to_python(None))
        self.assertEqual(self.field.to_python(_('hello')), _('hello'))
        self.assertEqual(self.field.to_python('hello'), _('hello'))
        self.assertEqual(self.field.to_python('hello'), _('hello'))
        self.assertEqual(self.field.to_python(1), _('1'))

    def test_get_prep_value(self):
        self.assertIsNone(self.field.get_prep_value(None))
        self.assertEqual(self.field.get_prep_value(_('hello')), 'hello')
        self.assertEqual(self.field.get_prep_value('hello'), 'hello')
        self.assertEqual(self.field.get_prep_value('hello'), 'hello')
        self.assertEqual(self.field.get_prep_value(1), '1')


class ModelDefinitionReferenceTest(BaseModelDefinitionTestCase):
    def test_manager_name_clash(self):
        test_apps = Apps()
        options = type(str('Meta'), (), {'apps': test_apps, 'app_label': 'mutant'})
        # Inexistent field
        with self.assertRaises(ImproperlyConfigured):
            class InexistentModelDefField(models.Model):
                objs = ModelClassAttributeDescriptor('model_def', 'objects')
                Meta = options
        # Non-FK field
        with self.assertRaises(ImproperlyConfigured):
            class NonFKModelDefField(models.Model):
                name = models.CharField(max_length=100)
                objs = ModelClassAttributeDescriptor('name', 'objects')
                Meta = options
        # FK not pointing to ModelDefinition
        with self.assertRaises(ImproperlyConfigured):
            class NonModelDefFKField(models.Model):
                model_def = models.ForeignKey('self', on_delete=models.CASCADE)
                objs = ModelClassAttributeDescriptor('model_def', 'objects')
                Meta = options
        # Lazy FK not pointing to ModelDefinition
        with self.assertRaises(ImproperlyConfigured):
            class LazyNonModelDefFKField(models.Model):
                model_def = models.ForeignKey('mutant.fielddefinition', on_delete=models.CASCADE)
                objs = ModelClassAttributeDescriptor('model_def', 'objects')
                Meta = options

    def test_manager_descriptor(self):
        obj = ModelWithModelDefinitionReference()
        # Not nullable field definition should raise
        with self.assertRaises(AttributeError):
            obj.model_objects
        # Nullable field definition should raise
        with self.assertRaises(AttributeError):
            obj.nullable_objects
        # Assigning an existing model def should allow manager retrieval
        obj.model_def = self.model_def
        self.assertIsInstance(obj.model_objects, models.Manager)
        # Assigning an existing model def should allow manager retrieval
        obj.nullable_model_def = self.model_def
        self.assertIsInstance(obj.nullable_objects, models.Manager)
        # Making sure we've got the right model
        Model = self.model_def.model_class()
        Model.objects.create()
        self.assertEqual(obj.model_objects.count(), 1)
        self.assertEqual(obj.nullable_objects.count(), 1)
