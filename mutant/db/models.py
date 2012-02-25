
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
    def is_obsolete(cls):
        return cls._is_obsolete
    
    def clean(self):
        if self.is_obsolete():
            raise ValidationError('Obsolete definition')
        return super(MutableModel, self).clean()
    
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
