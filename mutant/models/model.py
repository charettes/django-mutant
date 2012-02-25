from inspect import isclass

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.loading import cache as model_cache
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.translation import ugettext_lazy as _
from orderable.models import OrderableModel

from ..db.fields import (LazilyTranslatedField,
    PickledObjectField, PythonIdentifierField)
from ..db.models import MutableModel


def _get_db_table(app_label, model):
    return "mutant_%s_%s" % (app_label, model)

def _remove_from_model_cache(model_class):
    try:
        opts = model_class._meta
    except AttributeError:
        return
    app_label, model_name = opts.app_label, opts.object_name.lower()
    with model_cache.write_lock:
        app_models = model_cache.app_models.get(app_label, False)
        if app_models:
            model = app_models.pop(model_name, False)
            if model:
                model_cache._get_models_cache.clear()
                model._is_obsolete = True
                return model

class _ModelClassProxy(object):

    def __init__(self, model_class):
        self.__dict__['model_class'] = model_class

    @property
    def __model_class_is_obsolete(self):
        return self.model_class.is_obsolete()

    @staticmethod
    def __get_underlying_model_class(value):
        if isinstance(value, _ModelClassProxy):
            return value.model_class
        elif isclass(value) and issubclass(value, MutableModel):
            return value

    def __get_model_class(self):
        if self.__model_class_is_obsolete:
            return self.__get__(None, None)
        else:
            return self.model_class

    def __get__(self, instance, owner):
        if self.__model_class_is_obsolete:
            try:
                definition = self.model_class.definition()
            except ModelDefinition.DoesNotExist:
                raise AttributeError('This model definition has been deleted')
            else:
                self.__dict__['model_class'] = definition.model_class()
        return self.model_class

    def __set__(self, instance, value):
        model_class = self.__get_underlying_model_class(value)
        if model_class is not None:
            self.model_class = model_class
        else:
            raise AttributeError('Invalid value')

    def __call__(self, *args, **kwargs):
        model_class = self.__get_model_class()
        return model_class(*args, **kwargs)

    def __getattr__(self, name):
        model_class = self.__get_model_class()
        return getattr(model_class, name)

    def __setattr__(self, name, value):
        model_class = self.__get_model_class()
        return setattr(model_class, name, value)

    def __delattr__(self, name):
        model_class = self.__get_model_class()
        return delattr(model_class, name)

    def __instancecheck__(self, instance):
        model_class = self.__get_model_class()
        return isinstance(instance, model_class)

    def __eq__(self, other):
        other_model_class = self.__get_underlying_model_class(other)
        if type(self.model_class) == type(other_model_class):
            return self.model_class == other_model_class
        else:
            return NotImplemented
        
    def __str__(self):
        model_class = self.__get_model_class()
        return str(model_class)

class ModelDefinition(ContentType):
    
    object_name = PythonIdentifierField(_(u'object name'))
    
    verbose_name = LazilyTranslatedField(_(u'verbose name'),
                                         blank=True, null=True)
    
    verbose_name_plural = LazilyTranslatedField(_(u'verbose name plural'),
                                                blank=True, null=True)
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'model definition')
        verbose_name_plural = _(u'model definitions')
    
    def __init__(self, *args, **kwargs):
        super(ModelDefinition, self).__init__(*args, **kwargs)
        if self.pk:
            self._model_class = super(ModelDefinition, self).model_class()
    
    def get_model_bases(self):
        return tuple(bd.base for bd in self.basedefinitions.all())
    
    def get_model_opts(self):
        attrs = {
            'app_label': self.app_label,
            'db_table': _get_db_table(*self.natural_key()),
            'verbose_name': self.verbose_name,
            'verbose_name_plural': self.verbose_name_plural,
        }
        
        unique_together = tuple(tuple(utd.field_defs.names())
                                    for utd in self.uniquetogetherdefinitions.all())
        if unique_together:
            attrs['unique_together'] = unique_together
        
        ordering = tuple(ordf.get_defined_ordering()
                            for ordf in self.orderingfielddefinitions.all())
        if ordering:
            # Make sure not to add ordering if it's empty since it would
            # prevent the model from inheriting it's possible base ordering.
            # Kinda related to django #17429
            attrs['ordering'] = ordering
        
        return type('Meta', (), attrs)
    
    def get_model_attrs(self, existing_model_class=None):
        attrs = {
            'Meta': self.get_model_opts(),
            '__module__': "mutant.apps.%s.models" % self.app_label,
            '_definition': (self.__class__, self.pk),
            '_is_obsolete': False,
        }
        
        attrs.update(dict((f.name, f.field_instance())
                            for f in self.fielddefinitions.select_subclasses()))
        
        return attrs
    
    def _create_model_class(self, existing_model_class=None):
        bases = self.get_model_bases()
        bases += (MutableModel,)
            
        attrs = self.get_model_attrs(existing_model_class)
        
        _remove_from_model_cache(existing_model_class)
        
        model = type(str(self.object_name), bases, attrs)
        
        return model

    def model_class(self, force_create=False):
        existing_model_class = super(ModelDefinition, self).model_class()
        if force_create:
            model_class = self._create_model_class(existing_model_class)
        else:
            model_class = existing_model_class
            if model_class is None:
                model_class = self._create_model_class()
        return _ModelClassProxy(model_class)
    
    @property
    def model_ct(self):
        content_type = getattr(self, '_contenttype_ptr_cache', None)
        if content_type is None:
            content_type = ContentType.objects.get(id=self.contenttype_ptr_id)
            self._contenttype_ptr_cache = content_type
        return self._contenttype_ptr_cache
    
    def clean(self):
        """
        Ensure app_label doesn't override an installed app one
        since model collision could occur and would cause a lot of
        side effects, i. e.:
        
        Defining a new auth.User, while not tested, could override
        the existing one and create a beautiful mess in django's
        internals
        """
        try:
            models.loading.cache.get_app(self.app_label, emptyOK=True)
        except ImproperlyConfigured:
            pass
        else:
            msg = _(u'Cannot cloak an installed app')
            raise ValidationError({'label': [msg]})
    
    def save(self, *args, **kwargs):
        self.model = self.object_name.lower()
        
        save = super(ModelDefinition, self).save(*args, **kwargs)
        
        self._model_class = super(ModelDefinition, self).model_class()
        
        return save
    
    def delete(self, *args, **kwargs):
        model_class = self.model_class()
        
        delete = super(ModelDefinition, self).delete(*args, **kwargs)
        
        ContentType.objects.clear_cache()
        
        _remove_from_model_cache(model_class)
        
        del self._model_class
        
        return delete
        
    def __unicode__(self):
        return u'.'.join((self.app_label, self.object_name))

