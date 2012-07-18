
from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models.field import FieldDefinition, FieldDefinitionManager


class _NumericMeta:
    defined_field_category = _(u'Numeric')


class SmallIntegerFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.SmallIntegerField


class PositiveSmallIntegerFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.PositiveSmallIntegerField


class IntegerFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.IntegerField


class PositiveIntegerFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.PositiveIntegerField


class BigIntegerFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.BigIntegerField


class FloatFieldDefinition(FieldDefinition):

    class Meta(_NumericMeta):
        app_label = 'mutant'
        proxy = True
        defined_field_class = fields.FloatField


max_digits_help_text = _(u'The maximum number of digits allowed in the number. '
                         u'Note that this number must be greater than or equal '
                         u'to ``decimal_places``, if it exists.')

decimal_places_help_text = _(u'The number of decimal places to store '
                             u'with the number.')

class DecimalFieldDefinition(FieldDefinition):

    max_digits = fields.PositiveSmallIntegerField(_(u'max digits'),
                                                  help_text=max_digits_help_text)
    decimal_places = fields.PositiveSmallIntegerField(_(u'decimal_places'),
                                                      help_text=decimal_places_help_text)

    objects = FieldDefinitionManager()

    class Meta(_NumericMeta):
        app_label = 'mutant'
        defined_field_class = fields.DecimalField
        defined_field_options = ('max_digits', 'decimal_places',)
