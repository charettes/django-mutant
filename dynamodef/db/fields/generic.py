
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db.models import fields

class FieldDefinitionTypeField(fields.related.ForeignKey):
    
    def __init__(self, *args, **kwargs):
        defaults={'to': ContentType}
        defaults.update(kwargs)
        super(FieldDefinitionTypeField, self).__init__(*args, **defaults)
        
    def validate(self, value, model_instance):
        super(FieldDefinitionTypeField, self).validate(value, model_instance)
        if value is None:
            return
        if isinstance(value, int):
            try:
                value = ContentType.objects.get(id=value)
            except ContentType.DoesNotExist:
                msg = self.error_messages['invalid'] % {
                'model': self.rel.to._meta.verbose_name, 'pk': value}
                raise exceptions.ValidationError(msg)
        # Lazily import to avoid circular reference
        from dynamodef.models import FieldDefinition
        klass = value.model_class()
        if not issubclass(klass, FieldDefinition) or klass == FieldDefinition:
            msg = _(u'This field must be the ContentType of '
                    u'an explicit FieldDefinition subclass.')
            raise exceptions.ValidationError(msg)
