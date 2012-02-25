
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models import FieldDefinition

class BooleanFieldDefinition(FieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'boolean field')
        verbose_name_plural = _(u'boolean fields')
        defined_field_class = fields.BooleanField
        defined_field_category = _(u'boolean')

class NullBooleanFieldDefinition(FieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'null boolean field')
        verbose_name_plural = _(u'null boolean fields')
        defined_field_class = fields.NullBooleanField
        defined_field_category = _(u'boolean')
