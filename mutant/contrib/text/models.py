
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models.field import FieldDefinition

class CharFieldDefinition(FieldDefinition):
    
    max_length = fields.PositiveSmallIntegerField(_(u'max length'),
                                                  blank=True, null=True)
    
    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'char field')
        verbose_name_plural = _(u'char fields')
        defined_field_class = fields.CharField
        defined_field_options = ('max_length',)
        defined_field_category = _(u'text')
        
class TextFieldDefinition(CharFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.TextField
