
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from south.db import dbs

from mutant.models import (ModelDefinition, BaseDefinition, FieldDefinition,
    UniqueTogetherDefinition)


def model_definition_post_save(sender, instance, created, raw, **kwargs):
    db = instance._state.db
    if raw:
        ct = ContentType.objects.using(db).get(pk=instance.pk)
        instance.app_label, instance.model = ct.app_label, ct.model
    opts = instance.model_class(force_create=True)._meta
    if created:
        fields = tuple((field.name, field) for field in opts.fields)
        dbs[db].create_table(opts.db_table, fields)
    else:
        old_opts = instance._model_class._meta
        if old_opts.db_table != opts.db_table:
            dbs[db].rename_table(old_opts.db_table, opts.db_table)
            # It means that the natural key has changed
            ContentType.objects.clear_cache()

post_save.connect(model_definition_post_save, ModelDefinition,
                  dispatch_uid='mutant.management.model_definition_post_save')

def model_definition_post_delete(sender, instance, **kwargs):
    model_class = instance.model_class()
    db_table = model_class._meta.db_table
    dbs[instance._state.db].delete_table(db_table)
    
post_delete.connect(model_definition_post_delete, ModelDefinition,
                    dispatch_uid='mutant.management.model_definition_post_delete')

def base_definition_post_save(sender, instance, created, raw, **kwargs):
    base = instance.base
    if issubclass(base, models.Model):
        db = instance._state.db
        model = instance.model_def.model_class()
        opts = model._meta
        table_name = opts.db_table
        if created:
            for field in base._meta.fields:
                dbs[db].add_column(table_name, field.name,
                                         field, keep_default=False)
        else:
            for field in base._meta.fields:
                try:
                    old_field = opts.get_field(field.name)
                except FieldDoesNotExist:
                    dbs[db].add_column(table_name, field.name,
                                             field, keep_default=False)
                else:
                    column = old_field.get_attname_column()[1]
                    dbs[db].alter_column(table_name, column, field)
                    
post_save.connect(base_definition_post_save, BaseDefinition,
                  dispatch_uid='mutant.management.base_definition_post_save')

def base_definition_pre_delete(sender, instance, **kwargs):
    if issubclass(instance.base, models.Model):
        model = instance.model_def.model_class()
        instance._deletion_table_name = model._meta.db_table

pre_delete.connect(base_definition_pre_delete, BaseDefinition,
                   dispatch_uid='mutant.management.base_definition_pre_delete')

def base_definition_post_delete(sender, instance, **kwargs):
    if issubclass(instance.base, models.Model):
        table_name = instance._deletion_table_name
        db = instance._state.db
        for field in instance.base._meta.fields:
            dbs[db].delete_column(table_name, field.name)
        del instance._deletion_table_name

post_delete.connect(base_definition_post_delete, BaseDefinition,
                    dispatch_uid='mutant.management.base_definition_post_delete')

def unique_together_field_defs_changed(instance, action, model, **kwargs):
    names = list(instance.field_defs.names())
    # If there's no names and action is post_clear there's nothing to do
    if names and action != 'post_clear':
        db = instance._state.db
        db_table = instance.model_def.model_class()._meta.db_table
        if action in ('pre_add', 'pre_remove', 'pre_clear'):
            dbs[db].delete_unique(db_table, names)
        # Safe guard againts m2m_changed.action api change
        elif action in ('post_add', 'post_remove'):
            dbs[db].create_unique(db_table, names)
            
m2m_changed.connect(unique_together_field_defs_changed,
                    UniqueTogetherDefinition.field_defs.through,
                    dispatch_uid='mutant.management.unique_together_field_defs_changed')

def field_definition_post_save(sender, instance, created, raw, **kwargs):
    """
    This signal is connected by all FieldDefinition subclasses
    see comment in FieldDefinitionBase for more details
    """
    db = instance._state.db
    field = instance._south_ready_field_instance()
    model = instance.model_def.model_class()
    table_name = model._meta.db_table
    __, column = field.get_attname_column()
    
    if created:
        dbs[db].add_column(table_name, instance.name, field, keep_default=False)
    else:
        old_field = instance._old_field
        
        # Field renaming
        old_column = old_field.get_attname_column()[1]
        if column != old_column:
            dbs[db].rename_column(table_name, old_column, column)
        
        for opt in ('primary_key', 'unique'):
            value = getattr(field, opt)
            if value != getattr(old_field, opt):
                method_format = ('create' if value else 'delete', opt)
                method = getattr(dbs[db], "%s_%s" % method_format)
                method(table_name, (column,))
        
        dbs[db].alter_column(table_name, column, field)

def field_definition_pre_delete(sender, instance, **kwargs):
    """
    This signal is connected by all FieldDefinition subclasses
    see comment in FieldDefinitionBase for more details
    """
    opts = instance.model_def.model_class()._meta
    table_name = opts.db_table
    column_name = opts.get_field(instance.name).column
    instance._deletion_table_name = table_name
    instance._deletion_column_name = column_name

def field_definition_post_delete(sender, instance, **kwargs):
    """
    This signal is connected by all FieldDefinition subclasses
    see comment in FieldDefinitionBase for more details
    """
    db = instance._state.db
    dbs[db].delete_column(instance._deletion_table_name,
                          instance._deletion_column_name)
    del instance._deletion_table_name
    del instance._deletion_column_name
    
def connect_field_definition(definition):
    model = definition._meta.object_name.lower()
    post_save.connect(field_definition_post_save, sender=definition,
                      dispatch_uid="mutant.management.%s_post_save" % model)
    pre_delete.connect(field_definition_pre_delete, sender=definition,
                       dispatch_uid="mutant.management.%s_pre_delete" % model)
    post_delete.connect(field_definition_post_delete, sender=definition,
                        dispatch_uid="mutant.management.%s_post_delete" % model)
    
