
from ....management import field_definition_post_save, perform_ddl


def geometry_field_definition_post_save(sender, instance, created, raw, **kwargs):
    """
    Geometry fields need execution of deferred sql on creation. We make sure to
    clear pending deferred sql in order to avoid executing it now.
    """
    model_class = instance.model_def.model_class()
    
    perform_ddl(model_class, 'clear_deferred_sql')
    
    field_definition_post_save(sender, instance, created, raw, **kwargs)
    
    perform_ddl(model_class, 'execute_deferred_sql')
