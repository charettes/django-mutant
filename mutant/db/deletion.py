from __future__ import unicode_literals

from django.db.models.deletion import CASCADE


def CASCADE_MARK_ORIGIN(collector, field, sub_objs, using):
    """
    Custom on_delete handler which sets  _cascade_deletion_origin on the _state
    of the  all relating objects that will deleted.
    We use this handler on ModelDefinitionAttribute.model_def, so when we delete
    a ModelDefinition we can skip field_definition_post_delete and
    base_definition_post_delete and avoid an incremental columns deletion before
    the entire table is dropped.
    """
    CASCADE(collector, field, sub_objs, using)
    if sub_objs:
        for obj in sub_objs:
            obj._state._cascade_deletion_origin = field.name
