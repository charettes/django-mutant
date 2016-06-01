from __future__ import unicode_literals

import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.models import signals
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from picklefield.fields import PickledObjectField
from polymodels.models import BasePolymorphicModel
from polymodels.utils import copy_fields

from ...db.fields import (
    FieldDefinitionTypeField, LazilyTranslatedField, PythonIdentifierField,
)
from ...utils import lazy_string_format, popattr
from ..model import ModelDefinitionAttribute
from ..ordered import OrderedModel
from .managers import FieldDefinitionChoiceManager, FieldDefinitionManager


def NOT_PROVIDED():
    return models.NOT_PROVIDED


class FieldDefinitionBase(models.base.ModelBase):
    FIELD_CLASS_ATTR = 'defined_field_class'
    FIELD_OPTIONS_ATTR = 'defined_field_options'
    FIELD_DESCRIPTION_ATTR = 'defined_field_description'
    FIELD_CATEGORY_ATTR = 'defined_field_category'

    DEFAULT_VERBOSE_NAME = _("%s field definition")
    DEFAULT_VERBOSE_NAME_PLURAL = _("%s field definitions")

    _base_definition = None
    _field_definitions = {}
    _proxies = {}
    _lookups = {}

    def __new__(cls, name, parents, attrs):
        super_new = super(FieldDefinitionBase, cls).__new__

        if 'Meta' in attrs:
            Meta = attrs['Meta']

            field_description = popattr(Meta, cls.FIELD_DESCRIPTION_ATTR, None)

            field_class = popattr(Meta, cls.FIELD_CLASS_ATTR, None)
            if field_class:
                if not issubclass(field_class, models.Field):
                    msg = ("Meta's defined_field_class must be a subclass of "
                           "django.db.models.fields.Field")
                    raise ImproperlyConfigured(msg)
                elif field_description is None:
                    field_description = getattr(field_class, 'description', None)

            field_options = popattr(Meta, cls.FIELD_OPTIONS_ATTR, ())
            if field_options:
                if not isinstance(field_options, tuple):
                    msg = "Meta's defined_field_options must be a tuple"
                    raise ImproperlyConfigured(msg)

            field_category = popattr(Meta, cls.FIELD_CATEGORY_ATTR, None)

            has_verbose_name = hasattr(Meta, 'verbose_name')
            has_verbose_name_plural = hasattr(Meta, 'verbose_name_plural')
        else:
            field_class = None
            field_options = ()
            field_description = None
            field_category = None
            has_verbose_name = False
            has_verbose_name_plural = False

        definition = super_new(cls, name, parents, attrs)

        # Store the FieldDefinition cls
        if cls._base_definition is None:
            cls._base_definition = definition
        else:
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
                        parents = list(parent.__bases__) + parents  # mimic mro

            from ...management import (
                field_definition_post_save, FIELD_DEFINITION_POST_SAVE_UID
            )
            post_save_dispatch_uid = FIELD_DEFINITION_POST_SAVE_UID % definition._meta.model_name
            signals.post_save.connect(field_definition_post_save, definition,
                                      dispatch_uid=post_save_dispatch_uid)

            # Warn the user that they should rely on signals instead of
            # overriding the delete methods since it might not be called
            # when deleting the associated model definition.
            if definition.delete != base_definition.delete:
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
                verbose_name = lazy_string_format(cls.DEFAULT_VERBOSE_NAME, field_description)
                definition._meta.verbose_name = verbose_name
                if not has_verbose_name_plural:
                    verbose_name_plural = lazy_string_format(cls.DEFAULT_VERBOSE_NAME_PLURAL, field_description)
                    definition._meta.verbose_name_plural = verbose_name_plural

        if field_class is not None:
            cls._field_definitions[field_class] = definition

        return definition


