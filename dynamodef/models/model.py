import types

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.db.models import signals
from django.db.models.fields import FieldDoesNotExist
from django.db.models.loading import cache as model_cache
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.translation import ugettext_lazy as _
from orderable.models import OrderableModel
from south.db import db as south_api

from dynamodef.db.fields import (LazilyTranslatedField,
    PythonIdentifierField, PythonObjectReferenceField)
from dynamodef.db.models import MutableModel
from dynamodef.managers import InheritedModelManager
from dynamodef.models.definition import CachedObjectDefinition


class ModelDefinition(CachedObjectDefinition):
    
    app_label = PythonIdentifierField(_(u'app label'))
    
    object_name = PythonIdentifierField(_(u'object name'))
    
    model_ct = models.ForeignKey(ContentType, editable=False)
    
    verbose_name = LazilyTranslatedField(_(u'verbose name'),
                                         blank=True, null=True)
    
    verbose_name_plural = LazilyTranslatedField(_(u'verbose name plural'),
                                                blank=True, null=True)
    class Meta:
        app_label = 'dynamodef'
        verbose_name = _(u'model definition')
        verbose_name_plural = _(u'model definitions')
        unique_together = (('app_label', 'object_name',),)
            
    class DefinedModelProxy(object):
        
        def __init__(self, defined_model):
            # Bypass setattr
            self.__dict__['defined_object'] = defined_model
        
        def __defined_model_is_obsolete(self):
            return self.defined_object._MutableModel__is_obsolete
        
        @staticmethod
        def __get_underlying_defined_model(value):
            if isinstance(value, ModelDefinition.DefinedModelProxy):
                return value.defined_object
            elif issubclass(value, MutableModel):
                return value
        
        def __get_defined_model(self):
            if self.__defined_model_is_obsolete():
                return self.__get__(None, None)
            else:
                return self.defined_object
        
        def __get__(self, instance, owner):
            if self.__defined_model_is_obsolete():
                try:
                    definition = self.defined_object.definition()
                except ModelDefinition.DoesNotExist:
                    raise AttributeError('This model definition has been deleted')
                else:
                    # Bypass setattr
                    self.__dict__['defined_object'] = definition.defined_object
            return self.defined_object
        
        def __set__(self, instance, value):
            defined_model = self.__get_underlying_defined_model(value)
            if defined_model is not None:
                self.defined_object = defined_model
            else:
                raise AttributeError('Invalid value')
        
        def __call__(self, *args, **kwargs):
            defined_model = self.__get_defined_model()
            return defined_model(*args, **kwargs)
        
        def __getattr__(self, name):
            defined_model = self.__get_defined_model()
            return getattr(defined_model, name)
        
        def __setattr__(self, name, value):
            defined_model = self.__get_defined_model()
            return setattr(defined_model, name, value)
        
        def __delattr__(self, name):
            defined_model = self.__get_defined_model()
            return delattr(defined_model, name)
        
        def __instancecheck__(self, instance):
            defined_model = self.__get_defined_model()
            return isinstance(instance, defined_model)
        
        def __eq__(self, other):
            other_defined_model = self.__get_underlying_defined_model(other)
            if other_defined_model is not None:
                return self.defined_object == other_defined_model
            else:
                return NotImplemented
            
        def __str__(self):
            defined_model = self.__get_defined_model()
            return str(defined_model)

    def __init__(self, *args, **kwargs):
        super(ModelDefinition, self).__init__(*args, **kwargs)
        if self.pk:
            self.__original_natural_key = (self.app_label, self.object_name.lower())
            self.__original_db_table = self.defined_object._meta.db_table

    def invalidate_definition(self):
        obsolete_model = super(ModelDefinition, self).invalidate_definition()
        if obsolete_model:
            obsolete_model._MutableModel__mark_as_obsolete()
        return obsolete_model
    
    def get_model_bases(self):
        return tuple(bd.get_base_class()
                        for bd in self.basedefinitions.select_subclasses())
    
    def get_model_opts(self):
        attrs = {
            'app_label': self.app_label,
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
    
    def get_model_attrs(self):
        attrs = {
            'Meta': self.get_model_opts(),
            '__module__': "dynamodef.apps.%s.models" % self.app_label,
        }
        
        attrs.update(dict((str(f.name), f.defined_object)
                            for f in self.fielddefinitions.select_subclasses()))
        
        return attrs
    
    def _remove_from_model_cache(self):
        name = self.object_name.lower()
        with model_cache.write_lock:
            app_models = model_cache.app_models.get(self.app_label, False)
            if app_models:
                model = app_models.pop(name, False)
                if model:
                    model_cache._get_models_cache.clear()
                    return model
    
    def _get_object_definition(self):
        bases = self.get_model_bases()
        # Make sure we know it's a defined model
        if not any(issubclass(base, MutableModel) for base in bases):
            bases += (MutableModel,)
            
        attrs = self.get_model_attrs()
        
        self._remove_from_model_cache()
        
        model = type(str(self.object_name), bases, attrs)
        model._MutableModel__definition = (self.__class__, self.pk)
        
        return model
    
    def _prepare_object_definition(self, obj):
        return ModelDefinition.DefinedModelProxy(obj)
    
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
        create = self.pk is None
        natural_key = (self.app_label, self.object_name.lower())
        
        if create:
            model_ct = ContentType.objects.get_for_model(self.defined_object)
            self.model_ct = model_ct
        
        saved = super(ModelDefinition, self).save(*args, **kwargs)
        opts = self.defined_object._meta
        
        if create:
            fields = tuple((field.name, field) for field in opts.fields)
            south_api.create_table(opts.db_table, fields) #@UndefinedVariable
        else:
            if self.__original_db_table != opts.db_table:
                # Rename the table
                south_api.rename_table(self.__original_db_table, opts.db_table) #@UndefinedVariable
            
            if self.__original_natural_key != natural_key:
                # Make sure to rename the ContentType since we want that
                # foreign key pointing to this model to keep their reference.
                model_ct = self.model_ct
                model_ct.app_label, model_ct.object_name = natural_key
                model_ct.save()
                ContentType.objects.clear_cache()
        
        self.__original_natural_key = natural_key
        self.__original_db_table = opts.db_table
        
        return saved
    
    def delete(self, *args, **kwargs):
        db_table = self.defined_object._meta.db_table

        super(ModelDefinition, self).delete(*args, **kwargs)
        
        south_api.delete_table(db_table) #@UndefinedVariable
        
        # Remove ContentType since it's stall
        self.model_ct.delete()
        ContentType.objects.clear_cache()
        
        self._remove_from_model_cache()
        
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
        self.model_def.invalidate_definition()
        return super(ModelDefinitionAttribute, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        self.model_def.invalidate_definition()
        return super(ModelDefinitionAttribute, self).delete(*args, **kwargs)

class BaseDefinition(ModelDefinitionAttribute, OrderableModel):
    
    objects = InheritedModelManager()
    
    class Meta:
        app_label = 'dynamodef'
        ordering = ('order',)
        unique_together = (('model_def', 'order'),)
    
    @classmethod
    def subclasses(cls):
        return ('modelbasedefinition', 'mixindefinition')
    
    def get_base_class(self):
        raise NotImplementedError

class ModelBaseDefinition(BaseDefinition):
    """
    Allows a ModelDefinition to inherit from a specific model
    """
    
    content_type = models.ForeignKey(ContentType)
    
    class Meta:
        app_label = 'dynamodef'
    
    def get_base_class(self):
        return self.content_type.model_class()

class MixinDefinition(BaseDefinition):
    """
    Allows a ModelDefinition to inherit from defined mixins
    and abstract model classes which are not tracked by
    the ContentType framework.
    """
    
    reference = PythonObjectReferenceField(_(u'reference'),
                                           allowed_types=(types.TypeType, models.base.ModelBase))
    
    class Meta:
        app_label = 'dynamodef'
    
    def get_base_class(self):
        return self.reference.obj

class OrderingFieldDefinition(OrderableModel, ModelDefinitionAttribute):
    
    lookup = models.CharField(max_length=255)
    
    descending = models.BooleanField(_(u'descending'), default=False)
    
    class Meta(OrderableModel.Meta):
        app_label = 'dynamodef'
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
            opts = self.model_def.defined_object._meta
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
        app_label = 'dynamodef'
    
    def __unicode__(self):
        names = ', '.join(self.field_defs.names())
        return _(u"Unique together of (%s)") % names
    
    def clean(self):
        for field_def in self.field_defs.select_related('model_def'):
            if field_def.model_def != self.model_def:
                msg = _(u'All fields must be of the same model')
                raise ValidationError({'field_defs': [msg]})
            
def create_unique(instance, action, model, **kwargs):
    names = list(instance.field_defs.names())
    # If there's no names and action is post_clear there's nothing to do
    if names and action != 'post_clear':
        db_table = instance.model_def.defined_object._meta.db_table
        if action in ('pre_add', 'pre_remove', 'pre_clear'):
            south_api.delete_unique(db_table, names) #@UndefinedVariable
        # Safe guard againts m2m_changed.action api change
        elif action in ('post_add', 'post_remove'):
            south_api.create_unique(db_table, names) #@UndefinedVariable
            
signals.m2m_changed.connect(create_unique,
                            UniqueTogetherDefinition.field_defs.through)
