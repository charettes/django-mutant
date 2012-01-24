
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from south.db import db as south_api

from dynamodef.db.fields import (FieldDefinitionTypeField, LazilyTranslatedField,
    PythonIdentifierField)
from dynamodef.managers import InheritedModelManager
from dynamodef.models.choice import FieldDefinitionChoice
from dynamodef.models.model import ModelDefinitionAttribute

class FieldDefinitionBase(models.base.ModelBase):
    
    _base_definition = None
    _field_classes = {}
    _subclasses_lookups = []
    _proxies = {}
    
    def __new__(cls, name, bases, attrs):
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
        
        definition = super(FieldDefinitionBase, cls).__new__(cls, name, bases, attrs)
        
        # Store the FieldDefinition cls
        if cls._base_definition is None:
            cls._base_definition = definition
        else:
            meta = definition._meta
            object_name = meta.object_name.lower()
            lookup = [object_name]
            base_definition = cls._base_definition
            bases = list(definition.__bases__)
            while bases:
                base = bases.pop(0)
                if issubclass(base, base_definition):
                    base_meta = base._meta
                    if field_class is None:
                        field_class = base_meta.defined_field_class
                    if field_category is None:
                        field_category = base_meta.defined_field_category
                    field_options += base_meta.defined_field_options
                    if not base == FieldDefinition:
                        if not (base_meta.abstract or base_meta.proxy):
                            lookup.insert(0, base_meta.object_name.lower())
                        bases = list(base.__bases__) + bases # mimic mro
            if meta.proxy:
                cls._proxies[object_name] = (lookup[0:-1], definition)
            elif not meta.abstract:
                cls._subclasses_lookups.append(LOOKUP_SEP.join(lookup))
            if field_class:
                cls._field_classes[field_class] = definition
        
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
    verbose_name = LazilyTranslatedField(_(u'verbose name'),
                                         blank=True, null=True)
    
    null = models.BooleanField(_(u'null'), default=False)
    blank = models.BooleanField(_(u'blank'), default=False)
    max_length = models.PositiveSmallIntegerField(_(u'max length'),
                                                  blank=True, null=True)
    choices = GenericRelation(FieldDefinitionChoice,
                              content_type_field='field_def_type',
                              object_id_field='field_def_id')
    
    db_column = models.SlugField(_(u'db column'), max_length=30,
                                blank=True, null=True)
    db_index = models.BooleanField(_(u'db index'), default=False)
    
    editable = models.BooleanField(_(u'editable'), default=False)
    # TODO: implement default
    #default = models.TextField(blank=True, default=None) #Pickle field : default should be pickled NOT_PROVIDED
    help_text = LazilyTranslatedField(_(u'help text'), blank=True, null=True)
    
    primary_key = models.BooleanField(_(u'primary key'), default=False)
    unique = models.BooleanField(_(u'unique'), default=False)
    unique_for_date = PythonIdentifierField(_(u'unique for date'), blank=True, null=True)
    unique_for_month = PythonIdentifierField(_(u'unique for month'), blank=True, null=True)
    unique_for_year = PythonIdentifierField(_(u'unique for year'), blank=True, null=True)
    
    objects = FieldDefinitionManager()
    
    class Meta:
        app_label = 'dynamodef'
        verbose_name = _(u'field')
        verbose_name_plural = _(u'fields')
        unique_together = (('model_def', 'name'),)
        defined_field_options = ('name', 'verbose_name', 'null', 'blank',
                                 'max_length', 'db_column', 'db_index',
                                 'editable',  'help_text', 'primary_key',
                                 'unique', 'unique_for_date',
                                 'unique_for_month', 'unique_for_year')
    
    def __init__(self, *args, **kwargs):
        super(FieldDefinition, self).__init__(*args, **kwargs)
        if self.pk and self.__class__ != FieldDefinition:
            self.__old_field = self.field_instance()
    
    def save(self, *args, **kwargs):
        created = not self.pk
        
        if created:
            app_label = self._meta.app_label
            model = self._meta.object_name.lower()
            self.field_type = ContentType.objects.get_by_natural_key(app_label, model)
            
        saved = super(FieldDefinition, self).save(*args, **kwargs)
        
        # Make sure to get the field defined object first
        # in order to prevent the model defined object from caching the
        # in-db or queryset cached field state
        field = self._south_ready_field_instance()
        model = self.model_def.model_class()
        table_name = model._meta.db_table
        __, column = field.get_attname_column()
        
        if created:
            south_api.add_column(table_name, self.name, #@UndefinedVariable
                                 field, keep_default=False)
        else:
            old_field = self.__old_field
            
            # Field renaming
            old_column = old_field.get_attname_column()[1]
            if column != old_column:
                south_api.rename_column(table_name, old_column, column) #@UndefinedVariable
            
            for opt in ('primary_key', 'unique'):
                value = getattr(field, opt)
                if value != getattr(old_field, opt):
                    method_format = ('create' if value else 'delete', opt)
                    method = getattr(south_api, "%s_%s" % method_format)
                    method(table_name, (column,))
            
            south_api.alter_column(table_name, column, field) #@UndefinedVariable
        
        self.__old_field = field
        
        return saved
    
    def delete(self, *args, **kwargs):
        model = self.model_def.defined_object
        table_name = model._meta.db_table
        
        super(FieldDefinition, self).delete(*args, **kwargs)
        
        south_api.delete_column(table_name, self.name) #@UndefinedVariable
    
    @classmethod
    def subclasses(cls):
        # TODO: rename subclasses lookups?
        return FieldDefinitionBase._subclasses_lookups
    
    def type_cast(self):
        field_type_model = self.field_type.model
        
        # Tries to reverse a SingleRelatedObjectDescriptor
        type_casted = getattr(self, field_type_model, None)
        
        # Maybe it's just a proxy
        # TODO: Maybe we could cache that somehow, it's kinda a bottleneck
        if type_casted is None:
            proxy = FieldDefinitionBase._proxies.get(field_type_model, None)
            if proxy:
                attr_path, proxy_type = proxy
                proxy_for = self
                for attr in attr_path:
                    proxy_for = getattr(proxy_for, attr)
                assert proxy_for.__class__ == proxy_type._meta.proxy_for_model
                data = dict((f.attname, getattr(self, f.attname))
                                for f in self._meta.fields)
                type_casted = proxy_type(**data)
        
        return type_casted or self
    
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
        options = dict((opt, getattr(self, opt))
                            for opt in self._meta.defined_field_options)
        options['choices'] = tuple(self.choices.as_choices()) or None
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
                field.validate(self.default, None)
            except ValidationError:
                msg = _(u"%s is not a valid default value") % self.default
                raise ValidationError({'default':[msg]})
