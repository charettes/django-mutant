from __future__ import unicode_literals

import pickle
from hashlib import md5

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.migrations.state import ModelState
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from picklefield.fields import PickledObjectField

from ... import logger
from ...compat import get_remote_field_model
from ...db.deletion import CASCADE_MARK_ORIGIN
from ...db.fields import LazilyTranslatedField, PythonIdentifierField
from ...db.models import MutableModel
from ...signals import mutable_class_prepared
from ...state import handler as state_handler
from ...utils import get_db_table, get_foward_fields, remove_from_app_cache
from ..ordered import OrderedModel
from .managers import ModelDefinitionManager


def _model_class_from_pk(definition_cls, definition_pk):
    """
    Helper used to unpickle MutableModel model class from their definition
    pk.
    """
    try:
        return definition_cls.objects.get(pk=definition_pk).model_class()
    except definition_cls.DoesNotExist:
        pass


class MutableModelProxy(object):
    __slots__ = ['model', 'refreshing', '__weakref__']

    proxied_methods = [
        '__setattr__', '__delattr__', '__hash__', '__str__'
    ]

    @classmethod
    def method_factory(cls, name):
        def method(self, *args, **kwargs):
            model = self.__get__()
            return getattr(model.__class__, name)(model, *args, **kwargs)
        method.__name__ = str(name)
        return method

    @classmethod
    def factory(cls, base):
        attrs = dict(
            (name, cls.method_factory(name)) for name in cls.proxied_methods
        )
        name = str("%s(%s)" % (cls.__name__, base.__name__))
        return type(name, (cls,), attrs)

    def __new__(cls, model, *args, **kwargs):
        base = model.__class__
        try:
            cache = cls._proxy_class_cache
        except AttributeError:
            cls._proxy_class_cache = cache = {}
        try:
            proxy_class = cache[base]
        except KeyError:
            cache[base] = proxy_class = cls.factory(base)
        return super(MutableModelProxy, cls).__new__(proxy_class)

    def __init__(self, model):
        assert issubclass(model, MutableModel)
        supset = super(MutableModelProxy, self).__setattr__
        supset('model', model)
        supset('refreshing', False)

    def __get__(self, instance=None, owner=None):
        model = self.model
        if not self.refreshing and model.is_obsolete():
            supset = super(MutableModelProxy, self).__setattr__
            try:
                supset('refreshing', True)
                try:
                    definition = model.definition()
                finally:
                    supset('refreshing', False)
            except ModelDefinition.DoesNotExist:
                raise AttributeError(
                    'The definition of %s.%s has been deleted.' % (
                        model._meta.app_label,
                        model._meta.object_name,
                    )
                )
            else:
                proxy = definition.model_class()
                assert isinstance(proxy, MutableModelProxy)
                model = proxy.model
                supset('model', model)
        return model

    def __getattribute__(self, name):
        if name in ('model', 'refreshing', '__get__', '__eq__', '__ne__', '__reduce_ex__'):
            return super(MutableModelProxy, self).__getattribute__(name)
        model = super(MutableModelProxy, self).__getattribute__('__get__')()
        return getattr(model, name)

    def __call__(self, *args, **kwargs):
        model = self.__get__()
        return model(*args, **kwargs)

    def __eq__(self, other):
        model = self.__get__()
        if isinstance(other, MutableModelProxy):
            other = other.__get__()
        if type(model) == type(other):
            return model == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __instancecheck__(self, instance):
        model = self.__get__()
        return isinstance(instance, model)

    def __reduce_ex__(self, protocol):
        model = self.__get__()
        return (_model_class_from_pk, model._definition)


