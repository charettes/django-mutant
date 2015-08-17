from __future__ import unicode_literals

from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models.field import FieldDefinition, FieldDefinitionManager


class _NumericMeta:
    defined_field_category = _('Numeric')


class SmallIntegerFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.SmallIntegerField


class PositiveSmallIntegerFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.PositiveSmallIntegerField


class IntegerFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.IntegerField


class PositiveIntegerFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.PositiveIntegerField


class BigIntegerFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.BigIntegerField


class FloatFieldDefinition(FieldDefinition):
    class Meta(_NumericMeta):
        app_label = 'numeric'
        proxy = True
        defined_field_class = fields.FloatField


max_digits_help_text = _('The maximum number of digits allowed in the number. '
                         'Note that this number must be greater than or equal '
                         'to ``decimal_places``, if it exists.')
decimal_places_help_text = _('The number of decimal places to store '
                             'with the number.')


class DecimalFieldDefinition(FieldDefinition):
    max_digits = fields.PositiveSmallIntegerField(_('max digits'),
                                                  help_text=max_digits_help_text)
    decimal_places = fields.PositiveSmallIntegerField(_('decimal_places'),
                                                      help_text=decimal_places_help_text)

    objects = FieldDefinitionManager()

    class Meta(_NumericMeta):
        app_label = 'numeric'
        defined_field_class = fields.DecimalField
        defined_field_options = ('max_digits', 'decimal_places',)
