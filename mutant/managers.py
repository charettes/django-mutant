
from django.db.models import Manager
from django.db.models.query import QuerySet

from .common import choices_from_dict

class FilteredQuerysetManager(Manager):
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        super(FilteredQuerysetManager, self).__init__()
        
    def get_query_set(self):
        qs = super(FilteredQuerysetManager, self).get_query_set()
        return qs.filter(*self.args, **self.kwargs)

class InheritedModelManager(Manager):
    use_for_related_fields = True
    
    class InheritanceQuerySet(QuerySet):
        """
        Based on http://goo.gl/8CM5X by Jeff Elmores
        """
        
        def select_subclasses(self, *subclasses):
            if not subclasses:
                subclasses = self.model.subclasses()
            qs = self.select_related(*subclasses)
            qs.subclasses = subclasses
            return qs
        
        def _clone(self, klass=None, setup=False, **kwargs):
            try:
                kwargs.update({'subclasses': self.subclasses})
            except AttributeError:
                pass
            cls = InheritedModelManager.InheritanceQuerySet
            return super(cls, self)._clone(klass, setup, **kwargs)
        
        def iterator(self):
            iterator = super(InheritedModelManager.InheritanceQuerySet, self).iterator()
            if getattr(self, 'subclasses', False):
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

class ChoiceDefinitionManager(Manager):
    use_for_related_fields = True
    
    class ChoiceDefinitionQuerySet(QuerySet):
        
        def as_choices(self):
            qs = self.values('group', 'value', 'label')
            return choices_from_dict(qs)
    
    def as_choices(self):
        qs = self.ChoiceDefinitionQuerySet(self.model, using=self._db)
        return qs.as_choices()
