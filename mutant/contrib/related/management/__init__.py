
from django.db.models.signals import post_delete, pre_delete

from ....management import allow_syncdbs, perform_ddl

from ..models import ManyToManyFieldDefinition


def many_to_many_field_definition_pre_delete(sender, instance, **kwargs):
    model_class = instance.model_def.model_class()
    field = model_class._meta.get_field(str(instance.name))
    intermediary_table_name = field.rel.through._meta.db_table
    instance._state._m2m_deletion = (
        allow_syncdbs(model_class),
        intermediary_table_name
    )

pre_delete.connect(many_to_many_field_definition_pre_delete, ManyToManyFieldDefinition,
                   dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_pre_delete')

def many_to_many_field_definition_post_delete(sender, instance, **kwargs):
    syncdbs, intermediary_table_name = instance._state._m2m_deletion
    for db in syncdbs:
        db.delete_table(intermediary_table_name)
    del instance._state._m2m_deletion

post_delete.connect(many_to_many_field_definition_post_delete, ManyToManyFieldDefinition,
                    dispatch_uid='mutant.contrib.related.management.many_to_many_field_definition_post_delete')
