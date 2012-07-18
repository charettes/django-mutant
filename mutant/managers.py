
from django.db import models
from polymodels.managers import PolymorphicManager, PolymorphicQuerySet

from .utils import choices_from_dict


class FilteredQuerysetManager(models.Manager):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(FilteredQuerysetManager, self).__init__()

    def get_query_set(self):
        qs = super(FilteredQuerysetManager, self).get_query_set()
        return qs.filter(*self.args, **self.kwargs)


class ModelDefinitionManager(models.Manager):

    def create(self, bases=(), fields=(), **kwargs):
        obj = self.model(**kwargs)
        extra_fields = []
        delayed_save = []

        for base in bases:
            extra_fields.extend([(f.get_attname_column()[1], f)
                                 for f in base.get_declared_fields()])
            base._state._add_columns = False
            delayed_save.append(base)

        for field in fields:
            field_instance = field._south_ready_field_instance()
            extra_fields.append((field_instance.get_attname_column()[1], field_instance))
            field._state._add_column = False
            delayed_save.append(field)

        obj._state._create_extra_fields = extra_fields
        obj._state._create_delayed_save = delayed_save

        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj


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
