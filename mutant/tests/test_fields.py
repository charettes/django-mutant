from __future__ import unicode_literals

import sys
# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import TestCase
else:
    from django.utils.unittest import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

from mutant.db.fields.related import ModelClassAttributeDescriptor
from mutant.db.fields.translation import LazilyTranslatedField
from mutant.models import ModelDefinition

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


class ModelWithModelDefinitionReference(models.Model):
    model_def = models.OneToOneField(ModelDefinition, related_name='+')
    model_objects = ModelClassAttributeDescriptor('model_def', 'objects')

    nullable_model_def = models.ForeignKey(
        ModelDefinition, related_name='+', null=True
    )
    nullable_objects = ModelClassAttributeDescriptor(
        'nullable_model_def', 'objects'
    )

    class Meta:
        app_label = 'mutant'


class ModelDefinitionReferenceTest(BaseModelDefinitionTestCase):
    def test_manager_name_clash(self):
        # Inexistent field
        with self.assertRaises(ImproperlyConfigured):
            class InexistentModelDefField(models.Model):
                objs = ModelClassAttributeDescriptor('model_def', 'objects')
        # Non-FK field
        with self.assertRaises(ImproperlyConfigured):
            class NonFKModelDefField(models.Model):
                name = models.CharField(max_length=100)
                objs = ModelClassAttributeDescriptor('name', 'objects')
        # FK not pointing to ModelDefinition
        with self.assertRaises(ImproperlyConfigured):
            class NonModelDefFKField(models.Model):
                model_def = models.ForeignKey('self')
                objs = ModelClassAttributeDescriptor('model_def', 'objects')

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
