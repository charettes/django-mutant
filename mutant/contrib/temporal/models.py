from __future__ import unicode_literals

from django.db.models import fields
from django.utils.translation import ugettext_lazy as _

from ...models import FieldDefinition, FieldDefinitionManager

auto_now_help_text = _('Automatically set the field to now every time the '
                       'object is saved.')
auto_now_add_help_text = _('Automatically set the field to now when the '
                           'object is first created.')


class DateFieldDefinition(FieldDefinition):
    auto_now = fields.BooleanField(_('auto now'), default=False,
                                   help_text=auto_now_help_text)
    auto_now_add = fields.BooleanField(_('auto now add'), default=False,
                                       help_text=auto_now_add_help_text)

    objects = FieldDefinitionManager()

    class Meta:
        app_label = 'temporal'
        defined_field_class = fields.DateField
        defined_field_options = ('auto_now', 'auto_now_add',)
        defined_field_category = _('Temporal')


class TimeFieldDefinition(DateFieldDefinition):
    class Meta:
        app_label = 'temporal'
        proxy = True
        defined_field_class = fields.TimeField


class DateTimeFieldDefinition(DateFieldDefinition):
    class Meta:
        app_label = 'temporal'
        proxy = True
        defined_field_class = fields.DateTimeField