@python_2_unicode_compatible
class ModelDefinition(ContentType):
    object_name = PythonIdentifierField(_('object name'))
    db_table = models.CharField(
        _('database table'), max_length=63, blank=True, null=True
    )
    managed = models.BooleanField(_('managed'), default=False)
    verbose_name = LazilyTranslatedField(
        _('verbose name'), blank=True, null=True
    )
    verbose_name_plural = LazilyTranslatedField(
        _('verbose name plural'), blank=True, null=True
    )

    objects = ModelDefinitionManager()

    class Meta:
        app_label = 'mutant'
        verbose_name = _('model definition')
        verbose_name_plural = _('model definitions')

    def __str__(self):
        return "%s.%s" % (self.app_label, self.object_name)

    def natural_key(self):
        return (self.app_label, self.model)
    natural_key.dependencies = ['contenttypes.contenttype']

    def __init__(self, *args, **kwargs):
        # Attach unsaved related objects
        bases = kwargs.pop('bases', ())
        fields = kwargs.pop('fields', ())
        extra_fields = []
        delayed_save = []
        for base in bases:
            assert base.pk is None, 'Cannot associate already existing BaseDefinition'
            extra_fields.extend(
                [(f.get_attname_column()[1], f) for f in base.get_declared_fields()]
            )
            base._state._add_columns = False
            delayed_save.append(base)
        for field in fields:
            assert field.pk is None, 'Cannot associate already existing FieldDefinition'
            field_instance = field.construct_for_migrate()
            extra_fields.append(
                (field_instance.get_attname_column()[1], field_instance)
            )
            field._state._add_column = False
            delayed_save.append(field)
        super(ModelDefinition, self).__init__(*args, **kwargs)
        # Add those fields to the instance state to be retrieved later
        self._state._create_extra_fields = extra_fields
        self._state._create_delayed_save = delayed_save
        if self.pk:
            self._model_class = self.model_class().model

    def get_model_bases(self):
        """Build a tuple of bases for the constructed definition"""
        bases = []
        has_mutable_base = False
        for base_def in self.basedefinitions.all():
            base = base_def.construct()
            if issubclass(base, MutableModel):
                has_mutable_base = True
                base._dependencies.add((self.__class__, self.pk))
            bases.append(base)
        if not has_mutable_base:
            bases.append(MutableModel)
        return tuple(bases)

    def get_model_opts(self):
        opts = {'app_label': self.app_label, 'managed': self.managed}
        # Database table
        db_table = self.db_table
        if db_table is None:
            db_table = get_db_table(*self.natural_key())
        opts['db_table'] = db_table
        # Verbose names
        if self.verbose_name is not None:
            opts['verbose_name'] = self.verbose_name
        if self.verbose_name_plural is not None:
            opts['verbose_name_plural'] = self.verbose_name_plural
        # Unique together
        unique_together = [
            ut for ut in (
                ut_def.construct() for ut_def in self.uniquetogetherdefinitions.all()
            ) if ut
        ]
        if unique_together:
            opts['unique_together'] = unique_together
        # Ordering
        ordering = tuple(
            ord_field_def.construct()
            for ord_field_def in self.orderingfielddefinitions.all()
        )
        if ordering:
            # Make sure not to add ordering if it's empty since it would
            # prevent the model from inheriting its possible base ordering.
            # Kinda related to django #17429
            opts['ordering'] = ordering
        return opts

    def get_model_attrs(self):
        try:
            app = apps.get_app_config(self.app_label)
        except LookupError:
            __module__ = str("mutant.apps.%s.models" % self.app_label)
        else:
            __module__ = str("%s.models" % app.module.__name__)
        attrs = {
            '__module__': __module__,
            '_definition': (self.__class__, self.pk),
            '_dependencies': set(),
            '_is_obsolete': False,
        }
        return attrs

    def get_state(self):
        fields = [
            (field_def.name, field_def.construct()) for field_def in self.fielddefinitions.select_subclasses()
        ]
        options = self.get_model_opts()
        bases = self.get_model_bases()
        return ModelState(self.app_label, self.object_name, fields=fields, options=options, bases=bases)

    def construct(self, force_create=False, existing_model_class=None):
        state = self.get_state()
        attrs = self.get_model_attrs()

        identifier = (
            self.pk, self.object_name, state.options, dict(
                (name, field.deconstruct()) for name, field in state.fields
            ), [
                MutableModelProxy(base).checksum()
                if base is not MutableModel and issubclass(base, MutableModel) else base
                for base in state.bases
            ]
        )
        checksum = md5(pickle.dumps(identifier)).hexdigest()
        state_handler.set_checksum(self.pk, checksum)

        if existing_model_class:
            if not force_create and existing_model_class._checksum == checksum:
                existing_model_class._is_obsolete = False
                return existing_model_class
            remove_from_app_cache(existing_model_class)
            existing_model_class.mark_as_obsolete()

        try:
            model_class = state.render(apps)
        except RuntimeError:
            # Account for race conditions between the removal from the apps
            # and the rendering of the new state.
            return apps.get_model(state.app_label, state.name)
        model_class._checksum = checksum
        for attr, value in attrs.items():
            setattr(model_class, attr, value)

        mutable_class_prepared.send(
            sender=model_class, definition=self,
            existing_model_class=existing_model_class
        )
        logger.debug("Created model class %s.", model_class)

        return model_class

    def model_class(self, force_create=False):
        model_class = super(ModelDefinition, self).model_class()
        if force_create or model_class is None or model_class.is_obsolete():
            model_class = self.construct(force_create, model_class)
        return MutableModelProxy(model_class)

    @property
    def model_ct(self):
        try:
            content_type = self._contenttype_ptr_cache
        except AttributeError:
            content_type = ContentType.objects.get_for_id(
                self.contenttype_ptr_id
            )
            self._contenttype_ptr_cache = content_type
        return content_type

    def save(self, *args, **kwargs):
        self.model = self.object_name.lower()
        model_class = getattr(self, '_model_class', None)
        if model_class:
            remove_from_app_cache(model_class)
        return super(ModelDefinition, self).save(*args, **kwargs)


