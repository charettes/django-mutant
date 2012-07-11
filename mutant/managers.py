
from django.db import models

from .common import choices_from_dict


class FilteredQuerysetManager(models.Manager):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(FilteredQuerysetManager, self).__init__()

    def get_query_set(self):
        qs = super(FilteredQuerysetManager, self).get_query_set()
        return qs.filter(*self.args, **self.kwargs)


class ChoiceDefinitionQuerySet(models.query.QuerySet):

    def as_choices(self):
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
        return ChoiceDefinitionQuerySet(self.model, using=self._db)
