from __future__ import unicode_literals

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_text
from django.utils.functional import LazyObject

from .utils import choices_from_dict


class LazyFieldDefinitionQueryset(LazyObject):
    def __init__(self, queryset, models):
        super(LazyFieldDefinitionQueryset, self).__init__()
        self.__dict__.update(queryset=queryset, models=models)

    def _setup(self):
        queryset = self.__dict__.get('queryset')
        models = self.__dict__.get('models')
        self._wrapped = queryset.filter(
            pk__in=[ct.pk for ct in ContentType.objects.get_for_models(
                *models, for_concrete_models=False
            ).values()]
        )


class LazyFieldDefinitionGroupedChoices(LazyObject):
    def __init__(self, queryset, empty_label, label_from_instance):
        super(LazyFieldDefinitionGroupedChoices, self).__init__()
        self.__dict__.update(
            queryset=queryset, empty_label=empty_label,
            label_from_instance=label_from_instance
        )

    def _setup(self):
        queryset = self.__dict__.get('queryset')
        label_from_instance = self.__dict__.get('label_from_instance')
        empty_label = self.__dict__.get('empty_label')
        definition_choices = []
        for content_type in queryset:
            definition = content_type.model_class()
            category = definition.get_field_category()
            definition_choices.append({
                'group': smart_text(category) if category else None,
                'value': content_type.pk,
                'label': label_from_instance(content_type),
            })
        choices = list(
            choices_from_dict(
                sorted(definition_choices, key=lambda c: c['group'] or '')
            )
        )
        if empty_label is not None:
            choices.insert(0, ('', self.empty_label))
        self._wrapped = choices


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
            return LazyFieldDefinitionQueryset(queryset, self.field_definitions)
        return queryset

    queryset = property(_get_queryset, forms.ModelChoiceField._set_queryset)

    def _get_choices(self):
        if self.group_by_category:
            return LazyFieldDefinitionGroupedChoices(
                self.queryset, self.empty_label, self.label_from_instance
            )
        return super(FieldDefinitionTypeField, self)._get_choices()

    choices = property(_get_choices, forms.ModelChoiceField._set_queryset)

    def label_from_instance(self, obj):
        return smart_text(obj.model_class().get_field_description())
