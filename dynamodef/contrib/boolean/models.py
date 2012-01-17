
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from dynamodef.models import FieldDefinition

class BooleanFieldDefinition(FieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.BooleanField
        defined_field_category = _(u'boolean')

class NullBooleanFieldDefinition(FieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.NullBooleanField
        defined_field_category = _(u'boolean')
