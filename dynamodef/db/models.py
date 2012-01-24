from contextlib import contextmanager
import threading

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

class MutableModel(models.Model):
    """
    Abstract class used to identify models that we're created by a definition
    """
    class Meta:
        abstract = True
    
    @classmethod 
    def definition(cls):
        definition_cls, definition_pk = cls._definition
        return definition_cls.objects.get(pk=definition_pk)
    
    @classmethod
    def prevent_subscribtions(cls):
        @contextmanager
        def lock():
            current_thread = threading.current_thread()
            with cls._subscribe_lock:
                for subscriber in cls._subscribers:
                    if subscriber is not current_thread:
                        subscriber.join()
                yield
                cls._subscribers.clear()
        return lock
    
    @classmethod
    def subscribe(cls):
        with cls._subscribe_lock:
            cls._subscribers.add(threading.current_thread())
            
    @classmethod
    def is_obsolete(cls):
        return cls._is_obsolete
    
    def clean(self):
        if self.is_obsolete():
            raise ValidationError('Obsolete definition')
    
    def save(self, *args, **kwargs):
        if self.is_obsolete():
            msg = _(u'Cannot save an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.is_obsolete():
            msg = _(u'Cannot delete an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).delete(*args, **kwargs)
