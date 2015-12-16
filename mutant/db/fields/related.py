from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields
from django.db.models.fields import FieldDoesNotExist
from django.db.models.signals import class_prepared
from django.utils import six

from ...compat import get_remote_field_model
from ...models import ModelDefinition


class ModelClassAttributeDescriptor(object):
    """
    Provide an access to an attribute of  a model definition's underlying
    model class. Useful for defining an accessor to a manager.
    """
    def __init__(self, model_def_name, attr_name):
        self.model_def_name = model_def_name
        self.attr_name = attr_name

    def __validate(self, **kwargs):
        opts = self.model._meta
        try:
            field = opts.get_field(self.model_def_name)
        except FieldDoesNotExist:
            raise ImproperlyConfigured("%s.%s.%s refers to an inexistent field "
                                       "'%s'" % (opts.app_label, opts.object_name,
                                                 self.name, self.model_def_name))
        else:
            if (not isinstance(field, fields.related.ForeignKey) or
                    (isinstance(get_remote_field_model(field), six.string_types) and
                        get_remote_field_model(field).lower() != 'mutant.modeldefinition') or
                    not issubclass(get_remote_field_model(field), ModelDefinition)):
                raise ImproperlyConfigured("%s.%s.%s must refer to a ForeignKey "
                                           "to `ModelDefinition`"
                                           % (opts.app_label, opts.object_name,
                                              self.name))
        setattr(self.model, self.name, self)

    def contribute_to_class(self, cls, name):
        self.model = cls
        self.name = name
        class_prepared.connect(self.__validate, cls, weak=True)

    def __get__(self, instance, instance_type=None):
        if instance:
            try:
                model_def = getattr(instance, self.model_def_name)
            except ModelDefinition.DoesNotExist:
                pass
            else:
                if model_def is not None:
                    return getattr(model_def.model_class(), self.attr_name)
            raise AttributeError("Can't access attribute '%s' of the "
                                 "model defined by '%s' since it doesn't exist."
                                 % (self.attr_name, self.model_def_name))
        else:
            return self

    def __set__(self, instance, value):
        raise AttributeError("Can't set attribute")
