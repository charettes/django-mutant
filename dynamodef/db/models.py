
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

class MutableModel(models.Model):
    """
    Abstract class used to identify models that we're created by a definition
    """

    __is_obsolete = False
    
    class Meta:
        abstract = True
        
    @classmethod
    def __mark_as_obsolete(cls):
        cls.__is_obsolete = True
    
    @classmethod 
    def definition(cls):
        definition_cls, definition_pk = cls.__definition
        return definition_cls._default_manager.get(pk=definition_pk)
    
    def clean(self):
        if self.__is_obsolete:
            raise ValidationError('Obsolete definition')
    
    def save(self, *args, **kwargs):
        if self.__is_obsolete:
            msg = _(u'Cannot save an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.__is_obsolete:
            msg = _(u'Cannot delete an obsolete model')
            raise ValidationError(msg)
        return super(MutableModel, self).delete(*args, **kwargs)
