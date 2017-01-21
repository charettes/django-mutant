from __future__ import unicode_literals

import django
from django.db import models
from django.utils.translation import ugettext_lazy as _

from mutant.db.fields import FieldDefinitionTypeField
from mutant.db.fields.related import ModelClassAttributeDescriptor
from mutant.models import FieldDefinition, ModelDefinition


class CustomFieldDefinition(FieldDefinition):
    class Meta:
        app_label = 'tests'
        defined_field_category = _('Custom category')
        defined_field_description = _('Custom description')
        if (1, 10) <= django.VERSION < (2, 0):
            manager_inheritance_from_future = True


class FieldDefinitionModel(models.Model):
    field_type = FieldDefinitionTypeField()

    class Meta:
        app_label = 'tests'


class ModelWithModelDefinitionReference(models.Model):
    model_def = models.OneToOneField(ModelDefinition, on_delete=models.CASCADE, related_name='+')
    model_objects = ModelClassAttributeDescriptor('model_def', 'objects')

    nullable_model_def = models.ForeignKey(
        ModelDefinition, on_delete=models.SET_NULL, related_name='+', null=True
    )
    nullable_objects = ModelClassAttributeDescriptor(
        'nullable_model_def', 'objects'
    )

    class Meta:
        app_label = 'tests'


class Mixin(object):
    def method(self):
        return 'Mixin'


class ConcreteModel(models.Model):
    concrete_model_field = models.NullBooleanField()

    class Meta:
        app_label = 'tests'


class ProxyModel(ConcreteModel):
    class Meta:
        app_label = 'tests'
        proxy = True


class AbstractModel(models.Model):
    abstract_model_field = models.CharField(max_length=5)

    class Meta:
        abstract = True

    def method(self):
        return 'AbstractModel'


class AbstractConcreteModelSubclass(ConcreteModel):
    abstract_concrete_model_subclass_field = models.CharField(max_length=5)

    class Meta:
        abstract = True


class ModelSubclassWithTextField(models.Model):
    abstract_model_field = models.TextField()
    second_field = models.NullBooleanField()

    class Meta:
        abstract = True
