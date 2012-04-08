
from django.db.models.signals import post_delete, pre_delete

from ....management import (field_definition_pre_delete,
    FIELD_DEFINITION_PRE_DELETE_UID, field_definition_post_delete,
    FIELD_DEFINITION_POST_DELETE_UID, perform_ddl)

from ..models import ManyToManyFieldDefinition


MANY_TO_MANY_DEFINITION_OBJECT_NAME = ManyToManyFieldDefinition._meta.object_name.lower()

def many_to_many_field_definition_pre_delete(sender, instance, **kwargs):
    field_definition_pre_delete(sender, instance, **kwargs)
    model = instance.model_def.model_class()
    field = model._meta.get_field(str(instance.name))
    intermediary_table_name = field.rel.through._meta.db_table
    instance._state._m2m_deletion = intermediary_table_name

def many_to_many_field_definition_post_delete(sender, instance, **kwargs):
    syncdbs, _, _ = instance._state._deletion
    field_definition_post_delete(sender, instance, **kwargs)
    intermediary_table_name = instance._state._m2m_deletion
    for db in syncdbs:
        db.delete_table(intermediary_table_name)
    del instance._state._m2m_deletion

pre_delete.disconnect(sender=ManyToManyFieldDefinition,
                      dispatch_uid=FIELD_DEFINITION_PRE_DELETE_UID % MANY_TO_MANY_DEFINITION_OBJECT_NAME)
pre_delete.connect(many_to_many_field_definition_pre_delete, ManyToManyFieldDefinition)

post_delete.disconnect(sender=ManyToManyFieldDefinition,
                       dispatch_uid=FIELD_DEFINITION_POST_DELETE_UID % MANY_TO_MANY_DEFINITION_OBJECT_NAME)
post_delete.connect(many_to_many_field_definition_post_delete, ManyToManyFieldDefinition)
