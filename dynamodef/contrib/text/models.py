
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from dynamodef.models.field import FieldDefinition

class CharFieldDefinition(FieldDefinition):
    
    default = ''
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.CharField
        defined_field_options = ('default',)
        defined_field_category = _(u'text')
        
    @classmethod
    def get_field_description(cls):
        description = super(CharFieldDefinition, cls).get_field_description()
        return description % {'max_length': '255'}
        
class TextFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.TextField
        
    @classmethod
    def get_field_description(cls):
        # Skip CharFieldDefinition.get_field_description
        return super(CharFieldDefinition, cls).get_field_description()
