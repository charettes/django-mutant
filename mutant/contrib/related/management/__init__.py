from __future__ import unicode_literals

from django.db.models import Q, signals
from django.db.models.fields.related import RelatedField
from django.dispatch.dispatcher import receiver

from ....db.models import MutableModel
from ....management import allow_syncdbs, perform_ddl
from ....models import ModelDefinition
from ....signals import mutable_class_prepared

from ..models import ManyToManyFieldDefinition


@receiver(mutable_class_prepared)
def mutable_model_prepared(signal, sender, definition, **kwargs):
    """
    Make sure all related model class are created and marked as dependency
    when a mutable model class is prepared
    """
    # Add sender as a dependency of all mutable models it refers to
    for field in sender._meta.local_fields:
        if isinstance(field, RelatedField):
            to = field.rel.to
            if not isinstance(to, basestring) and issubclass(to, MutableModel):
                if to._definition != sender._definition:
                    to._dependencies.add(sender._definition)
    # Mark all model referring to this one as dependencies
    related_model_defs = ModelDefinition.objects.filter(
        Q(fielddefinitions__foreignkeydefinition__to=definition) |
        Q(fielddefinitions__manytomanyfielddefinition__to=definition)
    ).distinct()
    for model_def in related_model_defs:
        if model_def != definition:
            # Generate model class from definition and add it as a dependency
            sender._dependencies.add(model_def.model_class()._definition)


#def many_to_many_field_definition_post_save(sender, instance, created, **kwargs):
#    """
#    This is not connected atm since there's an issue while used as a signal
#    """
#    if created:
#        model_class = instance.model_def.model_class(force_create=True)
#        field = model_class._meta.get_field(str(instance.name))
#        options = field.rel.through._meta
#        intermediary_table_name = options.db_table
#        intermediary_table_fields = tuple((field.name, field)
#                                          for field in options.fields)
#        perform_ddl(model_class, 'create_table',
#                    intermediary_table_name, intermediary_table_fields)
#    else:
#        #TODO: track field and model rename in order to rename the intermediaray
#        # table...
#        pass

#post_save.connect(many_to_many_field_definition_post_save, ManyToManyFieldDefinition,
#                  dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_post_save')


@receiver(signals.pre_delete, sender=ManyToManyFieldDefinition,
          dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_pre_delete')
def many_to_many_field_definition_pre_delete(sender, instance, **kwargs):
    model_class = instance.model_def.model_class()
    field = model_class._meta.get_field(str(instance.name))
    intermediary_table_name = field.rel.through._meta.db_table
    instance._state._m2m_deletion = (
        allow_syncdbs(model_class),
        intermediary_table_name
    )


@receiver(signals.post_delete, sender=ManyToManyFieldDefinition,
          dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_post_delete')
def many_to_many_field_definition_post_delete(sender, instance, **kwargs):
    syncdbs, intermediary_table_name = instance._state._m2m_deletion
    for db in syncdbs:
        db.delete_table(intermediary_table_name)
    del instance._state._m2m_deletion
