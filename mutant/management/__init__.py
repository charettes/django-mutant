
from django.contrib.contenttypes.models import ContentType
from django.db import connections, models, router
from django.db.models.fields import FieldDoesNotExist
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from south.db import dbs

from mutant.models import (ModelDefinition, BaseDefinition, FieldDefinition,
    UniqueTogetherDefinition)


def allow_syncdbs(model):
    for db in connections:
        if router.allow_syncdb(db, model):
            yield dbs[db]
        
def perform_ddl(model, action, *args, **kwargs):
    for db in allow_syncdbs(model):
        getattr(db, action)(*args, **kwargs)

def model_definition_post_save(sender, instance, created, raw, **kwargs):
    if raw:
        ct_db = instance._state.db # cts should be one the same db as mds
        ct = ContentType.objects.using(ct_db).get(pk=instance.pk)
        instance.app_label, instance.model = ct.app_label, ct.model
    model_class = instance.model_class(force_create=True)
    opts = model_class._meta
    if created:
        fields = tuple((field.name, field) for field in opts.fields)
        perform_ddl(model_class, 'create_table', opts.db_table, fields)
    else:
        old_opts = instance._model_class._meta
        if old_opts.db_table != opts.db_table:
            perform_ddl(model_class, 'rename_table', old_opts.db_table, opts.db_table)
            # It means that the natural key has changed
            ContentType.objects.clear_cache()

post_save.connect(model_definition_post_save, ModelDefinition,
                  dispatch_uid='mutant.management.model_definition_post_save')

def model_definition_post_delete(sender, instance, **kwargs):
    model_class = instance.model_class()
    table_name = model_class._meta.db_table
    perform_ddl(model_class, 'delete_table', table_name)
    
post_delete.connect(model_definition_post_delete, ModelDefinition,
                    dispatch_uid='mutant.management.model_definition_post_delete')

def base_definition_post_save(sender, instance, created, raw, **kwargs):
    base = instance.base
    if issubclass(base, models.Model):
        model_class = instance.model_def.model_class()
        opts = model_class._meta
        table_name = opts.db_table
        if created:
            for field in base._meta.fields:
                perform_ddl(model_class, 'add_column', table_name,
                            field.name, field, keep_default=False)
        else:
            for field in base._meta.fields:
                try:
                    old_field = opts.get_field(field.name)
                except FieldDoesNotExist:
                    perform_ddl(model_class, 'add_column', table_name,
                                field.name, field, keep_default=False)
                else:
                    column = old_field.get_attname_column()[1]
                    perform_ddl(model_class, 'alter_column', table_name,
                                column, field)
                    
post_save.connect(base_definition_post_save, BaseDefinition,
                  dispatch_uid='mutant.management.base_definition_post_save')

def base_definition_pre_delete(sender, instance, **kwargs):
    """
    This is used to pass data required for deletion to the post_delete
    signal that is no more available thereafter.
    """
    if issubclass(instance.base, models.Model):
        model_class = instance.model_def.model_class()
        instance._state._deletion = (
            allow_syncdbs(model_class),
            model_class._meta.db_table,
        )

pre_delete.connect(base_definition_pre_delete, BaseDefinition,
                   dispatch_uid='mutant.management.base_definition_pre_delete')

def base_definition_post_delete(sender, instance, **kwargs):
    if issubclass(instance.base, models.Model):
        syncdbs, table_name = instance._state._deletion
        for field in instance.base._meta.fields:
            for db in syncdbs:
                db.delete_column(table_name, field.name)
        del instance._state._deletion

post_delete.connect(base_definition_post_delete, BaseDefinition,
                    dispatch_uid='mutant.management.base_definition_post_delete')

def unique_together_field_defs_changed(instance, action, model, **kwargs):
    columns = list(instance.field_defs.names())
    # If there's no columns and action is post_clear there's nothing to do
    if columns and action != 'post_clear':
        model_class = instance.model_def.model_class()
        table_name = model_class._meta.db_table
        if action in ('pre_add', 'pre_remove', 'pre_clear'):
            perform_ddl(model_class, 'delete_unique', table_name, columns)
        # Safe guard against m2m_changed.action API change
        elif action in ('post_add', 'post_remove'):
            perform_ddl(model_class, 'create_unique', table_name, columns)
            
m2m_changed.connect(unique_together_field_defs_changed,
                    UniqueTogetherDefinition.field_defs.through,
                    dispatch_uid='mutant.management.unique_together_field_defs_changed')

def field_definition_post_save(sender, instance, created, raw, **kwargs):
    """
    This signal is connected by all FieldDefinition subclasses
    see comment in FieldDefinitionBase for more details
    """
    model_class = instance.model_def.model_class()
    table_name = model_class._meta.db_table
    field = instance._south_ready_field_instance()
    
    if created:
        if hasattr(instance._state, '_creation_default_value'):
            field.default = instance._state._creation_default_value
            delattr(instance._state, '_creation_default_value')
            keep_default = False
        else:
            keep_default = True
        perform_ddl(model_class, 'add_column', table_name,
                    instance.name, field, keep_default=keep_default)
    else:
        __, column = field.get_attname_column()
        old_field = instance._old_field
        
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

def field_definition_pre_delete(sender, instance, **kwargs):
    model_class = instance.model_def.model_class()
    opts = model_class._meta
    instance._state._deletion = (
        allow_syncdbs(model_class),
        opts.db_table,
        opts.get_field(instance.name).column
    )

pre_delete.connect(field_definition_pre_delete, sender=FieldDefinition,
                   dispatch_uid='mutant.management.field_definition_pre_delete')

def field_definition_post_delete(sender, instance, **kwargs):
    syncdbs, table_name, name = instance._state._deletion
    for db in syncdbs:
        db.delete_column(table_name, name)
    del instance._state._deletion

post_delete.connect(field_definition_post_delete, sender=FieldDefinition,
                    dispatch_uid='mutant.management.field_definition_post_delete')
