from __future__ import unicode_literals

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_text

from .utils import choices_from_dict, group_item_getter


class FieldDefinitionTypeField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.field_definitions = kwargs.pop('field_definitions', [])
        self.group_by_category = kwargs.pop('group_by_category', False)
        super(FieldDefinitionTypeField, self).__init__(*args, **kwargs)

    def _get_field_definitions(self):
        return self._field_definitions

    def _set_field_definitions(self, definitions):
        for definition in definitions:
            from mutant.models import FieldDefinition
            if not issubclass(definition, FieldDefinition):
                raise TypeError(
                    "%r is not a subclass of `FieldDefinition`" % definition
                )
        self._field_definitions = definitions

    field_definitions = property(_get_field_definitions, _set_field_definitions)

    def _get_queryset(self):
        queryset = super(FieldDefinitionTypeField, self)._get_queryset()
        if self.field_definitions:
            queryset = queryset.model._base_manager.filter(
                pk__in=[ct.pk for ct in ContentType.objects.get_for_models(
                    *self.field_definitions, for_concrete_models=False
                ).values()]
            )
        return queryset

    queryset = property(_get_queryset, forms.ModelChoiceField._set_queryset)

    def _get_choices(self):
        # `yield from` would be awesome here...
        if self.group_by_category:
            definition_choices = []
            for content_type in self.queryset:
                definition = content_type.model_class()
                category = definition.get_field_category()
                definition_choices.append({
                    'group': smart_text(category) if category else None,
                    'value': content_type.pk,
                    'label': self.label_from_instance(content_type),
                })
            choices = list(
                choices_from_dict(
                    sorted(definition_choices, key=group_item_getter)
                )
            )
            if self.empty_label is not None:
                choices.insert(0, ('', self.empty_label))
            return choices
        return super(FieldDefinitionTypeField, self)._get_choices()

    choices = property(_get_choices, forms.ModelChoiceField._set_queryset)

    def label_from_instance(self, obj):
        return smart_text(obj.model_class().get_field_description())
