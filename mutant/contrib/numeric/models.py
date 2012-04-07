
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models.field import FieldDefinition


class _NumericFieldDefinition(FieldDefinition):
    
    class Meta:
        proxy = True
        defined_field_category = _(u'numeric')

class SmallIntegerFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'small integer field')
        verbose_name_plural = _(u'small integer fields')
        defined_field_class = fields.SmallIntegerField
        
class PositiveSmallIntegerFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'positive small integer field')
        verbose_name_plural = _(u'positive small integer fields')
        defined_field_class = fields.PositiveSmallIntegerField
        
class IntegerFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'integer field')
        verbose_name_plural = _(u'integer fields')
        defined_field_class = fields.IntegerField
        
class PositiveIntegerFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'positive integer field')
        verbose_name_plural = _(u'positive integer fields')
        defined_field_class = fields.PositiveIntegerField

class BigIntegerFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'big integer field')
        verbose_name_plural = _(u'big integer fields')
        defined_field_class = fields.BigIntegerField
        
class FloatFieldDefinition(_NumericFieldDefinition):
    
    class Meta:
        app_label = 'mutant'
        proxy = True
        verbose_name = _(u'float field')
        verbose_name_plural = _(u'float fields')
        defined_field_class = fields.FloatField

max_digits_help_text = _(u'The maximum number of digits allowed in the number. '
                         u'Note that this number must be greater than or equal '
                         u'to ``decimal_places``, if it exists.')

decimal_places_help_text = _(u'The number of decimal places to store '
                             u'with the number.')

class DecimalFieldDefinition(_NumericFieldDefinition):
    
    max_digits = fields.PositiveSmallIntegerField(_(u'max digits'),
                                                  help_text=max_digits_help_text)
    decimal_places = fields.PositiveSmallIntegerField(_(u'decimal_places'),
                                                      help_text=decimal_places_help_text)

    class Meta:
        app_label = 'mutant'
        verbose_name = _(u'decimal field')
        verbose_name_plural = _(u'decimal fields')
        defined_field_class = fields.DecimalField
        defined_field_options = ('max_digits', 'decimal_places',)
