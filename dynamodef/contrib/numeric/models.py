
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from dynamodef.models.field import FieldDefinition

__all__ = ('SmallIntegerFieldDefinition', 'PositiveSmallIntegerFieldDefinition',
           'IntegerFieldDefinition', 'PositiveIntegerFieldDefinition',
           'BigIntegerFieldDefinition', 'FloatFieldDefinition',
           'DecimalFieldDefinition',)

class NumericFieldDefinition(FieldDefinition):
    
    default = 0
    
    class Meta:
        proxy = True
        defined_field_options = ('default',)
        defined_field_category = _(u'numeric')

class SmallIntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.SmallIntegerField
        
    @classmethod
    def get_field_description(cls):
        return _(u'Small integer field')
        
class PositiveSmallIntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.PositiveSmallIntegerField
        
    @classmethod
    def get_field_description(cls):
        return _(u'Positive small integer field')
        
class IntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.IntegerField
        
class PositiveIntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.PositiveIntegerField
        
    @classmethod
    def get_field_description(cls):
        return _(u'Positive integer field')

class BigIntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.BigIntegerField
        
class FloatFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.FloatField

max_digits_help_text = _(u'The maximum number of digits allowed in the number. '
                         u'Note that this number must be greater than or equal '
                         u'to ``decimal_places``, if it exists.')

decimal_places_help_text = _(u'The number of decimal places to store '
                             u'with the number.')

class DecimalFieldDefinition(NumericFieldDefinition):
    
    max_digits = fields.PositiveSmallIntegerField(_(u'max digits'),
                                                  help_text=max_digits_help_text)
    decimal_places = fields.PositiveSmallIntegerField(_(u'decimal_places'),
                                                      help_text=decimal_places_help_text)

    class Meta:
        app_label = 'dynamodef'
        defined_field_class = fields.DecimalField
        defined_field_options = ('max_digits', 'decimal_places',)
        
class CommaSeparatedIntegerFieldDefinition(NumericFieldDefinition):
    
    class Meta:
        app_label = 'dynamodef'
        proxy = True
        defined_field_class = fields.CommaSeparatedIntegerField
