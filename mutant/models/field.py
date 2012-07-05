import warnings

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.models import signals
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.encoding import force_unicode
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _
from orderable.models import OrderableModel
from picklefield.fields import dbsafe_encode, PickledObjectField

from ..db.fields import (FieldDefinitionTypeField, LazilyTranslatedField,
    PythonIdentifierField)
from ..hacks import (get_concrete_model, get_real_content_type,
    patch_model_option_verbose_name_raw)
from ..managers import FieldDefinitionChoiceManager, InheritedModelManager

from .model import ModelDefinitionAttribute


patch_model_option_verbose_name_raw()

NOT_PROVIDED = dbsafe_encode(models.NOT_PROVIDED)

def _copy_fields(src, to_cls):
    """
    Returns a new instance of `to_cls` with fields data fetched from `src`.
    Useful for getting a model proxy instance from concrete model instance or
    the other way around.
    """
    fields = src._meta.fields
    data = tuple(getattr(src, field.attname) for field in fields)
    return to_cls(*data)

def _popattr(obj, attr, default):
    """
    Useful for retrieving an object attr and removing it if it's part of it's 
    dict while allowing retrieving from subclass.
    i.e.
    class A:
        a = 'a'
    class B(A):
        b = 'b'
    >>> popattr(B, 'a', None)
    'a'
    >>> A.a
    'a'
    """
    val = getattr(obj, attr, default)
    try:
        delattr(obj, attr)
    except AttributeError:
        pass
    return val

def _string_format(string, *args, **kwargs):
    if args:
        return string % tuple(force_unicode(s) for s in args)
    elif kwargs:
        return string % dict((k, force_unicode(v)) for k, v in kwargs.iteritems())
string_format = lazy(_string_format, unicode)

class FieldDefinitionBase(models.base.ModelBase):
    
    FIELD_CLASS_ATTR = 'defined_field_class'
    FIELD_OPTIONS_ATTR = 'defined_field_options'
    FIELD_DESCRIPTION_ATTR = 'defined_field_description'
    FIELD_CATEGORY_ATTR = 'defined_field_category'

    DEFAULT_VERBOSE_NAME = _(u"%s field definition")
    DEFAULT_VERBOSE_NAME_PLURAL = _(u"%s field definitions")

    _base_definition = None
    _field_definitions = {}
    _subclasses_lookups = []
    _proxies = {}
    _lookups = {}
    
    def __new__(cls, name, parents, attrs):
        if 'Meta' in attrs:
            Meta = attrs['Meta']

            field_description = _popattr(Meta, cls.FIELD_DESCRIPTION_ATTR, None)

            field_class = _popattr(Meta, cls.FIELD_CLASS_ATTR, None)
            if field_class:
                if not issubclass(field_class, models.Field):
                    msg = ("Meta's defined_field_class must be a subclass of "
                           "django.db.models.fields.Field")
                    raise ImproperlyConfigured(msg)
                elif field_description is None:
                    field_description = getattr(field_class, 'description', None)

            field_options = _popattr(Meta, cls.FIELD_OPTIONS_ATTR, ())
            if field_options:
                if not isinstance(field_options, tuple):
                    msg = "Meta's defined_field_options must be a tuple"
                    raise ImproperlyConfigured(msg)

            field_category = _popattr(Meta, cls.FIELD_CATEGORY_ATTR, None)

            has_verbose_name = hasattr(Meta, 'verbose_name')
            has_verbose_name_plural = hasattr(Meta, 'verbose_name_plural')
        else:
            field_class = None
            field_options = ()
            field_description = None
            field_category = None
            has_verbose_name = False
            has_verbose_name_plural = False
        
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
                if isinstance(parent, cls):
                    parent_opts = parent._meta
                    if field_description is None:
                        field_description = getattr(parent_opts, cls.FIELD_DESCRIPTION_ATTR, None)
                    if field_class is None:
                        field_class = getattr(parent_opts, cls.FIELD_CLASS_ATTR, None)
                        if field_class and field_description is None:
                            field_description = field_class.description
                    field_options += getattr(parent_opts, cls.FIELD_OPTIONS_ATTR, ())
                    if field_category is None:
                        field_category = getattr(parent_opts, cls.FIELD_CATEGORY_ATTR, None)
                    if parent is not base_definition:
                        if not (parent_opts.abstract or parent_opts.proxy):
                            lookup.insert(0, parent_opts.object_name.lower())
                        parents = list(parent.__bases__) + parents # mimic mro
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
            
            from ..management import (field_definition_post_save,
                FIELD_DEFINITION_POST_SAVE_UID)
            object_name = definition._meta.object_name.lower()
            post_save_dispatch_uid = FIELD_DEFINITION_POST_SAVE_UID % object_name
            signals.post_save.connect(field_definition_post_save, definition,
                                      dispatch_uid=post_save_dispatch_uid)
            
            # Warn the user that they should rely on signals instead of
            # overriding the delete methods since it might not be called
            # when deleting the associated model definition.
            if definition.delete != base_definition.delete:
                concrete_model = get_concrete_model(definition)
                if (opts.proxy and
                    concrete_model.delete != base_definition.delete):
                    # Because of the workaround for django #18083 in
                    # FieldDefinition, overriding the `delete` method on a proxy
                    # of a concrete FieldDefinition that also override the
                    # delete method might call some deletion code twice.
                    # Until #18083 is fixed and the workaround is removed we
                    # raise a `TypeError` to prevent this from happening.
                    msg = ("Proxy model deletion is partially broken until "
                           "django #18083 is fixed. To work around this issue, "
                           "mutant make sure to call the concrete `FieldDefinition`"
                           "you are proxying, in this case `%(concrete_cls)s`. "
                           "However, this can trigger a double execution of "
                           "`%(concrete_cls)s.delete`, thus it is prohibited.")
                    raise TypeError(msg % {'concrete_cls': concrete_model.__name__})
                def_name = definition.__name__
                warnings.warn("Avoid overriding the `delete` method on "
                              "`FieldDefinition` subclass `%s` since it won't "
                              "be called when the associated `ModelDefinition` "
                              "is deleted. If you want to perform actions on "
                              "deletion, add hooks to the `pre_delete` and "
                              "`post_delete` signals." % def_name, UserWarning)
        
        setattr(definition._meta, cls.FIELD_CLASS_ATTR, field_class)
        setattr(definition._meta, cls.FIELD_OPTIONS_ATTR, tuple(set(field_options)))
        setattr(definition._meta, cls.FIELD_DESCRIPTION_ATTR, field_description)
        setattr(definition._meta, cls.FIELD_CATEGORY_ATTR, field_category)
        
        if field_description is not None:
            if not has_verbose_name:
                lazy
                verbose_name = string_format(cls.DEFAULT_VERBOSE_NAME, field_description)
                definition._meta.verbose_name = verbose_name
                if not has_verbose_name_plural:
                    verbose_name_plural = string_format(cls.DEFAULT_VERBOSE_NAME_PLURAL, field_description)
                    definition._meta.verbose_name_plural = verbose_name_plural

        if field_class is not None:
            cls._field_definitions[field_class] = definition
        
        return definition

