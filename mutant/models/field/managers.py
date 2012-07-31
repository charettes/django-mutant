from __future__ import unicode_literals

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
    def get_query_set(self):
        return FieldDefinitionQuerySet(self.model, using=self._db)

    def get_by_natural_key(self, app_label, model, name):
        qs = self.select_subclasses()
        return qs.get(model_def__app_label=app_label,
                      model_def__model=model, name=name)

    def names(self):
        qs = self.get_query_set()
        return qs.order_by('name').values_list('name', flat=True)

    def create_with_default(self, default, **kwargs):
        qs = self.get_query_set()
        return qs.create_with_default(default, **kwargs)


class FieldDefinitionChoiceQuerySet(models.query.QuerySet):
    def as_choices(self):
        # Here we don't use .values() since it's raw output from the database
        # and values are not prepared correctly.
        choices = ({'group': choice.group,
                    'label': choice.label,
                    'value': choice.value}
                   for choice in self.only('group', 'value', 'label'))
        return choices_from_dict(choices)


class FieldDefinitionChoiceManager(models.Manager):
    use_for_related_fields = True

    def as_choices(self):
        return self.get_query_set().as_choices()

    def get_query_set(self):
        return FieldDefinitionChoiceQuerySet(self.model, using=self._db)
