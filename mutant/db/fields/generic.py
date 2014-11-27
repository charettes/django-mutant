from __future__ import unicode_literals

from polymodels.fields import PolymorphicTypeField

from ... import forms


class FieldDefinitionTypeField(PolymorphicTypeField):
    def __init__(self, *args, **kwargs):
        super(FieldDefinitionTypeField, self).__init__(
            'mutant.FieldDefinition', *args, **kwargs
        )

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FieldDefinitionTypeField}
        defaults.update(kwargs)
        return super(FieldDefinitionTypeField, self).formfield(**kwargs)
