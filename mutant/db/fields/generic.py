
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _


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
        from mutant.models import FieldDefinition
        klass = value.model_class()
        if not issubclass(klass, FieldDefinition) or klass == FieldDefinition:
            msg = _(u'This field must be the ContentType of '
                    u'an explicit FieldDefinition subclass.')
            raise exceptions.ValidationError(msg)
        
class ProxyAwareGenericForeignKey(GenericForeignKey):
    """
    Basically a GenericForeignKey that saves the actal ContentType of the object
    even if it's a proxy Model.
    """
    
    def get_content_type(self, obj=None, **kwargs):
        if obj and obj._meta.proxy:
            opts = obj._meta
            natural_key = (opts.app_label, opts.object_name.lower())
            return ContentType.objects.db_manager(obj._state.db).get_by_natural_key(*natural_key)
        else:
            return super(ProxyAwareGenericForeignKey, self).get_content_type(obj, **kwargs)