class ModelDefinitionAttribute(models.Model):
    """
    A mixin used to make sure models that alter the state of a defined model
    clear the cached version
    """
    model_def = models.ForeignKey(
        ModelDefinition, related_name="%(class)ss",
        on_delete=CASCADE_MARK_ORIGIN
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        force_create = kwargs.pop('force_create_model_class', True)
        save = super(ModelDefinitionAttribute, self).save(*args, **kwargs)
        self.model_def.model_class(force_create=force_create)
        return save

    def delete(self, *args, **kwargs):
        force_create = kwargs.pop('force_create_model_class', True)
        delete = super(ModelDefinitionAttribute, self).delete(*args, **kwargs)
        self.model_def.model_class(force_create=force_create)
        return delete


class OrderedModelDefinitionAttribute(OrderedModel, ModelDefinitionAttribute):
    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        qs = super(OrderedModelDefinitionAttribute, self).get_ordering_queryset()
        return qs.filter(model_def_id=self.model_def_id)


class BaseDefinition(OrderedModelDefinitionAttribute):
    """
    Model used to represent bases of a ModelDefinition
    """
    base = PickledObjectField(_('base'))

    class Meta:
        app_label = 'mutant'
        ordering = ['order']
        unique_together = (('model_def', 'order'),)

    def clean(self):
        try:
            if issubclass(self.base, models.Model):
                if self.base._meta.proxy:
                    raise ValidationError(_("Base can't be a proxy model."))
                elif (issubclass(self.base, MutableModel) and
                      self.base.definition() == self.model_def):
                    raise ValidationError(_("A model definition can't be a base of itself."))
        except TypeError:
            raise ValidationError(_('Base must be a class.'))
        return super(BaseDefinition, self).clean()

    def construct(self):
        if isinstance(self.base, MutableModelProxy):
            return self.base.__get__()
        return self.base

    def get_declared_fields(self):
        fields = []
        if issubclass(self.base, models.Model):
            opts = self.base._meta
            if opts.abstract:
                # Add fields inherited from base's abstract parent and
                # local fields.
                for field in get_foward_fields(opts):
                    if field.model is self.base or field.model._meta.abstract:
                        clone = field.clone()
                        clone.set_attributes_from_name(field.name)
                        fields.append(clone)
            elif not opts.proxy:
                # This is a concrete model base, we must declare a o2o
                attr_name = '%s_ptr' % opts.model_name
                parent_link = models.OneToOneField(
                    self.base, on_delete=models.CASCADE,
                    name=attr_name, auto_created=True, parent_link=True
                )
                parent_link.set_attributes_from_name(attr_name)
                fields.append(parent_link)
        return tuple(fields)


class OrderingFieldDefinition(OrderedModelDefinitionAttribute):
    lookup = models.CharField(max_length=255)
    descending = models.BooleanField(_('descending'), default=False)

    class Meta:
        app_label = 'mutant'
        ordering = ['order']
        # TODO: Should be unique both it bugs order swapping
        # unique_together = (('model_def', 'order'),)

    def clean(self):
        """
        Make sure the lookup makes sense
        """
        if self.lookup == '?':  # Randomly sort
            return
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
                        opts = get_remote_field_model(field)._meta
                    elif len(lookups):  # Cannot go any deeper
                        valid = False
                finally:
                    if not valid:
                        msg = _("This field doesn't exist")
                        raise ValidationError({'lookup': [msg]})

    def construct(self):
        return ("-%s" % self.lookup) if self.descending else self.lookup


@python_2_unicode_compatible
class UniqueTogetherDefinition(ModelDefinitionAttribute):
    field_defs = models.ManyToManyField(
        'FieldDefinition', related_name='unique_together_defs'
    )

    class Meta:
        app_label = 'mutant'

    def __str__(self):
        if self.pk:
            names = ', '.join(self.construct())
            return _("Unique together of (%s)") % names
        return ''

    def clean(self):
        for field_def in self.field_defs.select_related('model_def'):
            if field_def.model_def != self.model_def:
                msg = _('All fields must be of the same model')
                raise ValidationError({'field_defs': [msg]})

    def construct(self):
        return tuple(self.field_defs.names())
