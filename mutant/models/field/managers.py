from __future__ import unicode_literals

import warnings

import django
from django.db import models
from polymodels.managers import PolymorphicManager, PolymorphicQuerySet

from ...utils import choices_from_dict


class FieldDefinitionQuerySet(PolymorphicQuerySet):
    def create_with_default(self, default, **kwargs):
        obj = self.model(**kwargs)
        obj._state._creation_default_value = default
        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj


class FieldDefinitionManager(PolymorphicManager):
    def get_queryset(self):
        return FieldDefinitionQuerySet(self.model, using=self._db)

    if django.VERSION < (1, 8):
        def get_query_set(self):
            warnings.warn(
                "`FieldDefinitionManager.get_query_set` is deprecated, "
                "use `get_queryset` instead.",
                DeprecationWarning if django.VERSION >= (1, 7)
                else PendingDeprecationWarning,
                stacklevel=2
            )
            return FieldDefinitionManager.get_queryset(self)

    def get_by_natural_key(self, app_label, model, name):
        qs = self.select_subclasses()
        return qs.get(model_def__app_label=app_label,
                      model_def__model=model, name=name)

    def names(self):
        qs = self.get_queryset()
        return qs.order_by('name').values_list('name', flat=True)

    def create_with_default(self, default, **kwargs):
        qs = self.get_queryset()
        return qs.create_with_default(default, **kwargs)


class FieldDefinitionChoiceQuerySet(models.query.QuerySet):
    def construct(self):
        # Here we don't use .values() since it's raw output from the database
        # and values are not prepared correctly.
        choices = (
            {'group': choice.group, 'label': choice.label, 'value': choice.value}
            for choice in self.only('group', 'value', 'label')
        )
        return tuple(choices_from_dict(choices))


class FieldDefinitionChoiceManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return FieldDefinitionChoiceQuerySet(self.model, using=self._db)

    if django.VERSION < (1, 8):
        def get_query_set(self):
            warnings.warn(
                "`FieldDefinitionChoiceManager.get_query_set` is"
                "deprecated, use `get_queryset` instead.",
                DeprecationWarning if django.VERSION >= (1, 7)
                else PendingDeprecationWarning,
                stacklevel=2
            )
            return FieldDefinitionChoiceManager.get_queryset(self)

    def construct(self):
        return self.get_queryset().construct()
