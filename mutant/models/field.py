
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from picklefield.fields import dbsafe_encode

from ..db.fields import (FieldDefinitionTypeField, LazilyTranslatedField,
    PickledObjectField, ProxyAwareGenericForeignKey, PythonIdentifierField)
from ..managers import InheritedModelManager
from .choice import ChoiceDefinition
from .model import ModelDefinitionAttribute


NOT_PROVIDED = default=dbsafe_encode(models.NOT_PROVIDED)

class FieldDefinitionBase(models.base.ModelBase):
    
    _base_definition = None
    _subclasses_lookups = []
    _proxies = {}
    _lookups = {}
    
    def __new__(cls, name, parents, attrs):
        if 'Meta' in attrs:
            Meta = attrs['Meta']
            field_class = getattr(Meta, 'defined_field_class', None)
            if field_class:
                if not issubclass(field_class, models.Field):
                    msg = ("Meta's defined_field_class must be a subclass of "
                           "django.db.models.fields.Field")
                    raise ImproperlyConfigured(msg)
                del Meta.defined_field_class
            field_options = getattr(Meta, 'defined_field_options', ())
            if field_options:
                if not isinstance(field_options, tuple):
                    msg = "Meta's defined_field_options must be a tuple"
                    raise ImproperlyConfigured(msg)
                del Meta.defined_field_options
            field_category = getattr(Meta, 'defined_field_category', None)
            if field_category:
                del Meta.defined_field_category
        else:
            field_class = None
            field_options = ()
            field_category = None
        
        definition = super(FieldDefinitionBase, cls).__new__(cls, name, parents, attrs)
        
        # Store the FieldDefinition cls
        if cls._base_definition is None:
            cls._base_definition = definition
        else:
            opts = definition._meta
            model = opts.object_name.lower()
            lookup = []
            base_definition = cls._base_definition
            parents = [definition]
            while parents:
                parent = parents.pop(0)
                if issubclass(parent, base_definition):
                    parent_opts = parent._meta
                    field_class = getattr(parent_opts, 'field_class', field_class)
                    field_category = getattr(parent_opts, 'field_category', field_category)
                    field_options += getattr(parent_opts, 'defined_field_options', ())
                    if parent is not base_definition:
                        if not (parent_opts.abstract or parent_opts.proxy):
                            lookup.insert(0, parent_opts.object_name.lower())
                        parents = list(parent._meta.parents) + parents # mimic mro
            cls._lookups[model] = lookup
            if opts.proxy:
                cls._proxies[model] = definition
            elif not opts.abstract:
                if len(lookup) == 1:
                    # TODO: #16572
                    # We can't do `select_related` on multiple one-to-one
                    # relationships...
                    # see https://code.djangoproject.com/ticket/16572
                    cls._subclasses_lookups.append(LOOKUP_SEP.join(lookup))
            
            # Dynamically connection signals to avoid connecting the signal
            # with no sender and checking if it's a subclass of FieldDefinition
            from mutant.management import connect_field_definition
            connect_field_definition(definition)
        
        definition._meta.defined_field_class = field_class
        definition._meta.defined_field_options = tuple(set(field_options))
        definition._meta.defined_field_category = field_category
        
        return definition

class FieldDefinitionManager(InheritedModelManager):
    
    def names(self):
        qs = self.get_query_set()
        return qs.order_by('name').values_list('name', flat=True)
    
