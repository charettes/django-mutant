from __future__ import unicode_literals

from django.db.models import Q, signals
from django.db.models.fields.related import RelatedField
from django.dispatch.dispatcher import receiver
from django.utils.six import string_types

from ....db.models import MutableModel
from ....models import ModelDefinition
from ....signals import mutable_class_prepared
from ....utils import allow_migrate, clear_opts_related_cache
from ..models import ManyToManyFieldDefinition


@receiver(mutable_class_prepared)
def mutable_model_prepared(signal, sender, definition, existing_model_class,
                           **kwargs):
    """
    Make sure all related model class are created and marked as dependency
    when a mutable model class is prepared
    """
    referenced_models = set()
    # Collect all model class the obsolete model class was referring to
    if existing_model_class:
        for field in existing_model_class._meta.local_fields:
            if isinstance(field, RelatedField):
                rel_to = field.rel.to
                if not isinstance(rel_to, string_types):
                    referenced_models.add(rel_to)
    # Add sender as a dependency of all mutable models it refers to
    for field in sender._meta.local_fields:
        if isinstance(field, RelatedField):
            rel_to = field.rel.to
            if not isinstance(rel_to, string_types):
                referenced_models.add(rel_to)
                if (issubclass(rel_to, MutableModel) and
                        rel_to._definition != sender._definition):
                    rel_to._dependencies.add(sender._definition)
    # Mark all model referring to this one as dependencies
    related_model_defs = ModelDefinition.objects.filter(
        Q(fielddefinitions__foreignkeydefinition__to=definition) |
        Q(fielddefinitions__manytomanyfielddefinition__to=definition)
    ).distinct()
    for model_def in related_model_defs:
        if model_def != definition:
            # Generate model class from definition and add it as a dependency
            sender._dependencies.add(model_def.model_class()._definition)
    # Clear the referenced models opts related cache
    for model_class in referenced_models:
        clear_opts_related_cache(model_class)


@receiver(signals.pre_delete, sender=ManyToManyFieldDefinition,
          dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_pre_delete')
def many_to_many_field_definition_pre_delete(sender, instance, **kwargs):
    model_class = instance.model_def.model_class()
    field = model_class._meta.get_field(str(instance.name))
    intermediary_table_name = field.rel.through._meta.db_table
    instance._state._m2m_deletion = (
        allow_migrate(model_class),
        intermediary_table_name
    )


@receiver(signals.post_delete, sender=ManyToManyFieldDefinition,
          dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_post_delete')
def many_to_many_field_definition_post_delete(sender, instance, **kwargs):
    aliases, intermediary_table_name = instance._state._m2m_deletion
    # FIXME: Issue a delete_model
#     for alias in aliases:
#         db = dbs[alias]
#         db.delete_table(intermediary_table_name)
    del instance._state._m2m_deletion