class FieldDefinition(six.with_metaclass(FieldDefinitionBase, BasePolymorphicModel,
                                         ModelDefinitionAttribute)):
    CONTENT_TYPE_FIELD = 'content_type'
    content_type = FieldDefinitionTypeField()

    name = PythonIdentifierField(_('name'))
    verbose_name = LazilyTranslatedField(_('verbose name'), blank=True, null=True)
    help_text = LazilyTranslatedField(_('help text'), blank=True, null=True)

    null = models.BooleanField(_('null'), default=False)
    blank = models.BooleanField(_('blank'), default=False)

    db_column = models.SlugField(_('db column'), max_length=30, blank=True, null=True)
    db_index = models.BooleanField(_('db index'), default=False)

    editable = models.BooleanField(_('editable'), default=True)
    default = PickledObjectField(_('default'), null=True, default=NOT_PROVIDED)

    primary_key = models.BooleanField(_('primary key'), default=False)
    unique = models.BooleanField(_('unique'), default=False)

    unique_for_date = PythonIdentifierField(_('unique for date'), blank=True, null=True)
    unique_for_month = PythonIdentifierField(_('unique for month'), blank=True, null=True)
    unique_for_year = PythonIdentifierField(_('unique for year'), blank=True, null=True)

    objects = FieldDefinitionManager()

    class Meta:
        app_label = 'mutant'
        verbose_name = _('field')
        verbose_name_plural = _('fields')
        unique_together = (('model_def', 'name'),)
        defined_field_options = (
            'name', 'verbose_name', 'help_text',
            'null', 'blank', 'db_column', 'db_index',
            'editable', 'default', 'primary_key', 'unique',
            'unique_for_date', 'unique_for_month', 'unique_for_year'
        )

    def __init__(self, *args, **kwargs):
        super(FieldDefinition, self).__init__(*args, **kwargs)
        if self.pk:
            self._saved_name = self.name

    def natural_key(self):
        return self.model_def.natural_key() + (self.name,)
    natural_key.dependencies = ('mutant.modeldefinition',)

    def save(self, *args, **kwargs):
        if self.pk:
            self._state._pre_save_field = self.get_bound_field()
        saved = super(FieldDefinition, self).save(*args, **kwargs)
        self._saved_name = self.name
        return saved

    def delete(self, *args, **kwargs):
        opts = self._meta
        if opts.proxy:
            # TODO: #18083
            # Ok so this is a big issue: proxy model deletion is completely
            # broken. When you delete a inherited model proxy only the proxied
            # model is deleted, plus deletion signals are not sent for the
            # proxied model and it's subclasses. Here we attempt to fix this by
            # getting the concrete model instance of the proxy and deleting it
            # while sending proxy model signals.
            concrete_model = opts.concrete_model
            concrete_model_instance = copy_fields(self, concrete_model)

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

    def clone(self):
        options = dict(
            (name, getattr(self, name))
            for name in self.get_field_option_names()
        )
        return self.__class__(**options)

    @classmethod
    def get_field_class(cls):
        field_class = getattr(cls._meta, FieldDefinitionBase.FIELD_CLASS_ATTR)
        if not field_class:
            raise NotImplementedError(
                "%s didn't define any `field_class`." % cls.__name__
            )
        return field_class

    @classmethod
    def get_field_option_names(cls):
        return getattr(cls._meta, FieldDefinitionBase.FIELD_OPTIONS_ATTR)

    @classmethod
    def get_field_description(cls):
        return getattr(cls._meta, FieldDefinitionBase.FIELD_DESCRIPTION_ATTR)

    @classmethod
    def get_field_category(cls):
        return getattr(cls._meta, FieldDefinitionBase.FIELD_CATEGORY_ATTR)

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls, for_concrete_model=False)

    def get_field_options(self, **overrides):
        model_opts = self._meta
        options = {}
        for name in self.get_field_option_names():
            if name in overrides:  # Avoid fetching if it's overridden
                continue
            value = getattr(self, name)
            field = model_opts.get_field(name)
            default = field.to_python(field.get_default())
            if value != default:
                options[name] = value
        if 'choices' not in overrides:  # Avoid fetching if it's overridden
            choices = self.choices.construct()
            if choices:
                options['choices'] = choices
        return options

    def construct(self, **overrides):
        cls = self.get_field_class()
        options = self.get_field_options(**overrides)
        options.update(overrides)
        instance = cls(**options)
        instance.set_attributes_from_name(self.name)
        return instance

    def get_bound_field(self):
        opts = self.model_def.model_class()._meta
        for field in opts.fields:
            if field.name == self._saved_name:
                return field

    def construct_for_migrate(self):
        """
        Provide a suitable field to be used in migrations.
        """
        return self.construct()

    def clean(self):
        # Make sure we can build the field
        try:
            field = self.construct()
        except NotImplementedError:
            pass  # `get_field_class` is not implemented
        except Exception as e:
            raise ValidationError(e)
        else:
            # Test the specified default value
            if field.has_default():
                default = field.get_default()
                try:
                    field.clean(default, None)
                except Exception:
                    msg = _("%r is not a valid default value") % default
                    raise ValidationError({'default': [msg]})


class FieldDefinitionChoice(OrderedModel):
    """
    A Model to allow specifying choices for a field definition instance
    """
    field_def = models.ForeignKey(FieldDefinition, on_delete=models.CASCADE, related_name='choices')
    group = LazilyTranslatedField(_('group'), blank=True, null=True)
    value = PickledObjectField(_('value'), editable=True)
    label = LazilyTranslatedField(_('label'))

    objects = FieldDefinitionChoiceManager()

    class Meta:
        app_label = 'mutant'
        verbose_name = _('field definition choice')
        verbose_name_plural = _('field definition choices')
        ordering = ['order']
        unique_together = (
            ('field_def', 'order'),
            ('field_def', 'group', 'value')
        )

    def clean(self):
        try:
            # Make sure to create a field instance with no choices to avoid
            # validating against existing ones.
            field = self.field_def.type_cast().construct(choices=None)
            field.clean(self.value, None)
        except ValidationError as e:
            raise ValidationError({'value': e.messages})

    def save(self, *args, **kwargs):
        save = super(FieldDefinitionChoice, self).save(*args, **kwargs)
        self.field_def.model_def.model_class(force_create=True)
        return save

    def get_ordering_queryset(self):
        qs = super(FieldDefinitionChoice, self).get_ordering_queryset()
        return qs.filter(field_def_id=self.field_def_id)
