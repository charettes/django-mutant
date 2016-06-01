from __future__ import unicode_literals

from django.db import models
from polymodels.fields import PolymorphicTypeField

from ... import forms


class FieldDefinitionTypeField(PolymorphicTypeField):
    def __init__(self, on_delete=models.CASCADE, *args, **kwargs):
        super(FieldDefinitionTypeField, self).__init__(
            'mutant.FieldDefinition', on_delete=on_delete, *args, **kwargs
        )

    def deconstruct(self):
        name, path, args, kwargs = super(FieldDefinitionTypeField, self).deconstruct()
        kwargs.pop('polymorphic_type')
        if kwargs.get('on_delete') == models.CASCADE:
            kwargs.pop('on_delete')
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FieldDefinitionTypeField}
        defaults.update(kwargs)
        return super(FieldDefinitionTypeField, self).formfield(**kwargs)
