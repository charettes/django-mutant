
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

class InheritedModelManager(models.Manager):
    use_for_related_fields = True
    
    class InheritanceQuerySet(models.query.QuerySet):
        """
        Based on http://goo.gl/8CM5X by Jeff Elmores
        """
        
        def select_subclasses(self, *subclasses):
            self.type_cast = True
            lookups = self.model.subclasses_lookups(subclasses)
            return self.select_related('content_type', *lookups)
        
        def _clone(self, klass=None, setup=False, **kwargs):
            kwargs.update(type_cast=getattr(self, 'type_cast', False))
            cls = InheritedModelManager.InheritanceQuerySet
            return super(cls, self)._clone(klass, setup, **kwargs)
        
        def iterator(self):
            iterator = super(InheritedModelManager.InheritanceQuerySet, self).iterator()
            if getattr(self, 'type_cast', False):
                for obj in iterator:
                    yield obj.type_cast()
            else:
                # yield from iterator
                for obj in iterator:
                    yield obj
    
    def select_subclasses(self, *subclasses):
        return self.get_query_set().select_subclasses(*subclasses)
    
    def get_query_set(self):
        return self.InheritanceQuerySet(self.model, using=self._db)

class FieldDefinitionChoiceManager(models.Manager):
    use_for_related_fields = True
    
    class ChoiceDefinitionQuerySet(models.query.QuerySet):
        
        def as_choices(self):
            choices = ({'group': choice.group,
                        'label': choice.label,
                        'value': choice.value}
                       for choice in self.only('group', 'value', 'label'))
            return choices_from_dict(choices)

    def as_choices(self):
        return self.get_query_set().as_choices()

    def get_query_set(self):
        return self.ChoiceDefinitionQuerySet(self.model, using=self._db)