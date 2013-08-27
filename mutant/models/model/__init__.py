from __future__ import unicode_literals

from inspect import isclass
from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.signals import class_prepared
from django.utils.translation import ugettext_lazy as _
from orderable.models import OrderableModel
from picklefield.fields import PickledObjectField

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:
    from django.db.models.sql.constants import LOOKUP_SEP

from ... import logger
from ...db.deletion import CASCADE_MARK_ORIGIN
from ...db.fields import LazilyTranslatedField, PythonIdentifierField
from ...db.models import MutableModel
from ...signals import mutable_class_prepared
from ...utils import get_db_table, model_name

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

    def __reduce__(self):
        model_class = self.__get_model_class()
        return (_model_class_from_pk, model_class._definition)

    def __str__(self):
        model_class = self.__get_model_class()
        return str(model_class)


class ModelDefinition(ContentType):
    object_name = PythonIdentifierField(_('object name'))
    db_table = models.CharField(_('database table'), max_length=63,
                                blank=True, null=True)
    managed = models.BooleanField(_('managed'), default=False)
    verbose_name = LazilyTranslatedField(_('verbose name'),
                                         blank=True, null=True)
    verbose_name_plural = LazilyTranslatedField(_('verbose name plural'),
                                                blank=True, null=True)

    objects = ModelDefinitionManager()

    class Meta:
        app_label = 'mutant'
        verbose_name = _('model definition')
        verbose_name_plural = _('model definitions')

    def __unicode__(self):
        return '.'.join((self.app_label, self.object_name))

    def natural_key(self):
        return (self.app_label, self.model)
    natural_key.dependencies = ('contenttypes.contenttype',)

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
            field_instance = field._south_ready_field_instance()
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
            self._model_class = super(ModelDefinition, self).model_class()

    def get_model_bases(self):
        return tuple(bd.get_model_class() for bd in self.basedefinitions.all())

    def get_model_opts(self):
        attrs = {'app_label': self.app_label, 'managed': self.managed}
        # Database table
        db_table = self.db_table
        if db_table is None:
            db_table = get_db_table(*self.natural_key())
        attrs['db_table'] = db_table
        # Verbose names
        if self.verbose_name is not None:
            attrs['verbose_name'] = self.verbose_name
        if self.verbose_name_plural is not None:
            attrs['verbose_name_plural'] = self.verbose_name_plural
        # Unique togethers
        unique_together = tuple(tuple(utd.field_defs.names())
                                    for utd in self.uniquetogetherdefinitions.all())
        if unique_together:
            attrs['unique_together'] = unique_together
        # Ordering
        ordering = tuple(ordf.get_defined_ordering()
                            for ordf in self.orderingfielddefinitions.all())
        if ordering:
            # Make sure not to add ordering if it's empty since it would
            # prevent the model from inheriting it's possible base ordering.
            # Kinda related to django #17429
            attrs['ordering'] = ordering
        return type(str('Meta'), (), attrs)

    def get_model_attrs(self, existing_model_class=None):
        attrs = {
            'Meta': self.get_model_opts(),
            '__module__': str("mutant.apps.%s.models" % self.app_label),
            '_definition': (self.__class__, self.pk),
            '_is_obsolete': False,
            '_dependencies': set(),
        }
        attrs.update(dict((f.name, f.field_instance())
                            for f in self.fielddefinitions.select_subclasses()))
        return attrs

    def _create_model_class(self, existing_model_class=None):
        bases = self.get_model_bases()
        has_mutable_base = False
        for base in bases:
            if issubclass(base, MutableModel):
                has_mutable_base = True
                base._dependencies.add((self.__class__, self.pk))
        if not has_mutable_base:
            bases += (MutableModel,)
        attrs = self.get_model_attrs(existing_model_class)
        if existing_model_class:
            existing_model_class.mark_as_obsolete()
        model_class = type(str(self.object_name), bases, attrs)
        mutable_class_prepared.send(sender=model_class, definition=self,
                                    existing_model_class=existing_model_class)
        logger.debug("Created model class %s.", model_class)
        return model_class

    def model_class(self, force_create=False):
        model_class = super(ModelDefinition, self).model_class()
        if force_create or model_class is None:
            model_class = self._create_model_class(model_class)
        return _ModelClassProxy(model_class)

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
            raise ValidationError(_('Cannot cloak an installed app'))

    def save(self, *args, **kwargs):
        self.model = self.object_name.lower()
        save = super(ModelDefinition, self).save(*args, **kwargs)
        self._model_class = super(ModelDefinition, self).model_class()
        return save

    def delete(self, *args, **kwargs):
        model_class = self.model_class()
        delete = super(ModelDefinition, self).delete(*args, **kwargs)
        model_class.mark_as_obsolete()
        ContentType.objects.clear_cache()
        del self._model_class
        return delete


class ModelDefinitionAttribute(models.Model):
    """
    A mixin used to make sure models that alter the state of a defined model
    clear the cached version
    """
    model_def = models.ForeignKey(ModelDefinition, related_name="%(class)ss",
                                  on_delete=CASCADE_MARK_ORIGIN)

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


class BaseDefinition(OrderableModel, ModelDefinitionAttribute):
    """
    Model used to represent bases of a ModelDefinition
    """
    base = PickledObjectField(_('base'))

    class Meta:
        app_label = 'mutant'
        ordering = ('order',)
        unique_together = (('model_def', 'order'),)

    def get_model_class(self):
        if isinstance(self.base, _ModelClassProxy):
            return self.base.__get__(None, None)
        return self.base

    def get_declared_fields(self):
        fields = []
        if issubclass(self.base, models.Model):
            opts = self.base._meta
            if opts.abstract:
                # Add fields inherited from base's abstract parent and
                # local fields.
                base_fields = chain(
                    opts.get_fields_with_model(),
                    opts.get_m2m_with_model()
                )
                for field, model in base_fields:
                    if model is None or model._meta.abstract:
                        fields.append(field)
            elif not opts.proxy:
                # This is a concrete model base, we must declare a o2o
                attr_name = '%s_ptr' % model_name(opts)
                fields.append(
                    models.OneToOneField(
                        self.base, name=attr_name, null=True,
                        auto_created=True, parent_link=True
                    )
                )
        return tuple(fields)

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


class OrderingFieldDefinition(OrderableModel, ModelDefinitionAttribute):
    lookup = models.CharField(max_length=255)
    descending = models.BooleanField(_('descending'), default=False)

    class Meta(OrderableModel.Meta):
        app_label = 'mutant'
        # TODO: Should be unique both it bugs order swapping
        # unique_together = (('model_def', 'order'),)

    def clean(self):
        """
        Make sure the lookup makes sense
        """
        if self.lookup == '?':  # Randomly sort
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
                    elif len(lookups):  # Cannot go any deeper
                        valid = False
                finally:
                    if not valid:
                        msg = _('This field doesn\'t exist')
                        raise ValidationError({'lookup': [msg]})

    def get_defined_ordering(self):
        return ("-%s" % self.lookup) if self.descending else self.lookup


class UniqueTogetherDefinition(ModelDefinitionAttribute):
    field_defs = models.ManyToManyField(
        'FieldDefinition', related_name='unique_together_defs'
    )

    class Meta:
        app_label = 'mutant'

    def __unicode__(self):
        if self.pk:
            names = ', '.join(self.field_defs.names())
            return _("Unique together of (%s)") % names
        return ''

    def clean(self):
        for field_def in self.field_defs.select_related('model_def'):
            if field_def.model_def != self.model_def:
                msg = _('All fields must be of the same model')
                raise ValidationError({'field_defs': [msg]})