class FieldDefinitionManager(InheritedModelManager):
    
    class FieldDefinitionQuerySet(InheritedModelManager.InheritanceQuerySet):
        
        def create_with_default(self, default, **kwargs):
            obj = self.model(**kwargs)
            obj._state._creation_default_value = default
            self._for_write = True
            obj.save(force_insert=True, using=self.db)
            return obj
    
    def get_query_set(self):
        return self.FieldDefinitionQuerySet(self.model, using=self._db)
    
    def names(self):
        qs = self.get_query_set()
        return qs.order_by('name').values_list('name', flat=True)
    
    def create_with_default(self, default, **kwargs):
        qs = self.get_query_set()
        return qs.create_with_default(default, **kwargs)
    
class FieldDefinition(ModelDefinitionAttribute):
    
    FIELD_DEFINITION_PK_ATTR = '_mutant_field_definition_pk'

    __metaclass__ = FieldDefinitionBase
    
    # TODO: rename field_def_type
    field_type = FieldDefinitionTypeField()
    
    name = PythonIdentifierField(_(u'name'))
    verbose_name = LazilyTranslatedField(_(u'verbose name'), blank=True, null=True)
    help_text = LazilyTranslatedField(_(u'help text'), blank=True, null=True)
    
    null = models.BooleanField(_(u'null'), default=False)
    blank = models.BooleanField(_(u'blank'), default=False)
    
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
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.field_type = self.get_content_type()
        else:
            self._state._pre_save_field = self.get_bound_field()
            
        return super(FieldDefinition, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self._meta.proxy:
            # TODO: #18083
            # Ok so this is a big issue: proxy model deletion is completely
            # broken. When you delete a inherited model proxy only the proxied
            # model is deleted, plus deletion signals are not sent for the
            # proxied model and it's subclasses. Here we attempt to fix this by
            # getting the concrete model instance of the proxy and deleting it
            # while sending proxy model signals.
            concrete_model = get_concrete_model(self)
            concrete_model_instance = _copy_fields(self, concrete_model)
            
            # Send proxy pre_delete
            signals.pre_delete.send(self.__class__, instance=self)
            
            # Delete the concrete model
            delete = concrete_model_instance.delete(*args, **kwargs)
            
            # This should be sent before the subclasses post_delete but we
            # cannot venture into deletion.Collector to much. Better wait until
            # #18083 is fixed.
            signals.post_delete.send(self.__class__, instance=self)
            
            return delete
        return super(FieldDefinition, self).delete(*args, **kwargs)
    
    @classmethod
    def subclasses(cls):
        # TODO: rename subclasses lookups?
        return FieldDefinitionBase._subclasses_lookups
    
    def type_cast(self):
        field_type_model = self.field_type.model
        
        # Cast to the right concrete model by going up in the 
        # SingleRelatedObjectDescriptor chain
        type_casted = self
        for subclass in FieldDefinitionBase._lookups[field_type_model]:
            type_casted = getattr(type_casted, subclass)
        
        # If it's a proxy model we make to type cast it
        proxy = FieldDefinitionBase._proxies.get(field_type_model, None)
        if proxy:
            concrete_model = get_concrete_model(proxy)
            if not isinstance(type_casted, concrete_model):
                msg = ("Concrete type casted model %s is not an instance of %s "
                       "which is the model proxied by %s" % (type_casted, concrete_model, proxy))
                raise AssertionError(msg)
            type_casted = _copy_fields(type_casted, proxy)
        
        if type_casted._meta.object_name.lower() != field_type_model:
            raise AssertionError("Failed to type cast %s to %s" % (self, field_type_model))
        
        return type_casted
    
    @classmethod
    def get_field_class(cls, **kwargs):
        field_class = getattr(cls._meta, FieldDefinitionBase.FIELD_CLASS_ATTR)
        if not field_class:
            raise NotImplementedError
        return field_class
    
    @classmethod
    def get_field_description(cls):
        return getattr(cls._meta, FieldDefinitionBase.FIELD_DESCRIPTION_ATTR)
    
    @classmethod
    def get_field_category(cls):
        return getattr(cls._meta, FieldDefinitionBase.FIELD_CATEGORY_ATTR)
    
    @classmethod
    def get_content_type(cls):
        return get_real_content_type(cls)

    def get_field_choices(self):
        return tuple(self.choices.as_choices())
    
    def get_field_options(self, **kwargs):
        model_opts = self._meta
        options = {}
        for name in getattr(model_opts, FieldDefinitionBase.FIELD_OPTIONS_ATTR):
            value = getattr(self, name)
            if value != model_opts.get_field(name).get_default():
                options[name] = value
        if kwargs.get('choices', True):
            choices = self.get_field_choices()
            if choices:
                options['choices'] = choices
        return options
    
    def field_instance(self, **kwargs):
        cls = self.get_field_class(**kwargs)
        options = self.get_field_options(**kwargs)
        instance = cls(**options)
        setattr(instance, self.FIELD_DEFINITION_PK_ATTR, self.pk)
        return instance

    def get_bound_field(self):
        opts = self.model_def.model_class()._meta
        for field in opts.fields:
            if getattr(field, self.FIELD_DEFINITION_PK_ATTR, None) == self.pk:
                return field
    
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
        except NotImplementedError:
            pass # `get_field_class` is not implemented
        except Exception as e:
            raise ValidationError(e)
        else:
            # Test the specified default value
            if field.has_default():
                default = field.get_default()
                try:
                    field.clean(default, None)
                except Exception:
                    msg = _(u"%r is not a valid default value") % default
                    raise ValidationError({'default': [msg]})

class FieldDefinitionChoice(OrderableModel):
    """
    A Model to allow specifying choices for a field definition instance
    """
    field_def = models.ForeignKey(FieldDefinition, related_name='choices')
    
    group = LazilyTranslatedField(_(u'group'), blank=True, null=True)
    value = PickledObjectField(_(u'value'))
    label = LazilyTranslatedField(_(u'label'))
    
    objects = FieldDefinitionChoiceManager()
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'field definition choice')
        verbose_name_plural = _(u'field definition choices')
        unique_together = (('field_def', 'order'),
                           ('field_def', 'group', 'value'))
    
    def clean(self):
        try:
            # Make sure to create a field instance with no choices to avoid
            # validating against existing ones.
            field = self.field_def.type_cast().field_instance(choices=False)
            field.clean(self.value, None)
        except ValidationError as e:
            raise ValidationError({'value': e.messages})
    
    def save(self, *args, **kwargs):
        save = super(FieldDefinitionChoice, self).save(*args, **kwargs)
        self.field_def.model_def.model_class(force_create=True)
        return save
