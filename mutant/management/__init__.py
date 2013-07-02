from __future__ import unicode_literals

from functools import wraps

import django
from django.contrib.contenttypes.models import ContentType
from django.db import models, router
from django.db.models.fields import FieldDoesNotExist
from django.db.models.signals import (m2m_changed, post_delete, post_save,
    pre_delete)
from django.dispatch.dispatcher import receiver
from south.db import dbs

from .. import logger
from ..models import (ModelDefinition, BaseDefinition, FieldDefinition,
    UniqueTogetherDefinition)
from ..utils import popattr


def allow_syncdbs(model):
    for alias, db in dbs.iteritems():
        if router.allow_syncdb(alias, model):
            yield db


def perform_ddl(model, action, *args, **kwargs):
    if model._meta.managed:
        return

    for db in allow_syncdbs(model):
        if db.deferred_sql:
            for statement in db.deferred_sql:
                logger.warn("Clearing non-executed deferred SQL statement "
                            "since we can't assume it's safe to execute it now. "
                            "Statements was: %s", statement)
            db.clear_deferred_sql()

        if django.VERSION >= (1, 6):
            getattr(db, action)(*args, **kwargs)
            db.execute_deferred_sql()
        else:
            db.start_transaction()
            try:
                getattr(db, action)(*args, **kwargs)
                db.execute_deferred_sql()
            except Exception:
                db.rollback_transaction()
                raise
            else:
                db.commit_transaction()


def nonraw_instance(receiver):
    """
    A signal receiver decorator that fetch the complete instance from db when
    it's passed as raw
    """
    @wraps(receiver)
    def wrapper(sender, instance, raw, using, **kwargs):
        if raw:
            instance = sender._default_manager.using(using).get(pk=instance.pk)
        return receiver(sender=sender, raw=raw, instance=instance, using=using,
                        **kwargs)
    return wrapper


@receiver(post_save, sender=ModelDefinition,
          dispatch_uid='mutant.management.model_definition_post_save')
@nonraw_instance
def model_definition_post_save(sender, instance, created, **kwargs):
    model_class = instance.model_class(force_create=True)
    opts = model_class._meta
    if created:
        primary_key = opts.pk
        fields = [(field.get_attname_column()[1], field) for field in opts.fields
                  if field is not primary_key]
        try:
            extra_fields = getattr(instance._state, '_create_extra_fields')
        except AttributeError:
            pass
        else:
            for column, field in extra_fields:
                if field.primary_key:
                    primary_key = field
                else:
                    fields.append((column, field))
            delattr(instance._state, '_create_extra_fields')
        fields.insert(0, (primary_key.get_attname_column()[1], primary_key))
        try:
            delayed_save = getattr(instance._state, '_create_delayed_save')
        except AttributeError:
            pass
        else:
            for obj in delayed_save:
                obj.model_def = instance
                obj.save(force_insert=True, force_create_model_class=False)
            delattr(instance._state, '_create_delayed_save')
        perform_ddl(model_class, 'create_table', opts.db_table, fields)
        instance.model_class(force_create=True)
    elif instance._model_class:
        old_opts = instance._model_class._meta
        if old_opts.db_table != opts.db_table:
            perform_ddl(model_class, 'rename_table', old_opts.db_table, opts.db_table)
            # It means that the natural key has changed
            ContentType.objects.clear_cache()


@receiver(pre_delete, sender=ModelDefinition,
          dispatch_uid='mutant.management.model_definition_pre_delete')
def model_definition_pre_delete(sender, instance, **kwargs):
    model_class = instance.model_class()
    instance._state._deletion = (
        model_class,
        model_class._meta.db_table
    )


@receiver(post_delete, sender=ModelDefinition,
          dispatch_uid='mutant.management.model_definition_post_delete')
def model_definition_post_delete(sender, instance, **kwargs):
    model_class, table_name = popattr(instance._state, '_deletion')
    perform_ddl(model_class, 'delete_table', table_name)


@receiver(post_save, sender=BaseDefinition,
          dispatch_uid='mutant.management.base_definition_post_save')
def base_definition_post_save(sender, instance, created, raw, **kwargs):
    declared_fields = instance.get_declared_fields()
    if declared_fields:
        model_class = instance.model_def.model_class()
        opts = model_class._meta
        table_name = opts.db_table
        if created:
            try:
                add_columns = getattr(instance._state, '_add_columns')
            except AttributeError:
                add_columns = True
            else:
                delattr(instance._state, '_add_columns')
            finally:
                if add_columns:
                    for field in declared_fields:
                        perform_ddl(model_class, 'add_column', table_name,
                                    field.name, field)
        else:
            for field in declared_fields:
                try:
                    old_field = opts.get_field(field.name)
                except FieldDoesNotExist:
                    perform_ddl(model_class, 'add_column', table_name,
                                field.name, field)
                else:
                    column = old_field.get_attname_column()[1]
                    perform_ddl(model_class, 'alter_column', table_name,
                                column, field)


@receiver(pre_delete, sender=BaseDefinition,
          dispatch_uid='mutant.management.base_definition_pre_delete')