class FieldDefinition(ModelDefinitionAttribute):
    
    __metaclass__ = FieldDefinitionBase
    
    # TODO: rename field_def_type
    field_type = FieldDefinitionTypeField()
    
    name = PythonIdentifierField(_(u'name'))
    verbose_name = LazilyTranslatedField(_(u'verbose name'), blank=True, null=True)
    help_text = LazilyTranslatedField(_(u'help text'), blank=True, null=True)
    
    null = models.BooleanField(_(u'null'), default=False)
    blank = models.BooleanField(_(u'blank'), default=False)
    choices = GenericRelation('FieldDefinitionChoice',
                              content_type_field='field_def_type',
                              object_id_field='field_def_id')
    
    db_column = models.SlugField(_(u'db column'), max_length=30, blank=True, null=True)
    db_index = models.BooleanField(_(u'db index'), default=False)
    
    editable = models.BooleanField(_(u'editable'), default=True)
    default = PickledObjectField(_(u'default'), null=True, default=NOT_PROVIDED)
    
    primary_key = models.BooleanField(_(u'primary key'), default=False)
    unique = models.BooleanField(_(u'unique'), default=False)
    
    unique_for_date = PythonIdentifierField(_(u'unique for date'), blank=True, null=True)
    unique_for_month = PythonIdentifierField(_(u'unique for month'), blank=True, null=True)
    unique_for_year = PythonIdentifierField(_(u'unique for year'), blank=True, null=True)
    
    objects = FieldDefinitionManager()
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'field')
        verbose_name_plural = _(u'fields')
        unique_together = (('model_def', 'name'),)
        defined_field_options = ('name', 'verbose_name', 'help_text',
                                 'null', 'blank', 'db_column', 'db_index',
                                 'editable', 'default', 'primary_key', 'unique',
                                 'unique_for_date', 'unique_for_month', 'unique_for_year')
    
    def __init__(self, *args, **kwargs):
        super(FieldDefinition, self).__init__(*args, **kwargs)
        if self.pk and self.__class__ != FieldDefinition:
            self._old_field = self.field_instance()
    
    def save(self, *args, **kwargs):
        if not self.pk:
            app_label = self._meta.app_label
            model = self._meta.object_name.lower()
            self.field_type = ContentType.objects.get_by_natural_key(app_label, model)
            
        saved = super(FieldDefinition, self).save(*args, **kwargs)
        
        self._old_field = self._south_ready_field_instance()
        
        return saved
    
    @classmethod
    def subclasses(cls):
        # TODO: rename subclasses lookups?
        return FieldDefinitionBase._subclasses_lookups
    
    def type_cast(self):
        field_type_model = self.field_type.model
        
        # Cast to the right concrete model by the going up in the 
        # SingleRelatedObjectDescriptor chain
        type_casted = self
        for subclass in FieldDefinitionBase._lookups[field_type_model]:
            type_casted = getattr(type_casted, subclass)
        
        # If it's a proxy model we make to type cast it
        proxy = FieldDefinitionBase._proxies.get(field_type_model, None)
        if proxy:
            # Prior to django r17573, `proxy_for_model` returned the actual
            # concrete model of a proxy and there was no `concrete_model`
            # property so we try to fetch the `concrete_model` from the opts
            # and fallback to `proxy_for_model` if it's not defined.
            concrete_model = getattr(proxy._meta, 'concrete_model',
                                     proxy._meta.proxy_for_model)
            if not isinstance(type_casted, concrete_model):
                msg = ("Concrete type casted model %s is not an instance of %s "
                       "which is the model proxied by %s" % (type_casted, concrete_model, proxy))
                raise AssertionError(msg)
            data = dict((f.attname, getattr(self, f.attname))
                            for f in self._meta.fields)
            type_casted = proxy(**data)
        
        if type_casted._meta.object_name.lower() != field_type_model:
            raise AssertionError("Failed to type cast %s to %s" % (self, field_type_model))
        
        return type_casted
    
    @classmethod
    def get_field_class(cls):
        field_class = cls._meta.defined_field_class
        if not field_class:
            raise NotImplementedError
        return field_class
    
    @classmethod
    def get_field_description(cls):
        return capfirst(cls._meta.verbose_name)
    
    def get_field_options(self):
        opts = self._meta
        options = {}
        for name in opts.defined_field_options:
            value = getattr(self, name)
            if value != opts.get_field(name).get_default():
                options[name] = value
        choices = tuple(self.choices.as_choices())
        if choices:
            options['choices'] = choices
        return options
    
    def field_instance(self):
        cls = self.get_field_class()
        options = self.get_field_options()
        return cls(**options)
    
    def _south_ready_field_instance(self):
        """
        South api sometimes needs to have modified version of fields to work.
        i. e. You can't pass a ForeignKey(to='self') to add_column
        """
        return self.field_instance()
    
    def clean(self):
        # Make sure we can build the field
        try:
            field = self.field_instance()
        except Exception as e:
            raise ValidationError(e)
        else:
            # Test the specified default value
            try:
                field.clean(field.get_default(), None)
            except Exception:
                msg = _(u"%s is not a valid default value") % self.default
                raise ValidationError({'default':[msg]})

class FieldDefinitionChoice(ChoiceDefinition):
    """
    A Model to allow specifying choices for a field definition instance
    """
    
    field_def_id = models.IntegerField(_(u'field_def def id'), db_index=True)
    field_def = ProxyAwareGenericForeignKey(ct_field='field_def_type',
                                            fk_field='field_def_id')
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'field_def choice')
        verbose_name_plural = _(u'field_def choices')
        unique_together = (('field_def_type', 'field_def_id', 'order'),
                           ('field_def_type', 'field_def_id', 'group', 'value'))
    
    def clean(self):
        try:
            self.field_def.field_instance().clean(self.value, None)
        except ValidationError as e:
            messages = {'value': e.messages}
        else:
            messages = {}
            
        if not isinstance(self.field_def, FieldDefinition):
            msg = _(u'This must be an instance of a `FieldDefinition`')
            messages['field_def'] = [msg]
        
        if messages:
            raise ValidationError(messages)
    
    def save(self, *args, **kwargs):
        save = super(FieldDefinitionChoice, self).save(*args, **kwargs)
        self.field_def.model_def.model_class(force_create=True)
        return save