class ModelDefinitionAttribute(models.Model):
    """
    A mixin used to make sure models that alter the state of a defined model
    clear the cached version
    """
    
    model_def = models.ForeignKey(ModelDefinition, related_name="%(class)ss")
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        save = super(ModelDefinitionAttribute, self).save(*args, **kwargs)
        self.model_def.model_class(force_create=True)
        return save
    
    def delete(self, *args, **kwargs):
        delete = super(ModelDefinitionAttribute, self).delete(*args, **kwargs)
        self.model_def.model_class(force_create=True)
        return delete

class BaseDefinition(OrderableModel, ModelDefinitionAttribute):
    """
    Model used to represent bases of a ModelDefinition
    """
    
    base = PickledObjectField(_(u'base'))
    
    class Meta:
        app_label = 'mutant'
        ordering = ('order',)
        unique_together = (('model_def', 'order'),)
    
    def clean(self):
        # TODO: Validate the whole inheritance field clashes
        base = self.base
        msg = None
        if isclass(base):
            if issubclass(base, models.Model):
                opts = base._meta
                if not opts.abstract:
                    msg = _(u'Model base must be abstract')
                elif issubclass(base, MutableModel):
                    msg = _(u'Base cannot be a subclass of MutableModel')
        else:
            msg = _(u'Base must be a class')
        if msg:
            raise ValidationError({'base': [msg]})
        return super(BaseDefinition, self).clean()

class OrderingFieldDefinition(OrderableModel, ModelDefinitionAttribute):
    
    lookup = models.CharField(max_length=255)
    
    descending = models.BooleanField(_(u'descending'), default=False)
    
    class Meta(OrderableModel.Meta):
        app_label = 'mutant'
        # TODO: Should be unique both it bugs order swapping 
        #unique_together = (('model_def', 'order'),)
    
    def clean(self):
        """
        Make sure the lookup makes sense
        """
        if self.lookup == '?': # Randomly sort
            return
        #TODO: Support order_with_respect_to...
        else:
            lookups = self.lookup.split(LOOKUP_SEP)
            opts = self.model_def.model_class()._meta
            valid = True
            while len(lookups):
                lookup = lookups.pop(0)
                try:
                    field = opts.get_field(lookup)
                except FieldDoesNotExist:
                    valid = False
                else:
                    if isinstance(field, models.ForeignKey):
                        opts = field.rel.to._meta
                    elif len(lookups): # Cannot go any deeper
                        valid = False
                finally:
                    if not valid:
                        msg = _(u"This field doesn't exist")
                        raise ValidationError({'lookup': [msg]})
    
    def get_defined_ordering(self):
        return ("-%s" % self.lookup) if self.descending else self.lookup

class UniqueTogetherDefinition(ModelDefinitionAttribute):
    
    field_defs = models.ManyToManyField('FieldDefinition',
                                        related_name='unique_together_defs')
    
    class Meta:
        app_label = 'mutant'
    
    def __unicode__(self):
        names = ', '.join(self.field_defs.names())
        return _(u"Unique together of (%s)") % names
    
    def clean(self):
        for field_def in self.field_defs.select_related('model_def'):
            if field_def.model_def != self.model_def:
                msg = _(u'All fields must be of the same model')
                raise ValidationError({'field_defs': [msg]})