def base_definition_pre_delete(sender, instance, **kwargs):
    """
    This is used to pass data required for deletion to the post_delete
    signal that is no more available thereafter.
    """
    # see CASCADE_MARK_ORIGIN's docstring
    if popattr(instance._state, '_cascade_deletion_origin', None) == 'model_def':
        return
    if (instance.base and issubclass(instance.base, models.Model) and
        instance.base._meta.abstract):
        model_class = instance.model_def.model_class()
        instance._state._deletion = (
            model_class,
            model_class._meta.db_table,
        )


@receiver(post_delete, sender=BaseDefinition,
          dispatch_uid='mutant.management.base_definition_post_delete')
def base_definition_post_delete(sender, instance, **kwargs):
    """
    Make sure to delete fields inherited from an abstract model base.
    """
    if hasattr(instance._state, '_deletion'):
        model, table_name = popattr(instance._state, '_deletion')
        for field in instance.base._meta.fields:
            perform_ddl(model, 'delete_column', table_name, field.name)


@receiver(m2m_changed, sender=UniqueTogetherDefinition.field_defs.through,
          dispatch_uid='mutant.management.unique_together_field_defs_changed')
def unique_together_field_defs_changed(instance, action, model, **kwargs):
    # Here we can't use kwargs['pk_set'] since we need a reference to columns
    # *before* they're actually saved for unique deletion.
    # Note that we use a list and not a tuple for columns since SQLite
    # `delete_unique` chokes if we don't.
    columns = [
        field_def._south_ready_field_instance().get_attname_column()[1]
        for field_def in instance.field_defs.select_subclasses()
    ]
    # If there's no columns and action is post_clear there's nothing to do
    if columns and action != 'post_clear':
        model_class = instance.model_def.model_class()
        table_name = model_class._meta.db_table
        if action in ('pre_add', 'pre_remove', 'pre_clear'):
            perform_ddl(model_class, 'delete_unique', table_name, columns)
        # Safe guard against m2m_changed.action API change
        elif action in ('post_add', 'post_remove'):
            perform_ddl(model_class, 'create_unique', table_name, columns)


@receiver(post_save, sender=FieldDefinition,
          dispatch_uid='mutant.management.raw_field_definition_proxy_post_save')
def raw_field_definition_proxy_post_save(sender, instance, raw, **kwargs):
    """
    When proxy field definitions are loaded from a fixture they're not
    passing through the `field_definition_post_save` signal. Make sure they
    are.
    """
    if raw:
        model_class = instance.content_type.model_class()
        opts = model_class._meta
        if opts.proxy and opts.concrete_model is sender:
            field_definition_post_save(
                sender=model_class, instance=instance.type_cast(), raw=raw,
                **kwargs
            )


@nonraw_instance
def field_definition_post_save(sender, instance, created, raw, **kwargs):
    """
    This signal is connected by all FieldDefinition subclasses
    see comment in FieldDefinitionBase for more details
    """
    # If the field definition is raw we must re-create the model class
    # since ModelDefinitionAttribute.save won't be called
    model_class = instance.model_def.model_class(force_create=raw)
    table_name = model_class._meta.db_table
    field = instance._south_ready_field_instance()
    if created:
        if hasattr(instance._state, '_creation_default_value'):
            field.default = instance._state._creation_default_value
            delattr(instance._state, '_creation_default_value')
        try:
            add_column = getattr(instance._state, '_add_column')
        except AttributeError:
            add_column = True
        else:
            delattr(instance._state, '_add_column')
        finally:
            if add_column:
                perform_ddl(model_class, 'add_column', table_name,
                            instance.name, field)
    else:
        column = field.get_attname_column()[1]
        old_field = instance._state._pre_save_field
        delattr(instance._state, '_pre_save_field')
        # Field renaming
        old_column = old_field.get_attname_column()[1]
        if column != old_column:
            perform_ddl(model_class, 'rename_column', table_name, old_column, column)
        # Create/Drop unique and primary key
        for opt in ('primary_key', 'unique'):
            value = getattr(field, opt)
            if value != getattr(old_field, opt):
                action_prefix = 'create' if value else 'delete'
                action = "%s_%s" % (action_prefix, opt)
                perform_ddl(model_class, action, table_name, (column,))
        perform_ddl(model_class, 'alter_column', table_name, column, field)

FIELD_DEFINITION_POST_SAVE_UID = "mutant.management.%s_post_save"


@receiver(pre_delete, sender=FieldDefinition,
          dispatch_uid='mutant.management.field_definition_pre_delete')
def field_definition_pre_delete(sender, instance, **kwargs):
    # see CASCADE_MARK_ORIGIN's docstring
    if popattr(instance._state, '_cascade_deletion_origin', None) == 'model_def':
        return
    model_class = instance.model_def.model_class()
    opts = model_class._meta
    field = opts.get_field(instance.name)
    instance._state._deletion = (
        model_class,
        opts.db_table,
        field,
    )


@receiver(post_delete, sender=FieldDefinition,
          dispatch_uid='mutant.management.field_definition_post_delete')
def field_definition_post_delete(sender, instance, **kwargs):
    if hasattr(instance._state, '_deletion'):
        model, table_name, field = popattr(instance._state, '_deletion')
        column = field.get_attname_column()[1]
        if field.primary_key:
            primary_key = models.AutoField(name='id', primary_key=True)
            perform_ddl(model, 'alter_column', table_name, column, primary_key)
        else:
            perform_ddl(model, 'delete_column', table_name, column)
